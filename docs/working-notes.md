# Working notes: the Digitakt II library build (October to November 2026)

These were the README of the one-off project this tool grew from. They record how Jules's
library was built and why things are the way they are. For using sample-shepherd, see
[the README](../README.md).


Builds a curated Digitakt II library from `~/Music/Ableton/User Library/Samples/sample packs`
with [Fourier Samples](https://github.com/bvk7787/fourier-samples), without touching the
source library or breaking existing Digitakt projects.

**Rules:** the Ableton User Library is a read-only input. Every write goes under `~/sample-work`.
Every script has `--dry-run`. Bulk operations get a written plan and your approval first.


## This repository

Our own code and config for the library, kept in git since 2026-11-06. The working tree stays in
`~/sample-work` (outputs, Fourier home, vendor checkouts); `scripts/`, `config/`, `fourier.env` and
this README there are symlinks into `~/workspace/digitakt-library`. `docs/` holds copies of the phase
reports and plans. `config/patches/` are our patches to Fourier Samples (base `131ee62`, branch
`local/adaptive-folders`); `config/ratings-snapshot.json` is a copy of `$FOURIER_HOME/ratings.json`.
No audio is ever committed.

## Layout

```
~/sample-work/
  README.md              this file
  fourier.env            source before any fourier command: points every Fourier path here
  vendor/fourier-samples Fourier, cloned and pinned at 131ee62; its own .venv
  config/                fourier.toml and device profiles (Phase 1)
  fourier-home/          Fourier's database, CLAP index, caches, logs (created by the first build)
  cache/huggingface/     CLAP model (created by the first build)
  out/                   master, renders, releases (Phase 1+)
  scripts/               our own scripts (Phase 3)
  reports/               phase reports, CSVs
  tmp/                   test-suite home and demo; safe to delete
```

## Phase 0: setup (done 2026-10-25)

Results: [reports/phase0-report.md](reports/phase0-report.md).

```bash
# install (project-local; nothing system-wide)
mkdir -p ~/sample-work/vendor
git clone https://github.com/bvk7787/fourier-samples ~/sample-work/vendor/fourier-samples
cd ~/sample-work/vendor/fourier-samples
git checkout 131ee62
# Python itself lives in ~/sample-work/vendor/python (uv-managed), not Homebrew: Homebrew removed
# its python@3.13 on 2026-11-06 and broke the old venv (moved to tmp/venv.broken-20261106)
UV_PYTHON_INSTALL_DIR=~/sample-work/vendor/python uv python install 3.13.16
uv sync --frozen --python ~/sample-work/vendor/python/cpython-3.13.16-macos-aarch64-none/bin/python3.13 --extra dev --extra clap

# tests: 2028 passed, 15 skipped (manual PDFs / Windows / CAF), 3 min
FOURIER_HOME=~/sample-work/tmp/test-home HF_HUB_OFFLINE=1 .venv/bin/python -m pytest -n auto -q -p no:cacheprovider

# smoke test: builds, verifies and renders 280 synthetic samples in 40 s
. ~/sample-work/fourier.env
fourier demo --dir ~/sample-work/tmp/fourier-demo
```

Source inspection used only `find`, `du` and `ls`. Per-pack counts are in `reports/packs-by-count.txt`.

## Phase 1: test run (done 2026-10-26; waiting for your listening review)

Results: [reports/phase1-report.md](reports/phase1-report.md). 239 of 480 files picked, verify PASS,
no folder over 50 files, every Digitakt file 48 kHz/16-bit. Took 62 s to build and 6 s per render.

Settings: `config/fourier.toml` (4 packs as library entries, `preset = "balanced"`, `retune = "off"`,
outputs under `out/`) and `config/devices/digitakt_2_50.yaml` (extends `digitakt_2`, 50 files a folder).

```bash
. ~/sample-work/fourier.env
cd ~/sample-work
P="$HOME/Music/Ableton/User Library/Samples/sample packs"
env -u FOURIER_CONFIG fourier setup --yes --to "$FOURIER_CONFIG" \
  --library "$P/old/Brad Brunazzi Vintage Drum Machines" \
  --library "$P/2025/WOST - CLUB DRUMZ VOL. 1 (sample pack)" \
  --library "$P/old/Lurka - Lurka Sample Pack" \
  --library "$P/2024/Chord Marauders - Geode - U.D. Sample Pack" \
  --device digitakt_2_50 --device generic_folder --preset balanced --processing prepared \
  --master out/master --renders out/renders --publish out/publish --clap --no-llm --no-build
# then added  retune = "off"  to config/fourier.toml
fourier build --dry-run                 # up to ~405 files, ~226 MB; wrote nothing
fourier build > reports/phase1-build-output.txt 2>&1
fourier render generic_folder           # preview for Ableton/XO -> out/renders/generic_folder
fourier render digitakt_2_50            # preview only (no --release); for format/folder checks
python -I scripts/build_report.py --out reports/phase1 [--dry-run]   # read-only report
```

Audition: `out/renders/generic_folder`, or `fourier open report` to listen and rate.

### Phase 1b: local Fourier patch for `SD_` names (done 2026-10-26)

Fourier read the vendor prefix `SD_` ("SD_Falcon_Kick") as "snare drum", so kicks, hats and toms
were lost or put in SNARES. An overlay can't change that (see the Phase 1 report), so Fourier
carries a local patch: branch `local/sd-vendor-prefix`, 3 commits on `131ee62` (patch 0004 adds `local/adaptive-folders` on top), also saved as
`config/patches/*.patch`. **If Fourier is ever re-cloned or upgraded, reapply them**:

```bash
cd ~/sample-work/vendor/fourier-samples
git switch -c local/sd-vendor-prefix 131ee62      # or the new upstream commit
git am ~/sample-work/config/patches/*.patch
FOURIER_HOME=~/sample-work/tmp/test-home HF_HUB_OFFLINE=1 .venv/bin/python -m pytest -n auto -q -p no:cacheprovider
```

Tests: 2048 passed, 15 skipped. Rebuild (same config, about 20 s; the previous master is kept
in `out/master.prev`):

```bash
. ~/sample-work/fourier.env && cd ~/sample-work
fourier build --dry-run
fourier build > reports/phase1b-build-output.txt 2>&1
fourier render generic_folder && fourier render digitakt_2_50
python -I scripts/build_report.py --out reports/phase1b
```

Result: no `SD_` file is placed nowhere any more (24 before). 242 source files are in the master,
250 files per render, and verify passes. Details and the before/after table are in the Phase 1
report under "Phase 1b". The Phase 1 file lists from before the patch are in `tmp/phase1a/`.

## Phase 2: full build of `sample packs` (run 2026-10-26/27; waiting for your review)

Results: [reports/phase2-report.md](reports/phase2-report.md). The build has 10,830 files in 317
subfolders, none over 50, every Digitakt file 48 kHz/16-bit, 5.7 GB. **Verify failed 5 checks**,
so the build is held in `out/full/master.next`. The report lists each failure and your options.
Nothing is published or released.

Settings: `config/fourier.toml` (the 4 year folders as library entries, `scale = "off"`, outputs
in `out/full/`; the Phase 1 config is saved in `tmp/fourier.phase1.toml`) and `config/overlay.yaml`
(`MAX_PER_FAMILY 50`, `FOLDER_MAX 24`, `FOLDER_MIN_FILES 6`).

```bash
. ~/sample-work/fourier.env && cd ~/sample-work
fourier config explain MAX_PER_FAMILY          # confirm the overlay is read
fourier build --dry-run
# libsndfile's MP3 decoder crashes (SIGBUS) when threads open MP3s together: analyze on 1 thread
fourier tools analyze --only librosa --workers 1
fourier tools analyze --workers 1
fourier build -j 6 > reports/phase2-build-output.txt 2>&1   # verify FAIL -> out/full/master.next
# previews of the held-back build (no release, nothing locked)
fourier render generic_folder --from out/full/master.next --out out/full/preview/generic_folder
fourier render digitakt_2_50  --from out/full/master.next --out out/full/preview/digitakt_2_50
python -I scripts/build_report.py --master out/full/master.next --renders out/full/preview --out reports/phase2
python -I scripts/folder_structure.py --root out/full/preview/digitakt_2_50 --out reports/phase2
```

Times: analysis about 2.5 h on 1 thread (cached now), build 12 min, renders 25 s each. Disk: 24 GB.

### Phase 2b: keep more files, three folder levels (built 2026-11-03; waiting for your review)

Results: [reports/phase2b-report.md](reports/phase2b-report.md): 29,863 files, 1,122 folders, none over 50, verify
failed 5 checks (held in `out/full2/master.next`). Plan: [reports/phase2b-plan.md](reports/phase2b-plan.md). Fourier patches 0004–0008 (branch
`local/adaptive-folders`): adaptive folder counts (a full folder splits instead of cutting files)
and a render-time third level `CATEGORY/group/family` named from Live 12's auto-tags
(`FOLDER_GROUPS`). Config: new `config/overlay.yaml`, outputs in `out/full2/`, profiles
`generic_folder_3` and `digitakt_2_50_3` (the Digitakt one is preview-only until nested folders are
checked on the device). Phase 2's overlay and config are saved in `tmp/overlay.phase2.yaml` and
`tmp/fourier.phase2.toml`.

## Device sessions and Phase 3 (prepared, not run)

- [reports/device-session-1-checklist.md](reports/device-session-1-checklist.md): backup first,
  then the +Drive listing, free space and project sample lists, all into `~/sample-work/device/`.
  No uploads, deletes, moves or restores.
- `scripts/drive_match.py` (shared matching), `scripts/project_coverage.py`, `scripts/delete_list.py`:
  read-only, with `--dry-run`. Both stop without the device data. They were tested only on made-up
  input in `tmp/phase3-selftest/`. Matching uses a byte hash, else name plus the 16-bit/48 kHz
  size, else name plus duration. A name alone is never enough.

### Phase 2c: verify fixes and finer groups (built 2026-11-06; verify passed, master in `out/full2/master`)

Plan: [reports/phase2c-plan.md](reports/phase2c-plan.md). 37 verify failures stored as Drop ratings
(`config/phase2b-drops.csv`); patch 0007 keeps drum words out of tonal folder names; patch 0008
groups foley by its files' names and splits closed hats. Previews re-rendered with the new groups;
rebuilt with your approval: 29,849 files, verify passed, master in place. Acapellas: waiting for your choice.

### Phase 3: device sync (2026-11-06/07)

All 11 projects backed up with Elektroid (`~/sample-work/device/backups/2026-11-06-elektroid/`, the
three "NEW PROJECT" slots in `slot-6/7/8/`); 71 samples in use, all matched on the +Drive by path and
hash. Uploads run at ~77 KB/s plus ~1.6 s a file, so only one-shots and tonal folders go on the
device (12,604 files, 1.68 GB). After 3,209 files the layout moved to four levels: the uploaded
folders were moved (elektroid `sample:mv`, counts checked) into `DRUMS/`, and the rest upload into
`DRUMS`, `TONAL`, `VOX`, `FX`, matching the `digitakt_2_50_4` render (patch 0009). The Live/XO
render is `out/full2/preview/generic_folder_4`. After the upload, `scripts/delete_replaced.py`
removes the 2,987 old one-shot/tonal samples they replace (never a project's).
