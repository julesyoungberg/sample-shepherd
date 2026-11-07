# Phase 0 report: setup and inspection

Date: 2026-10-25. Everything below was read-only on the Ableton User Library.

## Machine

- Apple M5 Pro (arm64), macOS 26.6.2. PyTorch can use the GPU (MPS available: True).
- Free disk space: 961 GiB of 1.8 TiB. Fourier's reported ~25 GB for a large library is not a constraint.
- Tools found: uv 0.13.1, Python 3.13 and 3.14 (Homebrew), git, node. No ffmpeg or sox, and Fourier doesn't need either.

## Source 1: `Samples/sample packs` (primary)

| | |
|---|---|
| Size | 67 GB |
| Files | 56,075 total, of which 44,396 are audio (42,583 wav, 656 mp3, 509 flac, 473 aif, 175 aiff) |
| Non-audio | 9,696 `.asd` (Live analysis files), plus presets/instruments (vital, exs, nki, fxp, sxt, sfz, adg, rx2, mid, als...). Fourier ignores these. |
| Layout | Four year folders (`2024` 173 packs / 42 GB, `2025` 15 / 1.7 GB, `2026` 10 / 2.0 GB, `old` 80 / 21 GB), then packs. 1,110 folders hold audio. Max depth 11. |
| Flat hot spots | 777 files in one folder (`2024/4899_Metaphor-Full/.../Silverware_In_Hands`), and 14 more folders with 300–400 files |
| Archives | 15 `.zip`/`.rar` files inside packs (e.g. `2024/19769453869SKII_Drums.zip`, 11 in the 2026 Reggae pack). Fourier doesn't open archives, so their contents are out of scope unless you unpack them yourself. |
| Empty packs | Some pack folders have no audio: preset-only packs, plus a few that are 0 B (`old/SD_SATIN_SamplePack`, three `2025/Cymatics - QUAKE` folders). Check whether those downloads failed. |

Full per-pack counts: `reports/packs-by-count.txt`.

## Source 2: `Samples/Sounds` (undecided)

There's no `Sounds` folder at the top of the User Library. It's at `User Library/Samples/Sounds`.

- **It's almost all audio, not presets:** 12 GB, 43,263 files, of which 22,443 are audio (20,401 wav, 1,646 aif, 302 mp3, 48 aiff, 43 flac, 3 m4a). Also 20,503 `.asd`, 182 `.alc` (Live clips), 65 sfz, 35 nki. There are **no** `.adg`/`.adv` device presets.
- It's organized **by sound type**, not by pack:

| Folder | Audio files | Size |
|---|---:|---:|
| 8-bit | 10,401 | 1.4 GB |
| Drums | 6,318 | 2.6 GB |
| Drums-pack | 1,342 | 245 MB |
| Orchestra | 1,283 | 612 MB |
| FX | 971 | 1.3 GB |
| Strings | 681 | 1.0 GB |
| Synths | 680 | 367 MB |
| Sounds To Fuck With | 461 | 737 MB |
| Bass | 404 | 310 MB |
| SoundScapes | 282 | 2.6 GB |
| Keys / Pads / Dubspot / Mallets / Wind / others | ~800 | ~1.3 GB |
| (loose files at top level) | 166 | |

**Recommendation: include it, but not yet, and not all of it.**
1. Leave it out of the Phase 1 test.
2. For Phase 2, add it as **its own library entry, listing its subfolders and leaving out `8-bit`** for now. Fourier's per-vendor cap (no vendor may supply more than 40% of a category) only works for pack-style folders. A folder organized by sound type has no vendor, so nothing is capped, and 10,401 8-bit one-shots could swamp BLIPS/SYNTH. We can add `8-bit` later as an additive build.
3. Decide now whether `Sounds` counts as a "source directory" for the +Drive deletion policy. If it does, +Drive copies from `Sounds` that have equivalents in the new library become deletion candidates. If it doesn't, they're always KEEP-UNMATCHED.

## Not in scope, but relevant to Phase 3

`Samples/` also holds `!!!SOUNDS!!!!`, `!!!LOOPS!!!`, `LOOPMASTERS`, `Reverb Drum Machines | The Complete Collection`, `the drum club - kit 004 THE MEGA BUNDLE`, `SMPLZ`, `Imported`, `Processed`, `Recorded` and more. I didn't inspect them. Any +Drive sample that came from these is never a deletion candidate, under your policy.

## Fourier: install and status

