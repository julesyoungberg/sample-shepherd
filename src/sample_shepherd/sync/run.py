"""Carry out a sync plan on the device: resumable, logged, uploads before deletes.

Every action is appended to a log CSV as it happens. A rerun with the same log skips what's
done, so a stopped sync (unplugged cable, closed laptop) just continues.

Deletes run only after every upload in the plan has succeeded (the replacements are on the
device first), and each delete is checked again, as `plan` checks it: protected paths, paths
a project uses, and content hashes of samples a project uses. A delete row with no hash is
refused, since a hand-added row can't be checked for a renamed copy of a used sample.
"""
from __future__ import annotations

import time
from pathlib import Path

from sample_shepherd.sync.device import Device, DeviceError
from sample_shepherd.sync.plan import Guard, PlanRow, norm
from sample_shepherd.sync.projects import UsedSample
from sample_shepherd.util import AppendLog, fmt_bytes, fmt_duration

LOG_HEADER = ["action", "device_path", "local_path", "size", "seconds", "result"]
DONE = {"ok", "skipped-exists"}
MAX_FAILURES = 20


class SyncStopped(RuntimeError):
    pass


def _done(log: AppendLog) -> set[tuple[str, str]]:
    return {(r["action"], norm(r["device_path"])) for r in log.rows if r.get("result") in DONE}


def run_sync(device: Device, rows: list[PlanRow], log_path: Path, used: list[UsedSample] | None,
             do_delete: bool, out=print, clock=time.monotonic, protected=()) -> dict[str, int]:
    uploads = [r for r in rows if r.action == "upload"]
    deletes = [r for r in rows if r.action == "delete"] if do_delete else []
    if deletes and not used:
        raise SyncStopped("deleting needs a non-empty project-usage list (--used)")
    guard = Guard(used or [], protected)
    stats = {"uploaded": 0, "deleted": 0, "skipped": 0, "refused": 0, "failed": 0, "already_done": 0}

    with AppendLog(log_path, LOG_HEADER) as log:
        done = _done(log)
        todo = [r for r in uploads if ("upload", norm(r.device_path)) not in done]
        stats["already_done"] += len(uploads) - len(todo)
        total = sum(r.size or 0 for r in todo)
        out(f"uploads: {len(todo)} to do ({fmt_bytes(total)}), {len(uploads) - len(todo)} already done")
        known: dict[str, set[str]] = {}
        t0, sent, last = clock(), 0, clock()

        def names_in(folder: str) -> set[str]:
            """Names in a device folder, creating it (and its parents) if it's missing. A
            folder counts as missing only when its parent's listing lacks it: any other ls
            failure is an error, never an empty folder (that would skip the overwrite check)."""
            if folder in known:
                return known[folder]
            if "/" not in known:
                known["/"] = {e.name for e in device.ls("/")}
            parent = "/"
            for part in [p for p in folder.strip("/").split("/") if p]:
                cur = parent.rstrip("/") + "/" + part
                if cur not in known:
                    if part in known[parent]:
                        known[cur] = {e.name for e in device.ls(cur)}
                    else:
                        device.mkdir(cur)
                        known[parent].add(part)
                        known[cur] = set()
                parent = cur
            return known[parent]

        for i, r in enumerate(todo, 1):
            folder, _, name = r.device_path.rpartition("/")
            folder = folder or "/"
            t = clock()
            try:
                present = names_in(folder)
                if name in present:
                    log.write("upload", r.device_path, r.local_path, r.size or "", "", "skipped-exists")
                    stats["skipped"] += 1
                    continue
                if not Path(r.local_path).is_file():
                    raise DeviceError(f"local file missing: {r.local_path}")
                device.upload(Path(r.local_path), folder)
            except DeviceError as e:
                stats["failed"] += 1
                log.write("upload", r.device_path, r.local_path, r.size or "", round(clock() - t, 1), f"FAILED {e}"[:300])
                out(f"FAIL {r.device_path}: {e}")
                if stats["failed"] >= MAX_FAILURES:
                    raise SyncStopped(f"{MAX_FAILURES} failures, stopping. Rerun to resume.") from None
                continue
            present.add(name)
            sent += r.size or 0
            stats["uploaded"] += 1
            log.write("upload", r.device_path, r.local_path, r.size or "", round(clock() - t, 1), "ok")
            now = clock()
            if now - last >= 60 or i == len(todo):
                last = now
                el = now - t0
                rate = sent / el if el > 0 else 0
                left = (len(todo) - i) * el / i
                out(f"{i}/{len(todo)} files, {fmt_bytes(sent)}, {fmt_duration(el)} elapsed, "
                    f"~{fmt_duration(left)} left ({rate / 1000:.0f} KB/s measured), {stats['failed']} failures")

        if not deletes:
            return stats
        failed_uploads = [r for r in uploads if ("upload", norm(r.device_path)) not in _done(log)]
        if failed_uploads:
            out(f"deletes skipped: {len(failed_uploads)} uploads aren't done yet, and the "
                f"replacements must be on the device first. Rerun to retry them.")
            return stats

        todo_d = [r for r in deletes if ("delete", norm(r.device_path)) not in done]
        stats["already_done"] += len(deletes) - len(todo_d)
        out(f"deletes: {len(todo_d)} to do, {len(deletes) - len(todo_d)} already done")
        for r in todo_d:
            no = guard.refusal(r.device_path, r.hash, need_hash=True)
            if no:
                log.write("delete", r.device_path, "", r.size or "", "", f"refused: {no}")
                out(f"refused delete {r.device_path}: {no}")
                stats["refused"] += 1
                continue
            t = clock()
            try:
                device.delete(r.device_path)
            except DeviceError as e:
                stats["failed"] += 1
                log.write("delete", r.device_path, "", r.size or "", round(clock() - t, 1), f"FAILED {e}"[:300])
                out(f"FAIL delete {r.device_path}: {e}")
                if stats["failed"] >= MAX_FAILURES:
                    raise SyncStopped(f"{MAX_FAILURES} failures, stopping. Rerun to resume.") from None
                continue
            stats["deleted"] += 1
            log.write("delete", r.device_path, "", r.size or "", round(clock() - t, 1), "ok")
    return stats
