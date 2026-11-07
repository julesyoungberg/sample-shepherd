#!/usr/bin/env python3
"""Delete +Drive samples that the new library replaces, after the replacements are uploaded.

  python -I scripts/delete_replaced.py --list reports/phase3/delete-now.csv \
      --used device/used-samples.csv --upload-log device/upload-log.csv \
      --log device/delete-log.csv [--dry-run]

A row is deleted only if ALL hold, checked again here:
- its status is SAFE (from delete_list.py: matched to a source file that is in the new library);
- its +Drive path is not in --used (the samples the project backups list);
- its replacement (`new path`) is in --upload-log as uploaded (not failed).
Each deletion is appended to --log; a rerun skips those. --dry-run only counts.
"""
import argparse, csv, os, subprocess, sys, time

CLI = os.path.expanduser("~/sample-work/vendor/elektroid-install/bin/elektroid-cli")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", required=True)
    ap.add_argument("--used", required=True)
    ap.add_argument("--upload-log", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--device", default="1")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    used = {r["path"] for r in csv.DictReader(open(a.used))}
    uploaded = {"/" + r["path"] for r in csv.DictReader(open(a.upload_log)) if r["seconds"] != ""}
    done = {r["path"] for r in csv.DictReader(open(a.log))} if os.path.exists(a.log) else set()
    rows = list(csv.DictReader(open(a.list)))
    go, why = [], {"not SAFE": 0, "used by a project": 0, "replacement not uploaded": 0, "already deleted": 0}
    for r in rows:
        p = r["+Drive path"]
        if r["status"] != "SAFE":
            why["not SAFE"] += 1
        elif p in used:
            why["used by a project"] += 1
        elif r["new path"] not in uploaded:
            why["replacement not uploaded"] += 1
        elif p in done:
            why["already deleted"] += 1
        else:
            go.append(p)
    print(f"{len(rows)} rows: delete {len(go)}; skip " + ", ".join(f"{k} {v}" for k, v in why.items()), flush=True)
    if a.dry_run or not go:
        return
    new_log = not os.path.exists(a.log)
    with open(a.log, "a", newline="") as fh:
        w = csv.writer(fh)
        if new_log:
            w.writerow(["path", "result"])
        fails = 0
        for i, p in enumerate(go, 1):
            r = subprocess.run([CLI, "elektron:sample:rm", f"{a.device}:{p}"], capture_output=True)
            ok = r.returncode == 0
            fails += not ok
            w.writerow([p, "deleted" if ok else "FAILED " + r.stderr.decode(errors="replace")[-120:].strip()])
            fh.flush()
            if i % 200 == 0 or i == len(go):
                print(f"{i}/{len(go)} done, {fails} failures", flush=True)
            if fails >= 20:
                print("too many failures, stopping", flush=True)
                break
    print("DONE", flush=True)


if __name__ == "__main__":
    sys.exit(main())