- Cloned `https://github.com/bvk7787/fourier-samples` into `vendor/fourier-samples`, **pinned at `131ee62` (main, 2026-10-23)**. The package version is 0.1.2.
- Installed with `uv sync --frozen --python 3.13 --extra dev --extra clap` into `vendor/fourier-samples/.venv`. That's project-local: nothing system-wide, no Homebrew changes. Takes 12 s. torch 2.14.0, transformers 5.10.1.
- **Tests: 2028 passed, 15 skipped** (3 min 8 s, `pytest -n auto`). The golden end-to-end harness passed too (14 tests). The skips need things we don't have: the device-manual PDFs (`FOURIER_MANUALS_DIR`, which checks each device-profile citation against its manual page), Windows, CAF support.
- **Smoke test:** `fourier demo` built and verified a 271-file master from 280 synthetic samples, then rendered `digitakt_2` and `m8_tracker`, in 40 s. Nothing was written outside `~/sample-work`. I confirmed `~/.fourier`, `~/.config/fourier` and `~/Music/Fourier*` don't exist.
- The CLAP model (~600 MB, from Hugging Face) is **not downloaded yet**. The first real build or `fourier setup` fetches it into `~/sample-work/cache/huggingface`.

### Maintenance status: treat it as very young, alpha software

- The first commit is 2026-10-21. There are 100 commits in 3 days, all by one author. The status badge says alpha, and PyPI (0.1.2) lags main.
- On the plus side: CI on Linux and macOS for Python 3.11–3.14, mypy, OpenSSF scorecard, broad tests, careful safety design (it refuses to overwrite files it didn't make, keeps `.prev` for undo, writes atomically through `.next`). It was tested on hardware: a Digitakt 2 on OS 1.16.
- Risk: behavior and file formats (locks, manifest) may change quickly. **We stay on the pinned commit for the whole project** and upgrade only on purpose, after reading CHANGELOG, never between `publish v1` and a later release.

## Gotchas found (each affects a decision)

1. **Default write locations are outside `~/sample-work`** (`~/.fourier`, `~/.config/fourier`, `~/Music/FourierCurated`, `~/Music/FourierRenders`, `~/Music/Fourier/releases`, `~/.cache/huggingface`). `fourier.env` plus the Phase 1 config redirect all of them.
2. **The master is a curated subset, not the whole library.** A large library gets about 8,000–11,500 sounds depending on the style. Most of your 44k files won't be in it. For Phase 3, most old +Drive samples will have no equivalent and will come out KEEP-UNMATCHED.
3. **Fourier edits the audio it exports** (DC offset, phase-flipped stereo, end clicks, retuning a few cents, loudness, cleaned names). The Digitakt render is also converted to 48 kHz/16-bit. So rendered files never byte-match their sources. Settings can switch most of this off (`retune = "off"`, `loudness = "gentle"`, `stereo = "keep"`, `names = "keep"`).
4. **Hash matching against the +Drive will rarely work as specified.** Elektron Transfer converts everything to 16-bit/48 kHz when it uploads (the Digitakt II manual p.73, as quoted in Fourier's profile), so +Drive copies don't byte-match source files either. Workable plan: match on source content hash ↔ manifest `src` for the new side. For the +Drive side, match on name + expected size. A 48 kHz/16-bit WAV's size follows from the source's duration and channel count, so it can be predicted. Duration is the fallback. Whether elk-herd exports sizes or hashes is **unverified**. We'll check that in your first device session.
5. **Digitakt profile allows 128 files per folder**, which Fourier labels a convention, with no documented device cap. Fourier spills overflow into numbered sibling folders (`punchy`, `punchy-2`). To get ≤50, I'd add our own profile (`extends: digitakt_2`, `files_per_folder: 50`) in `config/devices`. **This must be set before `publish v1` + `render --release v1`**, because released device paths are locked from then on.
6. **Device locks key on each source's absolute path.** Don't move or rename the Ableton User Library or the pack folders after v1. Fourier can follow some moves, but don't rely on it.
7. **Layout detection.** With `library = ".../sample packs"`, the year folders could be read as "vendors", putting a whole year under one 40% cap. Plan: list the four year folders as four separate library entries, so each pack is detected as its own vendor. Confirm with `fourier doctor` in Phase 1.
8. **Fourier reads Live's and Sononym's databases** (read-only) for auto-tags if it finds them. That isn't an official API. It writes Live rating sidecars only inside the master.
9. **Evidence on the "move keeps project links" claim:** Fourier's profile cites Digitakt II manual p.29 as saying the device follows renames, while a deleted sample drops out of presets. That supports the forum claim, but it's still unverified until I read p.29 myself and we test it on a throwaway project.
10. Archives (`.zip`/`.rar`) and the 3 `.m4a` files aren't read.

## Proposed Phase 1 test subset (480 audio files, ~317 MB, 4 packs)

| Pack | Audio files | Why |
|---|---:|---|
| `old/Brad Brunazzi Vintage Drum Machines` | 201 | classic drum-machine one-shots |
| `2025/WOST - CLUB DRUMZ VOL. 1 (sample pack)` | 99 | modern club drums and loops |
| `old/Lurka - Lurka Sample Pack` | 100 | mixed bass, FX and percussion |
| `2024/Chord Marauders - Geode - U.D. Sample Pack` | 80 | melodic and chords, to exercise SYNTH/STABS/PADS |
