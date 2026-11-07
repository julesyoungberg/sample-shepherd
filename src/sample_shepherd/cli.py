"""The sample-shepherd command line.

  sample-shepherd organize   doctor | build | patches | install-fourier
  sample-shepherd export     profiles | render | check
  sample-shepherd device     ls | info | listing
  sample-shepherd projects   ls | backup | used
  sample-shepherd plan       listing + used + export -> plan CSV
  sample-shepherd sync       carry out a plan (resumable)
  sample-shepherd config     show

Every command that writes files or touches a device takes --dry-run. Commands that delete
print the plan and need --yes.
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

from sample_shepherd import __version__, config as config_mod
from sample_shepherd.util import DeviceBusy, device_lock, fmt_bytes, fmt_duration, estimate_seconds, write_csv


class UserError(Exception):
    """A problem the user can fix; printed without a traceback."""


def _out(msg: str = "") -> None:
    print(msg, flush=True)


def _err(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


# ----------------------------------------------------------------------------- config

def load_config(a) -> config_mod.Config:
    cfg = config_mod.load(a.config)
    if a.work_dir:
        cfg.work_dir = Path(a.work_dir).expanduser()
    if a.device:
        cfg.device_id = a.device
    if a.elektroid_cli:
        cfg.elektroid_cli = a.elektroid_cli
    return cfg


def cmd_config_show(cfg, a) -> int:
    _out(f"config file:     {cfg.path or '(none; defaults)'}")
    _out(f"work_dir:        {cfg.work_dir}")
    _out(f"device:          backend {cfg.device_backend}, id {cfg.device_id}")
    _out(f"elektroid-cli:   {cfg.elektroid_cli}")
    _out(f"fourier:         {cfg.fourier_command}")
    for k, v in cfg.fourier_env.items():
        _out(f"  env {k}={v}")
    _out(f"profile dirs:    {[str(p) for p in cfg.profile_dirs] or '(bundled only)'}")
    _out(f"protected paths: {cfg.protected}")
    _out(f"transfer:        {cfg.transfer.bytes_per_second:.0f} B/s + {cfg.transfer.seconds_per_call} s per call")
    return 0


# ----------------------------------------------------------------------------- organize

def cmd_organize_doctor(cfg, a) -> int:
    from sample_shepherd.organize import fourier
    exe = fourier.resolve_command(cfg)
    _out(f"fourier command: {exe or 'NOT FOUND (' + cfg.fourier_command + ')'}")
    for k, v in cfg.fourier_env.items():
        _out(f"  {k}={v}")
    patches = fourier.list_patches()
    _out(f"patches: {len(patches)} in {fourier.patches_dir()} (base {fourier.FOURIER_BASE})")
    if exe is None:
        _out("\nInstall the patched Fourier our profiles need:  sample-shepherd organize install-fourier --dir <path>")
        _out("or stock Fourier from PyPI:                     pip install 'sample-shepherd[organize]'")
        return 1
    return fourier.run(cfg, "--version")


def cmd_organize_build(cfg, a) -> int:
    from sample_shepherd.organize import fourier
    args = ["build", *(["--dry-run"] if a.dry_run else []), *a.args]
    # Fourier's own --dry-run reports what a build would do and writes nothing, so run it.
    return fourier.run(cfg, *args)


def cmd_organize_patches(cfg, a) -> int:
    from sample_shepherd.organize import fourier
    _out(f"Patches to Fourier Samples ({fourier.FOURIER_REPO} @ {fourier.FOURIER_BASE}), "
         f"in {fourier.patches_dir()}:")
    for p in fourier.list_patches():
        _out(f"  {p.name[:4]}  {fourier.patch_subject(p)}")
    _out("\nSee docs/fourier-patches.md for what each does and its upstream status.")
    return 0


def cmd_organize_install(cfg, a) -> int:
    import subprocess
    from sample_shepherd.organize import fourier
    target = Path(a.dir).expanduser()
    steps = fourier.install_steps(target, a.python)
    _out(f"Build the patched Fourier into {target} (clone, {len(fourier.list_patches())} patches, uv sync with CLAP):")
    for s in steps:
        _out("  $ " + " ".join(fourier._quote(x) for x in s))
    _out(f"Then set in your config:  [fourier] command = \"{target}/.venv/bin/fourier\"")
    if a.dry_run:
        _out("(dry run: nothing run)")
        return 0
    if target.exists():
        raise UserError(f"{target} already exists; choose an empty path")
    for s in steps:
        r = subprocess.run(s)
        if r.returncode:
            raise UserError(f"step failed ({r.returncode}): {' '.join(s)}")
    return 0


# ----------------------------------------------------------------------------- export

def cmd_export_profiles(cfg, a) -> int:
    from sample_shepherd.export import profiles
    dirs = profiles.search_dirs(cfg)
    for pid, name, path in profiles.list_profiles(dirs):
        _out(f"{pid:22} {name}  ({path})")
    return 0


def cmd_export_render(cfg, a) -> int:
    from sample_shepherd.export import profiles
    from sample_shepherd.organize import fourier
    dirs = profiles.search_dirs(cfg)
    if profiles.find(a.profile, dirs) is None and a.profile not in profiles.BASE_FACTS:
        raise UserError(f"unknown profile {a.profile!r}; see `sample-shepherd export profiles`")
    cfg.fourier_env.setdefault("FOURIER_DEVICES", str(dirs[0]))
    args = ["render", a.profile]
    if a.master:
        args += ["--from", a.master]
    if a.out:
        args += ["--out", a.out]
    return fourier.run(cfg, *args, *a.args, dry_run=a.dry_run)


def cmd_export_check(cfg, a) -> int:
    from sample_shepherd.export import check, profiles
    prof = profiles.resolve(a.profile, profiles.search_dirs(cfg))
    _out(f"profile {prof.id} ({' -> '.join(prof.chain)}): depth {prof.folder_depth}, "
         f"{prof.files_per_folder or 'any number of'} files a folder, {prof.sample_rate} Hz, {prof.bit_depth}-bit")
    stats, issues = check.check_render(Path(a.render), prof)
    _out(f"{stats['files']} files in {stats['folders']} folders, {stats['wav_checked']} WAV headers read")
    for i in issues[: a.show]:
        _out(f"  {i.path}: {i.problem}")
    if len(issues) > a.show:
        _out(f"  ... and {len(issues) - a.show} more")
    _out("OK" if not issues else f"{len(issues)} issues")
    return 0 if not issues else 1


# ----------------------------------------------------------------------------- device

def _device(cfg):
    from sample_shepherd.sync.device import get_backend
    return get_backend(cfg)


def cmd_device_ls(cfg, a) -> int:
    with device_lock(cfg.lock_file):
        devs = _device(cfg).list_devices()
    for d in devs:
        _out(f"{d.number}: {d.name} ({d.id})")
    if not devs:
        _out("no devices found")
    return 0


def cmd_device_info(cfg, a) -> int:
    with device_lock(cfg.lock_file):
        info = _device(cfg).info()
    for k, v in info.items():
        _out(f"{k}: {', '.join(v) if isinstance(v, list) else v}")
    if "sample" not in info.get("filesystems", []):
        _out("note: this device has no sample filesystem, so sample sync isn't supported")
    return 0


def cmd_device_listing(cfg, a) -> int:
    from sample_shepherd.sync import listing
    dev = _device(cfg)
    with device_lock(cfg.lock_file):
        if a.dry_run:
            top = dev.ls(a.root)
            _out(f"{a.root}: {sum(e.kind == 'D' for e in top)} folders, {sum(e.kind == 'F' for e in top)} files "
                 f"at the top level")
            _out(f"(dry run: would list everything below it and write {a.out})")
            return 0
        rows = listing.collect(dev, a.root, progress=lambda n: _err(f"{n} folders read"))
    listing.write(rows, Path(a.out))
    total = sum(r.size or 0 for r in rows)
    _out(f"{len(rows)} files, {total / 1024**3:.2f} GiB -> {a.out}")
    return 0


# ----------------------------------------------------------------------------- projects

def cmd_projects_ls(cfg, a) -> int:
    with device_lock(cfg.lock_file):
        slots = _device(cfg).list_projects()
    for s in slots:
        size = fmt_bytes(s.size) if s.size is not None else "?"
        _out(f"{s.slot:>5}  {s.name:32} {size}{'' if s.valid else '  (no data)'}")
    return 0


def cmd_projects_backup(cfg, a) -> int:
    from sample_shepherd.sync import projects
    dev = _device(cfg)
    out = Path(a.out) if a.out else cfg.work_dir / "backups" / dt.date.today().isoformat()
    with device_lock(cfg.lock_file):
        slots = [s for s in dev.list_projects() if s.valid or s.size]
        if a.slots:
            slots = [s for s in slots if s.slot in set(a.slots)]
        todo = [s for s in slots if not (out / projects.slot_folder(s.slot)).is_dir()]
        size = sum(s.size or 0 for s in todo)
        est = estimate_seconds(size, len(todo), cfg.transfer.bytes_per_second, cfg.transfer.seconds_per_call)
        _out(f"{len(slots)} projects; {len(slots) - len(todo)} already backed up in {out}; "
             f"to back up: {len(todo)} ({fmt_bytes(size)}, about {fmt_duration(est)})")
        for s in todo:
            _out(f"  slot {s.slot}: {s.name} -> {out / projects.slot_folder(s.slot)}/")
        if a.dry_run or not todo:
            return 0
        index = []
        try:
            for s in todo:
                # download into <slot>.part and rename when complete, so a stopped backup never
                # leaves a half-written project that a rerun would count as done
                final = out / projects.slot_folder(s.slot)
                part = final.with_name(final.name + ".part")
                if part.exists():
                    import shutil
                    shutil.rmtree(part)
                tmp = dev.download_project(s.slot, part)
                part.rename(final)
                f = final / tmp.name
                index.append([s.slot, s.name, str(f.relative_to(out)), f.stat().st_size, projects.sha256(f)])
                _out(f"  slot {s.slot}: {f.name} ({fmt_bytes(f.stat().st_size)})")
        finally:
            if index:
                idx = out / "backup-index.csv"
                old = []
                if idx.exists():
                    from sample_shepherd.util import read_csv
                    old = [[r["slot"], r["name"], r["file"], r["size"], r["sha256"]] for r in read_csv(idx)]
                write_csv(idx, ["slot", "name", "file", "size", "sha256"], old + index)
    _out(f"backed up {len(index)} projects; index: {out / 'backup-index.csv'}")
    _out("Copy this folder somewhere off this disk too. Never test a backup by restoring it to the device.")
    return 0


def cmd_projects_used(cfg, a) -> int:
    from sample_shepherd.sync import projects
    try:
        used, files = projects.used_samples(Path(a.backups))
    except ValueError as e:
        raise UserError(str(e)) from None
    if not files:
        raise UserError(f"no project backups found under {a.backups}")
    _out(f"{len(files)} projects use {len(used)} distinct samples")
    if a.dry_run:
        _out(f"(dry run: would write {a.out})")
        return 0
    write_csv(Path(a.out), projects.USED_HEADER, projects.used_rows(used))
    _out(f"-> {a.out}")
    return 0


# ----------------------------------------------------------------------------- plan / sync

def cmd_plan(cfg, a) -> int:
    from sample_shepherd.sync import listing, plan, projects
    used = projects.load_used(Path(a.used)) if a.used else None
    replace = plan.load_replace(Path(a.replace)) if a.replace else None
    try:
        rows = plan.make_plan(listing.load(Path(a.listing)), used, Path(a.export) if a.export else None,
                              a.folders, a.dest, a.prune, replace, cfg.protected)
    except plan.PlanError as e:
        raise UserError(str(e)) from None
    _out(plan.summarize(rows, cfg.transfer))
    if a.dry_run:
        _out(f"(dry run: would write {a.out})")
        return 0
    plan.write_plan(rows, Path(a.out))
    _out(f"plan -> {a.out}  (read it, edit it if you like, then `sample-shepherd sync --plan {a.out}`)")
    return 0


def cmd_sync(cfg, a) -> int:
    from sample_shepherd.sync import plan, projects, run
    rows = plan.load_plan(Path(a.plan))
    used = projects.load_used(Path(a.used)) if a.used else None
    do_delete = not a.no_delete
    deletes = [r for r in rows if r.action == "delete"]
    _out(plan.summarize(rows if do_delete else [r for r in rows if r.action != "delete"], cfg.transfer))
    if a.dry_run:
        _out("(dry run: nothing sent to the device)")
        return 0
    if deletes and do_delete:
        if not a.yes:
            for r in deletes[:20]:
                _out(f"  delete {r.device_path}  ({r.reason})")
            if len(deletes) > 20:
                _out(f"  ... and {len(deletes) - 20} more (see {a.plan})")
            raise UserError(f"this plan deletes {len(deletes)} files from the device: rerun with --yes "
                            f"to go ahead, or --no-delete to only upload")
        if not used:
            raise UserError("deleting needs --used (the CSV from `projects used`), checked again before each delete")
    log = Path(a.log) if a.log else Path(a.plan).with_name(Path(a.plan).stem + "-log.csv")
    with device_lock(cfg.lock_file):
        try:
            stats = run.run_sync(_device(cfg), rows, log, used, do_delete, out=_out)
        except run.SyncStopped as e:
            raise UserError(str(e)) from None
    _out("done: " + ", ".join(f"{k} {v}" for k, v in stats.items()) + f"  (log: {log})")
    return 1 if stats["failed"] else 0


# ----------------------------------------------------------------------------- parser

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="sample-shepherd", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"sample-shepherd {__version__}")
    ap.add_argument("--config", help="config file (default: see `sample-shepherd config show`)")
    ap.add_argument("--work-dir", help="where backups and logs go by default")
    ap.add_argument("--device", help="device number (from `sample-shepherd device ls`)")
    ap.add_argument("--elektroid-cli", help="path to elektroid-cli")
    sub = ap.add_subparsers(dest="cmd", required=True, metavar="command")

    def add(parent, name, fn, help, dry=False):
        p = parent.add_parser(name, help=help, description=help)
        p.set_defaults(fn=fn)
        if dry:
            p.add_argument("--dry-run", action="store_true", help="show what would happen; change nothing")
        return p

    c = sub.add_parser("config", help="show the settings in effect").add_subparsers(dest="sub", required=True)
    add(c, "show", cmd_config_show, "print the settings in effect")

    o = sub.add_parser("organize", help="curate a library with Fourier Samples").add_subparsers(dest="sub", required=True)
    add(o, "doctor", cmd_organize_doctor, "check that Fourier is installed and configured")
    p = add(o, "build", cmd_organize_build, "run `fourier build` (with --dry-run: Fourier's own dry run)", dry=True)
    p.add_argument("args", nargs="*", help="more arguments for fourier build, after --")
    add(o, "patches", cmd_organize_patches, "list our patches to Fourier")
    p = add(o, "install-fourier", cmd_organize_install, "build the patched Fourier our profiles need", dry=True)
    p.add_argument("--dir", required=True, help="where to clone and build it")
    p.add_argument("--python", help="Python for its venv (uv's --python)")

    e = sub.add_parser("export", help="render to targets by device profile").add_subparsers(dest="sub", required=True)
    add(e, "profiles", cmd_export_profiles, "list device profiles")
    p = add(e, "render", cmd_export_render, "render a master for a profile (runs `fourier render`)", dry=True)
    p.add_argument("profile")
    p.add_argument("--from", dest="master", help="the master to render (default: Fourier's config)")
    p.add_argument("--out", help="output folder (default: Fourier's config)")
    p.add_argument("args", nargs="*", help="more arguments for fourier render, after --")
    p = add(e, "check", cmd_export_check, "check a render against its profile's limits (reads only)")
    p.add_argument("render")
    p.add_argument("--profile", required=True)
    p.add_argument("--show", type=int, default=30, help="issues to print")

    d = sub.add_parser("device", help="connected devices and their sample storage").add_subparsers(dest="sub", required=True)
    add(d, "ls", cmd_device_ls, "list connected devices")
    add(d, "info", cmd_device_info, "show the device's filesystems (what it supports)")
    p = add(d, "listing", cmd_device_listing, "list the sample storage to CSV (read-only)", dry=True)
    p.add_argument("--out", required=True)
    p.add_argument("--root", default="/")

    pr = sub.add_parser("projects", help="project backups and the samples they use").add_subparsers(dest="sub", required=True)
    add(pr, "ls", cmd_projects_ls, "list projects on the device")
    p = add(pr, "backup", cmd_projects_backup, "download every project, one folder per slot", dry=True)
    p.add_argument("--out", help="backup folder (default: <work_dir>/backups/<today>)")
    p.add_argument("--slots", nargs="+", help="only these slots")
    p = add(pr, "used", cmd_projects_used, "list the samples the backed-up projects use", dry=True)
    p.add_argument("--backups", required=True, help="folder of project backups")
    p.add_argument("--out", required=True, help="CSV to write: path,size,hash,projects")

    p = add(sub, "plan", cmd_plan, "compare listing, project usage and an export; write upload/delete plan", dry=True)
    p.add_argument("--listing", required=True, help="CSV from `device listing`")
    p.add_argument("--used", help="CSV from `projects used` (required for any delete)")
    p.add_argument("--export", help="rendered folder to sync")
    p.add_argument("--folders", nargs="+", help="only these top-level folders of the export")
    p.add_argument("--dest", default="/", help="device folder to sync into (default /)")
    p.add_argument("--prune", action="store_true", help="delete device files in the synced folders that the export doesn't have")
    p.add_argument("--replace", help="CSV of device paths to delete once replaced (path or '+Drive path' column)")
    p.add_argument("--out", required=True, help="plan CSV to write")

    p = add(sub, "sync", cmd_sync, "carry out a plan on the device (resumable)", dry=True)
    p.add_argument("--plan", required=True)
    p.add_argument("--used", help="CSV from `projects used`; every delete is checked against it again")
    p.add_argument("--log", help="log CSV (default: <plan>-log.csv); a rerun skips what it lists as done")
    p.add_argument("--yes", action="store_true", help="go ahead with the plan's deletes")
    p.add_argument("--no-delete", action="store_true", help="only upload")
    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    try:
        cfg = load_config(a)
        return a.fn(cfg, a) or 0
    except (UserError, DeviceBusy, FileNotFoundError, ValueError) as e:
        _err(f"error: {e}")
        return 2
    except KeyboardInterrupt:
        _err("stopped. Logged work is kept; rerun to resume.")
        return 130
    except BrokenPipeError:          # output piped into `head` etc.
        import os
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return 0
    except Exception as e:  # device errors etc.
        from sample_shepherd.sync.device import DeviceError
        if isinstance(e, DeviceError):
            _err(f"device error: {e}")
            return 3
        raise
