# Research: Fourier Samples and Elektroid

What sample-shepherd depends on, under what terms, and what each Elektron device supports.
Read-only research, 2026-11-07. Sources: `github.com/bvk7787/fourier-samples` at `131ee62`
(still upstream `main`, v0.1.2) and `github.com/dagargo/elektroid` at `053d3fde`
(2026-11-03, `3.4-58`). No device was touched and nothing was filed upstream.

## Summary

- **Fourier Samples is Apache-2.0.** sample-shepherd can depend on it under any license.
  Elektroid is GPLv3, and that's fine too, as long as we only run `elektroid-cli` as a
  separate program and don't bundle or link it.
- **Fourier has no Python API to build on.** It's an alpha (0.1.x) CLI tool. Its extension
  points are config: `fourier.toml`, an overlay YAML of tunables, device profiles in
  `$FOURIER_DEVICES`, and an entry-point group (`fourier.preparers`) that only adds audio
  codecs. There's no plugin hook for curation rules, so a "plugin" isn't an option.
- **Recommendation:** treat Fourier as an external CLI that `sample-shepherd organize`
  runs as a subprocess. Find it by a `fourier` setting (path) or on `PATH`. Offer an
  optional extra (`sample-shepherd[organize]`, pinning `fourier-samples>=0.1.2,<0.2`) for
  stock installs. Don't vendor it.
- **Our config needs the patched Fourier.** Stock Fourier rejects our overlay (`unknown
  tunable 'FOLDER_ADAPTIVE'`, `layers.py:172`), and three-level folders come from patch 0004.
  So `organize` needs a documented "patched install": clone at `131ee62`, `git am
  config/patches/*.patch`, `uv sync`. All 8 patches still apply cleanly to upstream `main`
  (checked with `git am`).
- **Elektron sample sync is possible on Digitakt I/II, Rytm I/II and Model:Samples**
  (+Drive `sample` filesystem, project packages that list the samples they use). Syntakt has
  only a slot-based `data-sample` filesystem. Digitone I/II have no sample filesystem in
  Elektroid.

## 1. Fourier Samples

### License and terms

- `LICENSE`: Apache-2.0. `pyproject.toml`: `license = "Apache-2.0"`, with `NOTICE` and
  `THIRD_PARTY_NOTICES.md` as license files.
- Depending on it (pip, or running it) carries no obligations for us. If we ever
  redistribute Fourier itself (vendoring, an app bundle, a container image), we'd have to
  ship its LICENSE and NOTICE, mark our changes in modified files, and take on its
  dependencies' terms (LGPL soxr/libsndfile in `soundfile` wheels; with `[stretch]`, GPL
  Rubber Band as a separate process).
- `[clap]` downloads the `laion/clap-htsat-unfused` weights (Apache-2.0). The training
  dataset says research use only. That's Fourier's notice to carry, but our README should
  point to it, since `organize` asks for the CLAP model.
- On PyPI as `fourier-samples` (0.1.0, 0.1.1, 0.1.2, with provenance). Python >= 3.11.

### What we can program against

| Surface | Stable? | Use |
|---|---|---|
| CLI `fourier …` (`build`, `render`, `publish`, `verify`, `diff`, `sync`, `devices list/show/new`, `config show/explain`, `review …`, `tools …`) | Snapshot-tested (`tests/test_cli_tree.py`), but 0.x | **Primary interface.** Run it as a subprocess |
| `fourier.toml` (`$FOURIER_CONFIG`) | Documented in `docs/usage.md` | We generate or point at it |
| Overlay YAML (`overlay = …`, `advanced:` tunables) | Documented; an unknown key is an error | Library rules, size caps |
| Device profiles (`$FOURIER_DEVICES`, `extends:`) | Documented in `docs/device-profiles.md` | Our `digitakt_2_50*`, `generic_folder_3` |
| `$FOURIER_HOME`, `HF_HOME` | Documented | Keep Fourier writes in a user-chosen dir (what `fourier.env` does) |
| Entry points `fourier.preparers` | Documented | Codecs only. Not useful to us |
| `import fourier.*` internals | No API promise, alpha | Avoid. Our patches touch `packs/*` internals |

