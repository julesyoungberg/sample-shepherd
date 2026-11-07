# sample-shepherd

Organize a sample library, export it for each of your instruments, and sync it to hardware
samplers without breaking the projects already on them.

It's one command, `sample-shepherd`, with three layers:

1. **organize**: curate a library (classify, name, dedupe, rate, folder). This is done by
   [Fourier Samples](https://github.com/bvk7787/fourier-samples), which sample-shepherd runs
   as a separate program.
2. **export**: render the curated library for a target by *device profile*: a plain folder
   for Ableton Live or XO, a Digitakt II layout, or your own profile.
3. **sync**: back up the device's projects, work out which samples they use, plan what to
   upload and delete, and carry the plan out, resumably. Elektron devices come first,
   through [Elektroid](https://github.com/dagargo/elektroid)'s `elektroid-cli`.

It was built for one producer's Digitakt II, a library of about 30,000 samples synced over a
USB link that moves about 77 KB/s. So it's careful by default: every command that writes
or touches a device has `--dry-run`, nothing deletes without `--yes`, and a sample a project
uses is never deleted.

## Safety first

Read this before pointing it at a device you care about.

- **Back up your projects first** (`sample-shepherd projects backup`), and copy the backup off
  your computer too. Never "test" a backup by restoring it: a restore overwrites the project
  on the device.
- **Projects reference samples by hash and size.** Delete a sample a project uses and the
  project loses it. `plan` reads every backed-up project's sample list and won't delete
  any of those samples, matched by path or by content hash. With no project list at all, it
  won't delete anything.
- **One program talks to the device at a time.** Concurrent MIDI access can corrupt a
  transfer. sample-shepherd holds a lock per device (in `$XDG_RUNTIME_DIR` or the temp
  folder) while it uses it, but it can't see other programs: close Elektron Transfer, and
  don't run `elektroid-cli` by hand, or the older `scripts/` (which don't take the lock),
  alongside it.
- **Uploads never overwrite.** A file whose name is already in its device folder is skipped.
- **Deletes come last.** `sync` deletes only after every upload in the plan has succeeded,
  and checks each delete again the way `plan` does (protected paths, paths and content
  hashes projects use), so a hand-edited or stale plan can't slip one through.
- **An incomplete backup is refused.** `projects used` checks the backup against the slot
  list `projects backup` saved, so a missing project can't make its samples look deletable.
- **Your source library is read-only input.** Nothing here writes to it.
- **No audio goes in this repository.** `.gitignore` excludes wav/mp3/aif/flac; tests make
  their own tiny silent files at run time.

## Prerequisites

- **Python 3.11+** and [uv](https://docs.astral.sh/uv/) (or pipx).
- **For sync:** `elektroid-cli`, built from source on macOS (below). On Debian/Ubuntu,
  `apt install elektroid` provides it.
- **For organize and export render:** Fourier Samples. Our device profiles and overlay need
  our patched build (`sample-shepherd organize install-fourier`, below). Fourier is
  Apache-2.0. If you use its CLAP model, note that the model's training data is marked
  research-use only; see Fourier's README.
- `export check`, `plan` and `projects used` need neither: they read files only.

### Elektroid (`elektroid-cli`) on macOS

Elektroid is GPLv3. sample-shepherd runs it as a separate program and doesn't include it.

```bash
brew install autoconf automake libtool glib json-glib libsndfile libsamplerate libzip zlib \
  rtmidi rtaudio rubberband
git clone https://github.com/dagargo/elektroid
cd elektroid
```

**One fix is needed for a CLI-only build.** Upstream `configure.ac` line 72 asks for GTK
exactly when the GUI is turned *off*. Swap the two branches so it reads:

```
AM_COND_IF(ELEKTROID_BUILD_GUI, [PKG_CHECK_MODULES([GTK], [gtk+-3.0])], [])
```

Then build into a folder of your choice:

```bash
autoreconf --install
./configure --prefix="$HOME/opt/elektroid" BUILD_GUI=no
make && make install
"$HOME/opt/elektroid/bin/elektroid-cli" ld      # 0 is your computer, 1 the first device
```

Point sample-shepherd at it with `[elektroid] cli = "..."` in the config, or
`--elektroid-cli`.

## Install

```bash
uv tool install git+https://github.com/julesyoungberg/sample-shepherd
# or: pipx install git+https://github.com/julesyoungberg/sample-shepherd
# with stock Fourier from PyPI as well: uv tool install 'sample-shepherd[organize] @ git+https://...'
sample-shepherd --help
```

From a checkout, for development:

```bash
uv venv && uv pip install -e '.[dev]'
.venv/bin/pytest            # no device needed
```

## Configure

```bash
sample-shepherd config init        # writes ~/.config/sample-shepherd/config.toml (--dry-run to preview)
sample-shepherd config show        # what's in effect
```

Edit the paths in that file: where `elektroid-cli` and `fourier` are, and `work_dir` (where
backups, listings and plans go by default). Every setting is optional, and flags override the
file (`--config`, `--work-dir`, `--device`, `--elektroid-cli`). The starter file is
[examples/sample-shepherd.toml](examples/sample-shepherd.toml);
[examples/original-build.toml](examples/original-build.toml) is the config the first
Digitakt II library build used, for a fuller real-world example.

## Walkthrough: from sample packs to a synced Digitakt II

The whole path, one step at a time. Each step's output is the next step's input, and you can
stop after any of them: steps 1 and 2 alone give you a curated library for Live or XO.

### 1. Organize: curate your sample packs

Fourier Samples reads your packs (read-only), classifies and names every sample, drops
duplicates and weak ones, and writes a curated *master*.

```bash
sample-shepherd organize install-fourier --dir ~/opt/fourier-samples --dry-run   # the steps
sample-shepherd organize install-fourier --dir ~/opt/fourier-samples             # patched build
# then in your config: [fourier] command = "~/opt/fourier-samples/.venv/bin/fourier"
```

Give Fourier a config: copy [examples/fourier.toml](examples/fourier.toml) (and
[config/overlay.yaml](config/overlay.yaml) next to it), set `library` to your sample-pack
folders and `[output]` to where the master and renders go, and point sample-shepherd at it
with `[fourier] env = { FOURIER_HOME = "...", FOURIER_CONFIG = "/path/to/fourier.toml" }`.
Or run Fourier's own `fourier setup`, which asks the same questions.

```bash
sample-shepherd organize doctor              # Fourier found and configured?
sample-shepherd organize build --dry-run     # what a build would do; writes nothing
sample-shepherd organize build               # scan, analyze, build and verify (resumable; long the first time)
```

Fourier's own commands work on the same setup: `fourier open report` to listen and rate,
`fourier publish` to freeze a release. See its README.

### 2. Export: render the master for each target

```bash
sample-shepherd export profiles                                     # what's available
sample-shepherd export render generic_folder_3 --out ~/sample-shepherd/renders/live --dry-run
sample-shepherd export render generic_folder_3 --out ~/sample-shepherd/renders/live    # Live / XO
sample-shepherd export render digitakt_2_50_3 --out ~/sample-shepherd/renders/digitakt
sample-shepherd export check ~/sample-shepherd/renders/digitakt --profile digitakt_2_50_3
```

`export check` reads the render and reports anything the device would refuse or hide: too
many files in a folder, folders too deep, the wrong sample rate or bit depth, names too long.
For Live or XO you're done: add the render folder to Live's browser, or drag it into XO.

### 3. Back up the device's projects

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

### 4. Plan

List what's on the device (read-only), then compare it with the render and the projects:

```bash
sample-shepherd device listing --out listing.csv
sample-shepherd plan --listing listing.csv --used used.csv \
    --export ~/sample-shepherd/renders/digitakt --folders 01_KICKS 02_SNARES \
    --prune --out plan.csv
```

Without `--prune` (or `--replace`) the plan only uploads. Read `plan.csv`: every row says
what will happen and why. Delete a row and it won't happen.

### 5. Sync

```bash
sample-shepherd sync --plan plan.csv --dry-run                  # summary and time estimate
sample-shepherd sync --plan plan.csv --no-delete                # uploads only
sample-shepherd sync --plan plan.csv --used used.csv --yes      # uploads, then the deletes
```

Stop it any time (Ctrl-C, a dropped cable): run the same command again and it carries on
from its log (`plan-log.csv`). Transfers are slow (about 77 KB/s plus 1.6 s per file on a
Digitakt II), so `plan` and `sync --dry-run` print a time estimate. Set `[transfer]` in the
config to your own speeds; `sync` prints the measured speed as it goes.

### Dry runs and the device

`--dry-run` never changes anything. For `device ls`, `device info` and `projects ls` it
doesn't contact the device either; it prints the `elektroid-cli` command it would run.
`device listing --dry-run` and `projects backup --dry-run` do read the device (one folder
listing, the project list) to give you counts and a time estimate, so don't run them while
another program is transferring.

## Commands

| Command | What it does | Writes / touches |
|---|---|---|
| `config show` / `config init [--path P] [--dry-run]` | Settings in effect / write a starter config | `init`: the config file |
| `organize doctor` | Is Fourier installed and configured? | nothing |
| `organize build [--dry-run] [-- args]` | Runs `fourier build` | Fourier's outputs |
| `organize patches` | Lists our patches to Fourier | nothing |
| `organize install-fourier --dir D [--dry-run]` | Clones Fourier at the base commit, applies the patches, `uv sync` | `D` |
| `export profiles` | Lists device profiles | nothing |
| `export render PROFILE [--from M] [--out O] [--dry-run]` | Runs `fourier render` with our profiles | `O` |
| `export check RENDER --profile P` | Checks files per folder, folder depth, sample rate, bit depth, and (Elektron) names over 32 characters | nothing |
| `device ls` / `device info` `[--dry-run]` | Connected devices / a device's filesystems | reads the device |
| `device listing --out CSV [--dry-run]` | Lists the sample storage: `path,size,hash` | reads the device |
| `projects ls [--dry-run]` | Lists project slots | reads the device |
| `projects backup [--out DIR] [--slots ...] [--dry-run]` | Downloads projects, one folder per slot, plus `backup-index.csv` with SHA-256s | reads the device; writes `DIR` |
| `projects used --backups DIR --out CSV [--allow-partial]` | Samples the backed-up projects use: `path,size,hash,projects`. Refuses a backup missing any slot | `CSV` |
| `plan ... --out CSV [--dry-run]` | Upload/delete plan (see below) | `CSV` |
| `sync --plan CSV [--used CSV] [--yes] [--no-delete] [--dry-run]` | Carries out a plan, logging each step to `<plan>-log.csv` | **the device** |

### How `plan` decides

- **Upload** each export file whose device path (folder plus name, no extension) isn't on the
  device. `--folders` limits it to some top-level folders, and `--dest` puts them under a device
  folder.
- **Delete candidates** come only from what you ask for: `--prune` (device files inside the
  synced folders that the export doesn't have), and `--replace CSV` (a list of device paths,
  for example from your own matching).
- A candidate is **kept** if a project uses it (same path, ignoring case, or the same content
  hash), or if it's under a protected path (`[sync] protected`, `/factory` by default).
- Every row is in the CSV with its reason (and, for delete candidates, the device's content
  hash): `upload`, `delete`, `skip-exists`, `keep-used`, `keep-protected`, `skip-missing`.
  You can delete rows before syncing. A delete row you add by hand needs its `hash` from the
  listing, or `sync` refuses it.

## Supported devices

Elektron, through `elektroid-cli`. What works depends on the device's filesystems
(`device info`):

| Device | Sample sync | Project backup | Projects list their samples (`projects used`) |
|---|---|---|---|
| Digitakt II | yes (stereo kept) | yes (`.dt2prj`) | yes |
| Digitakt | yes (mono) | yes (`.dtprj`) | yes |
| Analog Rytm MKI/MKII | yes (mono) | yes (`.arprj`) | yes |
| Model:Samples | yes (mono) | yes (`.msprj`) | yes |
| Syntakt | no (slot-based `data-sample` only) | yes | no |
| Digitone I/II | no sample filesystem | yes | no |

Only the Digitakt II has been used with real hardware so far. `projects used` stops with an
error for a project whose package has no sample list, rather than treating it as "uses
nothing". Adding another device family: [docs/adding-a-device.md](docs/adding-a-device.md).

## Device profiles

Profiles are YAML in Fourier's format. Bundled ones (from [config/devices](config/devices)):

- `digitakt_2_50`: Digitakt II, 48 kHz/16-bit, at most 50 files a folder, two levels.
- `digitakt_2_50_3`: the same with three levels, `CATEGORY/group/family`.
- `generic_folder_3`: a plain folder for Live or XO, 44.1 kHz/24-bit, three levels.

Fourier's own profiles (`digitakt_2`, `generic_folder`, `m8`, ...) work too. To write your
own, see [docs/adding-a-profile.md](docs/adding-a-profile.md).

## Fourier and our patches

Fourier is an external command here, found through `[fourier] command` or `PATH`, with the
environment from `[fourier] env`. Our 8 patches to it live in
[config/patches](config/patches); [docs/fourier-patches.md](docs/fourier-patches.md) says
what each does, whether our config needs it, and how it could go upstream.

## Repository layout

```
src/sample_shepherd/   the package: cli.py, config.py, organize/, export/, sync/
tests/                 pytest; tests/fake/elektroid-cli stands in for a device
config/                Fourier config, device profiles, patches, curation decisions
examples/              starter configs for sample-shepherd and Fourier
docs/                  how-tos, and the notes and reports from the original library build
scripts/               the original one-off scripts (still in use; see below)
```

`scripts/` holds the scripts the first library build used: listing, upload, guarded delete,
source matching and reports. They're kept where they are and working, because a working
tree runs them by path. The package replaces the device parts (`drive_listing.py`,
`upload_tree.py`, `delete_replaced.py`) with `device listing`, `plan` and `sync`; the
source-library matching (`drive_match.py`, `delete_list.py`) and reports read Fourier's
database and stay scripts for now. Its output can feed `plan --replace`.

## Possible later work

A TUI or small web page for reviewing plans; more devices (SDS samplers, which Elektroid
supports); recording measured transfer speed per device.
