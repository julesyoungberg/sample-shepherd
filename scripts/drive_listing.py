#!/usr/bin/env python3
"""List the Digitakt II +Drive (read-only) with elektroid-cli, recursively.

Writes CSV: path,size,hash  (path from the +Drive root, e.g. /factory/BD 01; hash as the device
reports it, 8 hex digits). Only `elektron:sample:ls` is run, which never changes the device.

  python -I scripts/drive_listing.py --device 1 --out device/drive-listing.csv [--dry-run]

--dry-run lists only the top level and prints what would be written.
"""
import argparse, csv, os, re, subprocess, sys, time

CLI = os.path.expanduser("~/sample-work/vendor/elektroid-install/bin/elektroid-cli")
LINE = re.compile(r"^([DF])\s+(\S+)\s+([0-9a-fA-F]{8})\s(.*)$")
UNITS = {"B": 1, "KiB": 1024, "MiB": 1024**2, "GiB": 1024**3}


def parse_size(s):
    m = re.match(r"^([\d.]+)([A-Za-z]+)$", s)
    if not m:
        raise ValueError(f"size {s!r}")
    return round(float(m.group(1)) * UNITS[m.group(2)])


def ls(device, path):
    for attempt in range(3):
        r = subprocess.run([CLI, "elektron:sample:ls", f"{device}:{path}"], capture_output=True)
        if r.returncode == 0:
            break
        time.sleep(2)
    else:
        raise RuntimeError(f"ls {path}: {r.stderr.decode(errors='replace')[-300:]}")
    out = []
    for raw in r.stdout.decode("utf-8", errors="replace").splitlines():
        m = LINE.match(raw)
        if m:
            out.append((m.group(1), parse_size(m.group(2)), m.group(3).lower(), m.group(4).rstrip()))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="1")
    ap.add_argument("--out", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.dry_run:
        top = ls(a.device, "/")
        print(f"top level: {sum(t == 'D' for t, *_ in top)} folders, {sum(t == 'F' for t, *_ in top)} files")
        print(f"would write {a.out}")
        return
    rows, stack, dirs = [], ["/"], 0
    while stack:
        d = stack.pop()
        dirs += 1
        for t, size, h, name in ls(a.device, d):
            p = (d.rstrip("/") + "/" + name)
            if t == "D":
                stack.append(p)
            else:
                rows.append((p, size, h))
        if dirs % 50 == 0:
            print(f"{dirs} folders, {len(rows)} files", file=sys.stderr)
    rows.sort()
    tmp = a.out + ".part"
    with open(tmp, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["path", "size", "hash"])
        w.writerows(rows)
    os.replace(tmp, a.out)
    print(f"{dirs} folders, {len(rows)} files, {sum(r[1] for r in rows) / 1024**3:.2f} GiB -> {a.out}")


if __name__ == "__main__":
    main()
