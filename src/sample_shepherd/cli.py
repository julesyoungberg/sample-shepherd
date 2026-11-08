"""The sample-shepherd command line.

  sample-shepherd organize   doctor | build | patches | install-fourier
  sample-shepherd export     profiles | render | check
  sample-shepherd device     ls | info | listing
  sample-shepherd projects   ls | backup | used
  sample-shepherd plan       listing + used + export -> plan CSV
  sample-shepherd sync       carry out a plan (resumable)
  sample-shepherd config     show | init
  sample-shepherd eval       categories | import-ratings | sample
  sample-shepherd tools      which helper tools are installed

Every command that writes files or touches a device takes --dry-run. Commands that delete
print the plan and need --yes. With --json (before the command), stdout is one JSON event
per line (see src/sample_shepherd/events.schema.json) and human text goes to stderr.
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

from sample_shepherd import __version__, config as config_mod, events
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


def cmd_config_init(cfg, a) -> int:
    target = Path(a.path).expanduser() if a.path else config_mod.user_config_path()
    if target.exists():
        raise UserError(f"{target} already exists; edit it, or choose another --path")
    text = config_mod.example_config().read_text(encoding="utf-8")
    if a.dry_run:
        _out(f"(dry run: would write the starter config to {target})")
        return 0
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    _out(f"wrote {target}. Edit its paths, then check them with `sample-shepherd config show`.")
    if target.resolve() != config_mod.user_config_path().resolve():
        _out(f"note: this file isn't looked up by default; pass --config {target} "
             f"or set ${config_mod.ENV_VAR} to use it")
    elif cfg.path and Path(cfg.path).resolve() != target.resolve():
        _out(f"note: {cfg.path} is the config in effect here and takes precedence over {target} "
             f"(lookup order: --config, ${config_mod.ENV_VAR}, ./sample-shepherd.toml, then this file)")
    return 0


# ----------------------------------------------------------------------------- tools

#: what each external tool is needed for, shown by `tools` and the app's setup screen
TOOL_USES = {
    "elektroid-cli": ["device", "projects", "sync"],
    "fourier": ["organize", "export render"],
}


def _tool_version(exe: str, cfg) -> str | None:
    import subprocess
    from sample_shepherd.organize import fourier
    try:
        r = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=30,
                           env=fourier.env_for(cfg))
    except (OSError, subprocess.TimeoutExpired):
        return None
    first = (r.stdout or r.stderr).strip().splitlines()
    return first[0] if r.returncode == 0 and first else None


def cmd_tools(cfg, a) -> int:
    import os
    import shutil
    from sample_shepherd.organize import fourier
    # elektroid-cli is only located, never run: running it could talk to a connected device.
    elektroid = cfg.elektroid_cli
    found = {
        "elektroid-cli": (elektroid if os.access(elektroid, os.X_OK) and Path(elektroid).is_file() else None)
        if "/" in elektroid
        else shutil.which(elektroid),
        "fourier": fourier.resolve_command(cfg),
    }
    missing = []
    for name, uses in TOOL_USES.items():
        path = found[name]
        version = _tool_version(path, cfg) if path and name == "fourier" else None
        if path is None:
            missing.append(name)
        _out(f"{name:14} {path or 'NOT FOUND'}{f'  ({version})' if version else ''}  needed for: {', '.join(uses)}")
        a.events.emit("row", kind="tool", name=name, found=path is not None, path=path,
                      version=version, enables=uses)
    if missing:
        _out("See docs/cli/getting-started.md for how to install them.")
    a.events.summary["missing"] = missing
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
    limit = a.max_name_length if a.max_name_length is not None else check.default_name_limit(prof)
    stats, issues = check.check_render(Path(a.render), prof, max_name_length=limit or None)
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


def _dry_device(cfg, a, op: str) -> bool:
    """For a read-only device command's --dry-run: say what would run, touch nothing."""
    if not a.dry_run:
        return False
    _out(f"would run: {_device(cfg).describe(op)}")
    _out("(dry run: the device wasn't contacted)")
    return True


def cmd_device_ls(cfg, a) -> int:
    if _dry_device(cfg, a, "list_devices"):
        return 0
    with device_lock(cfg.lock_file):
        devs = _device(cfg).list_devices()
    for d in devs:
        _out(f"{d.number}: {d.name} ({d.id})")
    if not devs:
        _out("no devices found")
    return 0


