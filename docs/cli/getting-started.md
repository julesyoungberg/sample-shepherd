# Getting started: from sample packs to a synced Digitakt II

This walks the whole path once. It assumes you've [installed](../../README.md#install)
sample-shepherd and written a config (`sample-shepherd config init`; see
[Configuration](configuration.md)). Read the [safety rules](../../README.md#safety-first)
before step 3.

Every command here that writes or touches the device takes `--dry-run`: run that first,
read what it says, then run it for real. [Commands](commands.md) says exactly what each one
reads and writes.

The whole path, one step at a time. Each step's output is the next step's input, and you can
stop after any of them: steps 1 and 2 alone give you a curated library for Live or XO.

## 1. Organize: curate your sample packs

Fourier Samples reads your packs (read-only), classifies and names every sample, drops
duplicates and weak ones, and writes a curated *master*.

```bash
sample-shepherd organize install-fourier --dir ~/opt/fourier-samples --dry-run   # the steps
sample-shepherd organize install-fourier --dir ~/opt/fourier-samples             # patched build
# then in your config: [fourier] command = "~/opt/fourier-samples/.venv/bin/fourier"
```

Give Fourier a config: copy [examples/fourier.toml](../../examples/fourier.toml) (and
[config/overlay.yaml](../../config/overlay.yaml) next to it), set `library` to your sample-pack
folders and `[output]` to where the master and renders go, and point sample-shepherd at it
with `[fourier] env = { FOURIER_HOME = "...", FOURIER_CONFIG = "/path/to/fourier.toml" }`.
Or run Fourier's own `fourier setup`, which asks the same questions.

```bash
sample-shepherd tools                        # elektroid-cli and fourier found?
sample-shepherd organize doctor              # Fourier found and configured?
sample-shepherd organize build --dry-run     # what a build would do; writes nothing
sample-shepherd organize build               # scan, analyze, build and verify (resumable; long the first time)
```

Fourier's own commands work on the same setup: `fourier open report` to listen and rate,
`fourier publish` to freeze a release. See its README.

## 2. Export: render the master for each target

```bash
sample-shepherd export profiles                                     # what's available
sample-shepherd export render generic_folder_4 --out ~/sample-shepherd/renders/live --dry-run
sample-shepherd export render generic_folder_4 --out ~/sample-shepherd/renders/live    # Live / XO
sample-shepherd export render digitakt_2_50_4 --out ~/sample-shepherd/renders/digitakt
sample-shepherd export check ~/sample-shepherd/renders/digitakt --profile digitakt_2_50_4
```

`export check` reads the render and reports anything the device would refuse or hide: too
many files in a folder, folders too deep, the wrong sample rate or bit depth, names too long.
For Live or XO you're done: add the render folder to Live's browser, or drag it into XO.

## 3. Back up the device's projects

From here on sample-shepherd talks to the device. Close Elektron Transfer first.

```bash
sample-shepherd device ls                       # find its number (1 for the first device)
sample-shepherd device info                     # its filesystems; "sample" means sync works
sample-shepherd projects backup --out backups/2026-11-07 --dry-run   # what and how long
sample-shepherd projects backup --out backups/2026-11-07             # one folder per slot
```

Copy the backup folder off your computer too. Then list what the projects use. This reads
the backup, not the device:

```bash
sample-shepherd projects used --backups backups/2026-11-07 --out used.csv
```

## 4. Plan

List what's on the device (read-only), then compare it with the render and the projects:

```bash
sample-shepherd device listing --out listing.csv
sample-shepherd plan --listing listing.csv --used used.csv \
    --export ~/sample-shepherd/renders/digitakt --folders DRUMS/01_KICKS DRUMS/02_SNARES \
    --prune --out plan.csv
```

Name category folders under their section (`DRUMS/01_KICKS`), not a whole section: with
`--prune`, the folders you name are the delete scope, and `--folders DRUMS` would make all of
`/DRUMS` on the device fair game. If you already keep your own folders called `DRUMS`, `FX`,
`LOOPS`, `TONAL` or `VOX` (names match ignoring case), always pass `--folders` with `--prune`,
or render to a three-level profile.

Without `--prune` (or `--replace`) the plan only uploads. Read `plan.csv`: every row says
what will happen and why. Delete a row and it won't happen.

## 5. Sync

```bash
sample-shepherd sync --plan plan.csv --dry-run                  # summary and time estimate
sample-shepherd sync --plan plan.csv --no-delete                # uploads only
sample-shepherd sync --plan plan.csv --used used.csv --yes      # uploads, then the deletes
```

Stop it any time (Ctrl-C, a dropped cable): run the same command again and it carries on
from its log (`plan-log.csv`). Transfers are slow (about 77 KB/s plus 1.6 s per file on a
Digitakt II), so `plan` and `sync --dry-run` print a time estimate. Set `[transfer]` in the
config to your own speeds; `sync` prints the measured speed as it goes.

## Next

- [Commands](commands.md): each command in more depth, including how `plan` decides.
- [Command reference](reference.md): every flag.
- Another sampler or layout: [adding a profile](../adding-a-profile.md).
