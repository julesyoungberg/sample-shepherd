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
file. [Configuration](docs/cli/configuration.md) lists every setting.

## Using it

The short version, once you've installed and configured it:

```bash
sample-shepherd organize build                                    # curate your packs (Fourier)
sample-shepherd export render digitakt_2_50_4 --out renders/dt    # render for a device
sample-shepherd projects backup --out backups/today               # back up the device's projects
sample-shepherd projects used --backups backups/today --out used.csv
sample-shepherd device listing --out listing.csv
sample-shepherd plan --listing listing.csv --used used.csv --export renders/dt --out plan.csv
sample-shepherd sync --plan plan.csv --used used.csv --dry-run    # then without --dry-run
```

The [documentation](docs/README.md) covers it properly:

- [Getting started](docs/cli/getting-started.md): the whole path, step by step.
- [Configuration](docs/cli/configuration.md): every setting and where the file lives.
- [Commands](docs/cli/commands.md): what each command reads and writes, how `plan` decides,
  and the safety checks.
- [Command reference](docs/cli/reference.md): every flag, generated from the code.

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
- `digitakt_2_50_4`, `generic_folder_4`: four levels, with section folders on top:
  `SECTION/CATEGORY/group/family`, sections `DRUMS`, `LOOPS`, `TONAL`, `VOX`, `FX`
  (patch 0009). Fewer, bigger folders at a device's root, next to your own folders.

Fourier's own profiles (`digitakt_2`, `generic_folder`, `m8`, ...) work too. To write your
own, see [docs/adding-a-profile.md](docs/adding-a-profile.md).

## Fourier and our patches

Fourier is an external command here, found through `[fourier] command` or `PATH`, with the
environment from `[fourier] env`. Our 9 patches to it live in
[config/patches](config/patches); [docs/fourier-patches.md](docs/fourier-patches.md) says
what each does, whether our config needs it, and how it could go upstream.

## Evaluating the sorting

`sample-shepherd eval categories` measures how well samples land in the right category, against
a hand-labeled set (paths only, no audio), with simple baselines (majority, file-name keywords,
folder names, hand-written rules) to compare Fourier against. The bundled seed set is a regression
suite, not yet an accuracy estimate: nobody has listened to it. See
[docs/evaluation.md](docs/evaluation.md) for the metrics and how to grow a real test set from
your ratings or a random sample.

## Repository layout

```
src/sample_shepherd/   the package: cli.py, config.py, organize/, export/, sync/, evaluate/
eval/labels/           hand-labeled categories for `eval` (paths only)
tests/                 pytest; tests/fake/elektroid-cli stands in for a device
config/                Fourier config, device profiles, patches, curation decisions
examples/              starter configs for sample-shepherd and Fourier
docs/                  user guides (start at docs/README.md) and how-tos; docs/history/ has notes from the first build
scripts/               the original one-off scripts (still in use; see below)
```

`scripts/` holds the scripts the first library build used: listing, upload, guarded delete,
source matching and reports. They're kept where they are and working, because a working
tree runs them by path. The package replaces the device parts (`drive_listing.py`,
`upload_tree.py`, `delete_replaced.py`) with `device listing`, `plan` and `sync`; the
source-library matching (`drive_match.py`, `delete_list.py`) and reports read Fourier's
database and stay scripts for now. Its output can feed `plan --replace`.

## What's next

See the [roadmap](docs/roadmap.md).