def cmd_device_info(cfg, a) -> int:
    if _dry_device(cfg, a, "info"):
        return 0
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
    if _dry_device(cfg, a, "list_projects"):
        return 0
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
        if not a.dry_run and not a.slots:
            # every slot the device has, so `projects used` can tell a complete backup
            write_csv(out / projects.SLOTS_FILE, projects.SLOTS_HEADER,
                      ([s.slot, s.name, "" if s.size is None else s.size] for s in slots))
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
    found, expected, problems = projects.completeness(Path(a.backups))
    for p in problems:
        _out(f"  {p}")
    if problems and not a.allow_partial:
        raise UserError("this backup may not hold every project, and samples only a missing project "
                        "uses would look deletable. Finish the backup (`projects backup` again), or "
                        "pass --allow-partial if you're sure it's complete")
    slots = f"{found} of {expected} slots" if expected is not None else "slot count unknown"
    _out(f"{len(files)} project files ({slots}) use {len(used)} distinct samples")
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
            stats = run.run_sync(_device(cfg), rows, log, used, do_delete, out=_out, protected=cfg.protected)
        except run.SyncStopped as e:
            raise UserError(str(e)) from None
    _out("done: " + ", ".join(f"{k} {v}" for k, v in stats.items()) + f"  (log: {log})")
    return 1 if stats["failed"] else 0


# ----------------------------------------------------------------------------- eval

def _labels_path(a) -> Path:
    from sample_shepherd.evaluate import labels
    return Path(a.labels).expanduser() if a.labels else labels.bundled_labels()


def _thresholds(specs: list[str] | None) -> dict[str, float]:
    out = {}
    for s in specs or []:
        name, sep, val = s.partition("=")
        try:
            out[name] = float(val)
        except ValueError:
            sep = ""
        if not sep or not name:
            raise UserError(f"--fail-under takes SYSTEM=ACCURACY, e.g. rules=0.8 (got {s!r})")
    return out


def cmd_eval_categories(cfg, a) -> int:
    from sample_shepherd.evaluate import labels as lab_mod, report
    path = _labels_path(a)
    labs = lab_mod.load_labels(path)
    if a.provenance:
        labs = [x for x in labs if x.provenance in a.provenance]
    if not labs:
        raise UserError(f"no labels to evaluate in {path}" + (f" with provenance {a.provenance}" if a.provenance else ""))
    floors = _thresholds(a.fail_under)
    results = report.run(labs, a.baselines if a.baselines is not None else list(report.BASELINES),
                         [Path(p).expanduser() for p in a.predictions or []])
    _out(f"label file: {path}")
    _out(report.format_report(labs, results, a.detail, a.show))
    if a.json:
        if a.dry_run:
            _out(f"(dry run: would write {a.json})")
        else:
            Path(a.json).expanduser().parent.mkdir(parents=True, exist_ok=True)
            Path(a.json).expanduser().write_text(report.results_json(labs, results), encoding="utf-8")
            _out(f"wrote {a.json}")
    failed = []
    for name, floor in floors.items():
        r = next((r for r in results if r.system == name), None)
        if r is None:
            raise UserError(f"--fail-under names {name!r}, which wasn't evaluated")
        if r.accuracy < floor:
            failed.append(f"{name} accuracy {r.accuracy:.2f} < {floor:.2f}")
    if failed:
        _err("below the floor: " + "; ".join(failed))
        return 1
    return 0


def cmd_eval_import(cfg, a) -> int:
    from sample_shepherd.evaluate import labels as lab_mod
    target = Path(a.labels).expanduser()
    new, skipped = lab_mod.labels_from_ratings(Path(a.ratings).expanduser(), a.root)
    existing = lab_mod.load_labels(target) if target.exists() else []
    merged, added, changed, confirmed = lab_mod.merge(existing, new)
    _out(f"{len(new)} labels from {a.ratings}: {added} new, {changed} relabeled and {confirmed} confirmed "
         f"by a human rating, {len(new) - added - changed - confirmed} already there; {len(skipped)} rows skipped")
    for s in skipped[:a.show]:
        _out(f"  skipped {s}")
    if len(skipped) > a.show:
        _out(f"  ... and {len(skipped) - a.show} more")
    if a.dry_run:
        _out(f"(dry run: would write {len(merged)} labels to {target})")
        return 0
    lab_mod.write_labels(target, merged)
    _out(f"wrote {target} ({len(merged)} labels)")
    return 0


