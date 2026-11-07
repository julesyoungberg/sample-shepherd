"""Plan a sync: compare the device listing, the samples projects use, and an export
(a rendered folder), and write what to upload and what to delete as a CSV you can read
and edit before anything touches the device.

Rules:
- Upload every export file whose device path isn't on the device yet. Never overwrite.
- Delete only candidates you asked for: files under the synced folders that aren't in the
  export (--prune), and/or the paths in a replace list (--replace).
- Never delete a sample a project uses, matched by path (case-insensitive) or by the
  device's content hash; never delete under a protected path; never delete with no
  project-usage list at all.
"""
from __future__ import annotations

import collections
import os
from dataclasses import dataclass
from pathlib import Path

from sample_shepherd.sync.listing import Listed
from sample_shepherd.sync.projects import UsedSample
from sample_shepherd.util import read_csv, write_csv

HEADER = ["action", "device_path", "local_path", "size", "reason"]
AUDIO = (".wav", ".aif", ".aiff", ".flac")
ACTIONS = ("upload", "delete")


@dataclass
class PlanRow:
    action: str        # upload | delete | skip-exists | keep-used | keep-protected | skip-missing
    device_path: str
    local_path: str = ""
    size: int | None = None
    reason: str = ""

    def as_list(self) -> list:
        return [self.action, self.device_path, self.local_path, "" if self.size is None else self.size, self.reason]


class PlanError(ValueError):
    pass


def norm(path: str) -> str:
    return "/" + path.strip().strip("/").lower()


def join(dest: str, rel: str) -> str:
    return "/" + "/".join(p for p in (dest.strip("/"), rel.strip("/")) if p)


def export_files(render: Path, folders: list[str] | None) -> list[tuple[Path, str]]:
    """[(local file, its path relative to render without extension)] for the chosen folders."""
    render = Path(render)
    if not render.is_dir():
        raise PlanError(f"export folder not found: {render}")
    tops = folders or sorted(p.name for p in render.iterdir() if p.is_dir())
    out = []
    for top in tops:
        d = render / top
        if not d.is_dir():
            raise PlanError(f"folder {top!r} is not in {render}")
        for dp, _, fs in os.walk(d):
            for n in sorted(fs):
                if n.lower().endswith(AUDIO) and not n.startswith("."):
                    p = Path(dp) / n
                    rel = p.relative_to(render).with_suffix("")
                    out.append((p, rel.as_posix()))
    return sorted(out, key=lambda t: t[1])


def make_plan(listing: list[Listed], used: list[UsedSample] | None, render: Path | None = None,
              folders: list[str] | None = None, dest: str = "/", prune: bool = False,
              replace: list[str] | None = None, protected: list[str] = ()) -> list[PlanRow]:
    on_device = {norm(r.path): r for r in listing}
    rows: list[PlanRow] = []
    export_paths: set[str] = set()
    tops: list[str] = []

    if render is not None:
        files = export_files(render, folders)
        tops = sorted({rel.split("/")[0] for _, rel in files}) if not folders else folders
        for local, rel in files:
            dpath = join(dest, rel)
            export_paths.add(norm(dpath))
            size = local.stat().st_size
            if norm(dpath) in on_device:
                rows.append(PlanRow("skip-exists", dpath, str(local), size, "already on the device"))
            else:
                rows.append(PlanRow("upload", dpath, str(local), size))

    candidates: dict[str, str] = {}
    if prune:
        if render is None:
            raise PlanError("--prune needs an export folder to compare with")
        roots = [norm(join(dest, t)) + "/" for t in tops]
        for key, r in on_device.items():
            if any(key.startswith(root) for root in roots) and key not in export_paths:
                candidates.setdefault(r.path, "in a synced folder but not in the export")
    for p in replace or []:
        candidates.setdefault(on_device[norm(p)].path if norm(p) in on_device else p, "in the replace list")

    if candidates:
        if used is None:
            raise PlanError("deleting needs the list of samples projects use (--used, from "
                            "`projects used`); without it nothing can be deleted safely")
        if not used:
            raise PlanError("the project-usage list is empty. That would make every sample look "
                            "deletable, so it's refused. Check the backups it was made from")
        used_paths = {norm(u.path) for u in used}
        used_hashes = {u.hash for u in used if u.hash}
        prot = [norm(p) for p in protected]
        for path, why in sorted(candidates.items()):
            key = norm(path)
            r = on_device.get(key)
            if any(key == pp or key.startswith(pp.rstrip("/") + "/") for pp in prot):
                rows.append(PlanRow("keep-protected", path, "", r.size if r else None, "protected path"))
            elif key in used_paths:
                rows.append(PlanRow("keep-used", path, "", r.size if r else None, "a project uses it"))
            elif r is None:
                rows.append(PlanRow("skip-missing", path, "", None, "not in the device listing"))
            elif r.hash and r.hash in used_hashes:
                rows.append(PlanRow("keep-used", path, "", r.size, "same content hash as a sample a project uses"))
            else:
                rows.append(PlanRow("delete", r.path, "", r.size, why))
    return rows


def summarize(rows: list[PlanRow], transfer) -> str:
    from sample_shepherd.util import estimate_seconds, fmt_bytes, fmt_duration
    counts = collections.Counter(r.action for r in rows)
    up = [r for r in rows if r.action == "upload"]
    dl = [r for r in rows if r.action == "delete"]
    up_bytes = sum(r.size or 0 for r in up)
    dl_bytes = sum(r.size or 0 for r in dl)
    folders = {r.device_path.rsplit("/", 1)[0] for r in up}
    est = estimate_seconds(up_bytes, len(up) + len(folders) * 2 + len(dl), transfer.bytes_per_second,
                           transfer.seconds_per_call)
    lines = [f"upload {len(up)} files ({fmt_bytes(up_bytes)}) into {len(folders)} folders",
             f"delete {len(dl)} files (about {fmt_bytes(dl_bytes)})"]
    for k in ("skip-exists", "keep-used", "keep-protected", "skip-missing"):
        if counts[k]:
            lines.append(f"{k}: {counts[k]}")
    lines.append(f"estimated time: about {fmt_duration(est)} "
                 f"(at {transfer.bytes_per_second / 1000:.0f} KB/s + {transfer.seconds_per_call} s per call)")
    return "\n".join(lines)


def write_plan(rows: list[PlanRow], out: Path) -> None:
    order = {"upload": 0, "delete": 1}
    write_csv(out, HEADER, (r.as_list() for r in sorted(rows, key=lambda r: (order.get(r.action, 2), r.device_path))))


def load_plan(path: Path) -> list[PlanRow]:
    rows = []
    for r in read_csv(path):
        rows.append(PlanRow(r["action"], r["device_path"], r.get("local_path", ""),
                            int(r["size"]) if r.get("size") else None, r.get("reason", "")))
    return rows


def load_replace(path: Path) -> list[str]:
    """Paths from a CSV with a `path` (or `+Drive path`) column; with a `status` column, only
    SAFE rows (the delete_list.py format)."""
    out = []
    for r in read_csv(path):
        p = r.get("path") or r.get("+Drive path")
        if not p:
            raise PlanError(f"{path}: needs a 'path' or '+Drive path' column")
        if "status" in r and r["status"] != "SAFE":
            continue
        out.append(p)
    return out
