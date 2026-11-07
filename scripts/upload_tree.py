#!/usr/bin/env python3
"""Upload chosen top-level folders of a rendered library to the Digitakt II +Drive, resumably.

  python -I scripts/upload_tree.py --render out/full2/preview/digitakt_2_50_3 \
      --folders 00_KITS 01_KICKS ... --dest / --log device/upload-log.csv [--dry-run]

- Mirrors <render>/<folder>/... to <dest><folder>/... on the +Drive (elektroid-cli: mkdir, ul).
- Never deletes or overwrites: a file whose name already exists in its +Drive folder is skipped.
- Resumable: every uploaded file is appended to --log (path,size,seconds), and a rerun skips them.
- --dry-run prints the file count, size and a time estimate, and touches nothing.
"""
import argparse, csv, os, re, subprocess, sys, time
from pathlib import Path

CLI = os.path.expanduser("~/sample-work/vendor/elektroid-install/bin/elektroid-cli")
BPS, PER_FILE = 77_000, 1.6  # measured 2026-11-06: ~77 KB/s plus ~1.6 s per call
LS_LINE = re.compile(r"^([DF])\s+\S+\s+[0-9a-fA-F]{8}\s(.*)$")


def run(*args, tries=3):
    err = ""
    for i in range(tries):
        r = subprocess.run([CLI, *args], capture_output=True)
        if r.returncode == 0:
            return r.stdout.decode("utf-8", errors="replace")
        err = r.stderr.decode(errors="replace")[-300:]
        time.sleep(3 * (i + 1))
    raise RuntimeError(f"{args}: {err}")


def ls_names(dev, path):
    try:
        out = run("elektron:sample:ls", f"{dev}:{path}", tries=1)
    except RuntimeError:
        return None  # folder doesn't exist
    return {m.group(2).rstrip() for line in out.splitlines() if (m := LS_LINE.match(line))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", required=True)
    ap.add_argument("--folders", nargs="+", required=True)
    ap.add_argument("--dest", default="/")
    ap.add_argument("--device", default="1")
    ap.add_argument("--log", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    root = Path(a.render)
    files = sorted(p for f in a.folders for p in (root / f).rglob("*.wav"))
    done = set()
    if os.path.exists(a.log):
        done = {r["path"] for r in csv.DictReader(open(a.log))}
    todo = [p for p in files if str(p.relative_to(root)) not in done]
    size = sum(p.stat().st_size for p in todo)
    est = size / BPS + PER_FILE * len(todo)
    print(f"{len(files)} files in {len(a.folders)} folders; {len(done)} already logged; "
          f"to upload: {len(todo)} files, {size / 1e9:.2f} GB, about {est / 3600:.1f} h")
    if a.dry_run or not todo:
        return

    new_log = not os.path.exists(a.log)
    log = open(a.log, "a", newline="")
    w = csv.writer(log)
    if new_log:
        w.writerow(["path", "size", "seconds"])
    known = {}  # +Drive folder -> names present
    t0, sent, fails = time.time(), 0, 0
    for i, p in enumerate(todo, 1):
        rel = p.relative_to(root)
        ddir = a.dest.rstrip("/") + "/" + str(rel.parent)
        if ddir not in known:
            parts, cur = ddir.strip("/").split("/"), ""
            for part in parts:
                cur += "/" + part
                if cur not in known:
                    names = ls_names(a.device, cur)
                    if names is None:
                        run("elektron:sample:mkdir", f"{a.device}:{cur}")
                        names = set()
                    known[cur] = names
        if p.stem in known[ddir]:
            w.writerow([str(rel), p.stat().st_size, "skipped-exists"]); log.flush()
            continue
        t = time.time()
        try:
            run("elektron:sample:ul", str(p), f"{a.device}:{ddir}")
        except RuntimeError as e:
            fails += 1
            print(f"FAIL {rel}: {e}", flush=True)
            if fails >= 20:
                print("too many failures, stopping", flush=True)
                break
            continue
        known[ddir].add(p.stem)
        sent += p.stat().st_size
        w.writerow([str(rel), p.stat().st_size, round(time.time() - t, 1)]); log.flush()
        if i % 200 == 0 or i == len(todo):
            el = time.time() - t0
            left = (len(todo) - i) * el / i
            print(f"{i}/{len(todo)} files, {sent / 1e6:.0f} MB, {el / 3600:.1f} h elapsed, "
                  f"~{left / 3600:.1f} h left, {fails} failures", flush=True)
    print(f"DONE: {sent / 1e6:.0f} MB uploaded, {fails} failures", flush=True)


if __name__ == "__main__":
    main()