def cmd_eval_sample(cfg, a) -> int:
    from sample_shepherd.evaluate import labels as lab_mod, report
    known = _labels_path(a)
    exclude = lab_mod.load_labels(known) if known.exists() else []
    rows = report.sample_sheet(Path(a.manifest).expanduser(), a.per_category, a.seed, exclude)
    out = Path(a.out).expanduser()
    if out.exists():
        raise UserError(f"{out} already exists; it may hold your labels. Choose another --out")
    _out(f"{len(rows)} samples to label ({a.per_category} per category at most, seed {a.seed})")
    if a.dry_run:
        _out(f"(dry run: would write {out})")
        return 0
    write_csv(out, ["path", "category", "provenance", "note"], [[r[k] for k in ("path", "category", "provenance", "note")] for r in rows])
    _out(f"wrote {out}. Listen to each, fill in category, then: sample-shepherd eval categories --labels {out}")
    return 0


# ----------------------------------------------------------------------------- parser

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="sample-shepherd", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"sample-shepherd {__version__}")
    ap.add_argument("--config", help="config file (default: see `sample-shepherd config show`)")
    ap.add_argument("--work-dir", help="where backups and logs go by default")
    ap.add_argument("--device", help="device number (from `sample-shepherd device ls`)")
    ap.add_argument("--elektroid-cli", help="path to elektroid-cli")
    ap.add_argument("--json", dest="json_events", action="store_true",
                    help="write JSON events to stdout, one per line, and human text to stderr")
    sub = ap.add_subparsers(dest="cmd", required=True, metavar="command")

    def add(parent, name, fn, help, dry=False):
        p = parent.add_parser(name, help=help, description=help)
        p.set_defaults(fn=fn)
        if dry:
            p.add_argument("--dry-run", action="store_true", help="show what would happen; change nothing")
        return p

    c = sub.add_parser("config", help="show the settings in effect").add_subparsers(dest="sub", required=True)
    add(c, "show", cmd_config_show, "print the settings in effect")
    p = add(c, "init", cmd_config_init, "write a starter config file to edit", dry=True)
    p.add_argument("--path", help="where to write it (default: ~/.config/sample-shepherd/config.toml)")

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
    p.add_argument("profile", help="profile name (see `export profiles`)")
    p.add_argument("--from", dest="master", help="the master to render (default: Fourier's config)")
    p.add_argument("--out", help="output folder (default: Fourier's config)")
    p.add_argument("args", nargs="*", help="more arguments for fourier render, after --")
    p = add(e, "check", cmd_export_check, "check a render against its profile's limits (reads only)")
    p.add_argument("render", help="the rendered folder to check")
    p.add_argument("--profile", required=True, help="the profile it was rendered with")
    p.add_argument("--show", type=int, default=30, help="issues to print")
    p.add_argument("--max-name-length", type=int,
                   help="flag longer sample names (default: 32 for Elektron profiles; 0 turns it off)")

    d = sub.add_parser("device", help="connected devices and their sample storage").add_subparsers(dest="sub", required=True)
    add(d, "ls", cmd_device_ls, "list connected devices", dry=True)
    add(d, "info", cmd_device_info, "show the device's filesystems (what it supports)", dry=True)
    p = add(d, "listing", cmd_device_listing, "list the sample storage to CSV (read-only)", dry=True)
    p.add_argument("--out", required=True, help="CSV to write: path,size,hash")
    p.add_argument("--root", default="/", help="device folder to list (default /)")

    pr = sub.add_parser("projects", help="project backups and the samples they use").add_subparsers(dest="sub", required=True)
    add(pr, "ls", cmd_projects_ls, "list projects on the device", dry=True)
    p = add(pr, "backup", cmd_projects_backup, "download every project, one folder per slot", dry=True)
    p.add_argument("--out", help="backup folder (default: <work_dir>/backups/<today>)")
    p.add_argument("--slots", nargs="+", help="only these slots")
    p = add(pr, "used", cmd_projects_used, "list the samples the backed-up projects use", dry=True)
    p.add_argument("--backups", required=True, help="folder of project backups")
    p.add_argument("--out", required=True, help="CSV to write: path,size,hash,projects")
    p.add_argument("--allow-partial", action="store_true",
                   help="go ahead even if the backup can't be shown to hold every project")

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
    p.add_argument("--plan", required=True, help="plan CSV from `plan`")
    p.add_argument("--used", help="CSV from `projects used`; every delete is checked against it again")
    p.add_argument("--log", help="log CSV (default: <plan>-log.csv); a rerun skips what it lists as done")
    p.add_argument("--yes", action="store_true", help="go ahead with the plan's deletes")
    p.add_argument("--no-delete", action="store_true", help="only upload")

    add(sub, "tools", cmd_tools, "show which helper tools (elektroid-cli, fourier) are installed")

    ev = sub.add_parser("eval", help="measure category sorting against hand-labeled samples").add_subparsers(dest="sub", required=True)
    p = add(ev, "categories", cmd_eval_categories,
            "score baselines and real systems (e.g. a Fourier manifest) on a label set (reads only)", dry=True)
    p.add_argument("--labels", help="label CSV: path,category,provenance,note (default: the bundled seed set)")
    p.add_argument("--predictions", nargs="+", metavar="FILE",
                   help="a system's output: a Fourier master folder or manifest.json, or a path,category CSV")
    p.add_argument("--baselines", nargs="*", metavar="NAME",
                   help="baselines to run: majority name folder rules (default: all; none: --baselines)")
    p.add_argument("--provenance", nargs="+", help="only labels from these sources (e.g. listened rated-keep)")
    p.add_argument("--detail", help="system to break down by category (default: the last one)")
    p.add_argument("--show", type=int, default=20, help="errors to print")
    p.add_argument("--json", help="also write the full results here")
    p.add_argument("--fail-under", nargs="+", metavar="SYSTEM=ACC",
                   help="exit 1 if a system's accuracy is below this, e.g. rules=0.8 (for CI)")
    p = add(ev, "import-ratings", cmd_eval_import,
            "add labels from your Fourier ratings (ratings.json or a review CSV): Keep and Misfiled rows", dry=True)
    p.add_argument("ratings", help="$FOURIER_HOME/ratings.json, or a path,rating,category CSV")
    p.add_argument("--labels", required=True, help="label CSV to add to (created if missing)")
    p.add_argument("--root", help="the library root the rated paths start with (they're stored relative to it)")
    p.add_argument("--show", type=int, default=10, help="skipped rows to print")
    p = add(ev, "sample", cmd_eval_sample,
            "write a labeling sheet: random samples from each category of a master, category left blank", dry=True)
    p.add_argument("manifest", help="a Fourier master folder or its manifest.json (read only)")
    p.add_argument("--out", required=True, help="CSV to write; fill in category after listening")
    p.add_argument("--per-category", type=int, default=10)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--labels", help="already-labeled paths to leave out (default: the bundled seed set)")
    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    if not a.json_events:
        a.events = events.Events()
        return _run(a)
    with events.json_mode() as ev:
        a.events = ev
        ev.emit("start", cmd=" ".join(x for x in (a.cmd, getattr(a, "sub", None)) if x),
                dry_run=bool(getattr(a, "dry_run", False)))
        code = _run(a)
        if not a.error:
            ev.emit("result", ok=code == 0, exit=code, summary=ev.summary)
        return code


def _fail(a, code: str, msg: str, exit: int) -> int:
    _err(msg)
    a.error = code
    a.events.emit("error", code=code, msg=msg, exit=exit)
    return exit


def _run(a) -> int:
    a.error = None
    try:
        cfg = load_config(a)
        return a.fn(cfg, a) or 0
    except DeviceBusy as e:
        return _fail(a, "device_busy", f"error: {e}", 2)
    except (UserError, FileNotFoundError, ValueError) as e:
        return _fail(a, "user_error", f"error: {e}", 2)
    except KeyboardInterrupt:
        return _fail(a, "stopped", "stopped. Logged work is kept; rerun to resume.", 130)
    except BrokenPipeError:          # output piped into `head` etc.
        import os
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return 0
    except Exception as e:  # device errors etc.
        from sample_shepherd.sync.device import DeviceError
        if isinstance(e, DeviceError):
            return _fail(a, "device_error", f"device error: {e}", 3)
        # A bug: tell the app the run is over, then let the traceback go to stderr.
        a.error = "internal"
        a.events.emit("error", code="internal", msg=f"{type(e).__name__}: {e}", exit=1)
        raise