Note: Fourier has its own `render` (device profile → folder) and `sync` (M8 SD card only).
sample-shepherd's `export` layer can mostly wrap `fourier render <profile>` and add our
profiles. Our `sync` layer covers what Fourier doesn't: MIDI devices through Elektroid.

### How to depend on it

1. **Optional extra for stock users:** `pip install 'sample-shepherd[organize]'` pulls
   `fourier-samples>=0.1.2,<0.2`. `sample-shepherd` itself installs and runs `export`
   (from an existing master) and `sync` without it. `organize` checks for `fourier` and
   says how to install it.
2. **Patched install, documented and scripted:** a `sample-shepherd organize
   install-fourier --dir <path> [--dry-run]` (or a script) that clones upstream at the pinned
   base, applies `config/patches/` with `git am`, and runs `uv sync --extra clap` into
   `<path>/.venv`. Config then points `fourier = "<path>/.venv/bin/fourier"`. That's what
   `~/sample-work/vendor/fourier-samples` already is, made reproducible.
3. **Alternative (needs Jules's OK, since it publishes):** a public fork with the patches on
   a branch, installable as `fourier-samples @ git+https://github.com/<fork>@<tag>`. It's
   simpler for users, but it's a public artifact to maintain.

Not recommended: vendoring (the brief rules it out, and it's 0.x moving code), or
importing internals (the patches show how much is internal).

### Carrying the 8 patches

Keep them as `git format-patch` output in `config/patches/` (they already are), and add:

- `config/patches/README.md`: base repo and commit (`bvk7787/fourier-samples@131ee62`,
  v0.1.2), how to apply (`git am`), how to refresh (rebase `local/adaptive-folders` onto the
  new upstream, then `git format-patch -o config/patches <base>`), and one line per patch
  saying what it does, whether our config needs it, and its upstream status.
- A CI or pytest check (skipped when offline) that clones the base and runs `git am --check`
  on the series, so a bad edit is caught.

| Patch | What | Our config needs it? | Upstream fit |
|---|---|---|---|
| 0001–0003 | A vendor's `SD_` name prefix isn't "snare drum" | Changes classification | Generic. Good candidate. Test names (`SD_Falcon_Kick`, `SD_Kick_Alauda`, …) may be real pack sample names. CONTRIBUTING asks for invented names (Acme, Northwind), so rename them before offering |
| 0004 | Adaptive folder counts (`FOLDER_ADAPTIVE`) and a third folder level | **Yes:** overlay and `*_3` profiles | Largest (~1.7k lines, mostly the tunables snapshot). Needs an issue and the maintainer's go-ahead first |
| 0005–0008 | Group and naming refinements (tempo families, FX foley, phrase drum words, finer hats) | Changes output | Generic. Each needs the synthetic golden re-run (`tests/golden/synthetic_build.py --check`) |

Upstream process (CONTRIBUTING.md): open an issue and wait for a maintainer's go-ahead
before a PR. A PR needs tests, the golden re-run, the CLI snapshot for CLI changes, and a
class line in `config/tunables.yaml` for new tunables. Nothing gets filed without Jules's OK.

## 2. Elektroid and Elektron devices

### License

GPLv3 (`COPYING`). Running `elektroid-cli` as a separate process and parsing its output is
"aggregate" use. sample-shepherd keeps its own license. Don't bundle Elektroid binaries in a
sample-shepherd release without meeting GPLv3 (source offer, etc.). Better to make it a
documented prerequisite. Debian/Ubuntu package it, and Flathub has the GUI. On macOS it has
to be built from source.

**The configure.ac bug is still in upstream HEAD** (`053d3fde`, line 72):
`AM_COND_IF(ELEKTROID_BUILD_GUI, [], [PKG_CHECK_MODULES([GTK], [gtk+-3.0])])` needs GTK
exactly when the GUI is off. Our local fix swaps the branches. It's still unreported. Ask
Jules before filing.

### CLI commands (all devices)

Device commands: `ld`, `info N` (lists the device's filesystems: use this to detect what a
device supports, rather than hard-coding it), `df N:/` (+Drive and RAM size, used, free),
`send`, `receive`, `upgrade`, `play`, `record`.

Filesystem commands: `elektron:<fs>:<op>`, where op is `ls`, `mkdir`, `rmdir` (recursive),
`ul`, `dl`, `rdl`/`backup` (recursive download), `mv`, `rm`, `cl` (clear a slot), `cp`, `sw`
(swap). Not every filesystem implements every op (for example, samples can't be swapped).

- `sample:ls` lines are `type size cksum name`, for example `F 1.29MiB 0bbc22bd square`.
  Size is rounded and human-formatted (as our `drive_listing.py` found). The cksum is the
  32-bit hash the device keeps per file, printed in hex. A project manifest's `Hash` is
  decimal. The two matched for all 71 used samples on Jules's device, but I couldn't confirm
  the conversion in this repo's code. Compare them as integers, and add a unit test with a
  known pair.
- `data`/`project`/`sound`/`preset*` items are addressed by **slot index**, not name.
  `ls` gives `type index perms valid hasmeta size name`.
- Sample names are at most 32 characters (`ELEKTRON_NAME_MAX_LEN`). Syntakt `data-sample`
  slot names are at most 16.

### Per device (from `res/elektron/devices.json` and `src/connectors/elektron*.c`)

| Device (id) | Filesystems | Storage | Samples on upload | Project package lists samples? |
|---|---|---|---|---|
| Digitakt (12) | `sample`, `data`, `project` (.dtprj), `sound` (.dtsnd), `ram`, `track`, `track-loop` | +Drive, RAM | mono, 48 kHz, 16-bit | Yes, 127 slots |
| **Digitakt II** (42) | `sample`, `data`, `project` (.dt2prj, .dtprj), `preset-takt-ii` (.dt2pst, .dtsnd) | +Drive, RAM | **stereo kept stereo**, 48 kHz, 16-bit | Yes, 1023 slots |
| Analog Rytm (8) / MKII (16) | `sample`, `data`, `project` (.arprj), `sound` (.arsnd) | +Drive, RAM | mono, 48 kHz, 16-bit | Yes, 127 slots |
| Model:Samples (25) | `sample`, `data`, `project` (.msprj), `sound` (.mssnd) | +Drive, RAM | mono, 48 kHz, 16-bit | Yes, 127 slots |
| Syntakt (30) | `data`, `project` (.stprj), `sound` (.stsnd), `data-sample` | none listed | mono, 48 kHz, **5 s max**, slot-based | No |
| Digitone (20) / Keys (28) | `data`, `project` (.dnprj), `sound` (.dnsnd) | none | No sample filesystem | No |
| Digitone II (43) | `data`, `project` (.dn2prj, .dnprj), `preset-takt-ii` | none | **No sample filesystem in Elektroid yet** | No |

(Also supported but out of scope here: Analog Four/Keys, Analog Heat, Model:Cycles with
`raw`/`preset-raw` on +Drive, Monomachine, and MIDI SDS samplers through the `sds` connector.)

What this means for the device interface:

- **Full flow** (backup → used → plan → sync on the +Drive): Digitakt I/II, Rytm I/II,
  Model:Samples. Same `sample` operations everywhere. Differences are profile data: channel
  handling (only DT II keeps stereo, so mono-fold stereo files before upload on the others,
  or accept Elektroid folding them) and slot counts.
- **"Used samples" from project packages:** Elektroid builds the `Samples/…` manifest only
  for those five ids (`elektron_pkg.c:524`). On other devices, `projects used` has to say
  "not available" instead of reporting an empty list. An empty list would make every sample
  look deletable.
- **Syntakt:** a different model (numbered slots, 5 s cap, no folders). It fits a later
  "slot upload" mode, not the +Drive sync.
- **Digitone I/II:** backup of projects and sounds only. No sample sync until Elektroid adds
  it.
- Detect at runtime with `elektroid-cli info N` (filesystems line) and `df` (storage), and
  map the device name to a profile. Our tests can fake both outputs.

### Safety notes for the sync layer (from source and the brief)

- One process per device at a time. Add a lock file per device in the sync code.
- `rm`/`rmdir` on `sample` are immediate and recursive. `cl` on project slots wipes the slot.
  Neither has a confirmation in the CLI, so our `--yes` gate is the only guard.
- A project package download (`project:dl`) is the backup unit. Keep one folder per slot,
  since names can collide (as the three "NEW PROJECT" slots did).
