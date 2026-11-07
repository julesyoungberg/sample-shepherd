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
  transfer. sample-shepherd holds a lock while it uses the device, but it can't see other
  programs: close Elektron Transfer and don't run `elektroid-cli` by hand alongside it.
- **Uploads never overwrite.** A file whose name is already in its device folder is skipped.
- **Deletes come last.** `sync` deletes only after every upload in the plan has succeeded,
  and checks each delete against the project list again.
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

Copy [examples/sample-shepherd.toml](examples/sample-shepherd.toml) to
`~/.config/sample-shepherd/config.toml` and edit the paths. Every setting is optional, and
flags override the file (`--config`, `--work-dir`, `--device`, `--elektroid-cli`).
`sample-shepherd config show` prints what's in effect.

## Quick start: sync a Digitakt II

```bash
sample-shepherd device ls                       # find its number (1 for the first device)
sample-shepherd device info                     # its filesystems; "sample" means sync works

# 1. Back up every project, one folder per slot (slow: dry run first for the estimate)
sample-shepherd projects backup --out backups/2026-11-07 --dry-run
sample-shepherd projects backup --out backups/2026-11-07

# 2. What do the projects use? (reads the backups, not the device)
sample-shepherd projects used --backups backups/2026-11-07 --out used.csv

# 3. What's on the device? (read-only)
sample-shepherd device listing --out listing.csv

# 4. Render your library for the device, and check it
sample-shepherd export render digitakt_2_50_3 --out renders/digitakt
sample-shepherd export check renders/digitakt --profile digitakt_2_50_3

# 5. Plan: upload what's missing; with --prune, delete what the export no longer has
sample-shepherd plan --listing listing.csv --used used.csv --export renders/digitakt \
    --folders 01_KICKS 02_SNARES --prune --out plan.csv
#    -> read plan.csv. Edit it if you like: remove a row and it won't happen.

# 6. Sync, resumably. Stop it any time; run the same command again to continue.
sample-shepherd sync --plan plan.csv --dry-run
sample-shepherd sync --plan plan.csv --used used.csv --yes
```

Transfers are slow (about 77 KB/s plus 1.6 s per file on a Digitakt II), so `plan` and
`sync --dry-run` print a time estimate. Set `[transfer]` in the config to your own speeds;
`sync` prints the measured speed as it goes.

## Commands

| Command | What it does | Writes / touches |
|---|---|---|
| `organize doctor` | Is Fourier installed and configured? | nothing |
| `organize build [--dry-run] [-- args]` | Runs `fourier build` | Fourier's outputs |
| `organize patches` | Lists our patches to Fourier | nothing |
| `organize install-fourier --dir D [--dry-run]` | Clones Fourier at the base commit, applies the patches, `uv sync` | `D` |
| `export profiles` | Lists device profiles | nothing |
| `export render PROFILE [--from M] [--out O] [--dry-run]` | Runs `fourier render` with our profiles | `O` |
| `export check RENDER --profile P` | Checks files per folder, folder depth, sample rate and bit depth | nothing |
| `device ls` / `device info` | Connected devices / a device's filesystems | reads the device |
| `device listing --out CSV [--dry-run]` | Lists the sample storage: `path,size,hash` | reads the device |
| `projects ls` | Lists project slots | reads the device |
| `projects backup [--out DIR] [--slots ...] [--dry-run]` | Downloads projects, one folder per slot, plus `backup-index.csv` with SHA-256s | reads the device; writes `DIR` |
| `projects used --backups DIR --out CSV` | Samples the backed-up projects use: `path,size,hash,projects` | `CSV` |
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
- Every row is in the CSV with its reason: `upload`, `delete`, `skip-exists`, `keep-used`,
  `keep-protected`, `skip-missing`.

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
examples/              an example config file
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
