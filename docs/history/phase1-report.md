# Phase 1 report: test run on 4 packs

Date: 2026-10-26. The source library was only read. All output is under `~/sample-work/out`.
Detail: `phase1/summary.md`, plus `phase1/dropped.csv` (every left-out file
and its reasons), `phase1/picked.csv` (source → master path), `phase1/folders.csv` and
`phase1/digitakt-files.csv`. Full build log: `phase1-build-output.txt`.

## Settings

- Packs: Brad Brunazzi Vintage Drum Machines (201), WOST Club Drumz Vol. 1 (99), Lurka (100),
  Chord Marauders Geode (80). 480 audio files, all WAV (301 at 44.1/24, 99 at 48/24, 80 at 44.1/16).
- `preset = "balanced"`, `retune = "off"`. The other fixes stay on: `loudness = standard`,
  `stereo = fold-near-mono`, tidy names, DC/phase/click fixes.
- Devices: `digitakt_2_50`, our own profile: `config/devices/digitakt_2_50.yaml`, which extends
  `digitakt_2` with `files_per_folder: 50`. Also `generic_folder`.
- Fourier also read Live's file index read-only, and matched Live auto-tags for 477 of the 480 files.

## Timings

| Step | Time |
|---|---|
| `fourier build` (scan, librosa, CLAP on the GPU, curate, verify) | 62 s |
| `render generic_folder` / `render digitakt_2_50` | 6 s each |

For scale: analysis ran at about 12 files/s. The full `sample packs` (44.4k files) is roughly
**1–1.5 h** for the first build. I'll get Fourier's own estimate with `build --dry-run` before Phase 2.

## Result

**239 of 480 source files are in the master. 247 files are in each render**, counting 8
slice-ready loops in `00_SLICE`. Verify: **PASS**, 120 checks, 1 warning (SUB, FX and VOX have
fewer candidates than their budgets, which is normal for a small library).

| Category | Files | | Category | Files |
|---|---:|---|---|---:|
| KICKS | 26 | | FX | 16 |
| SNARES | 33 | | VOX | 4 |
| CLAPS | 12 | | SUB | 13 |
| HATS | 28 | | SYNTH | 5 |
| CYMBALS | 10 | | STABS | 5 |
| TOMS | 25 | | PADS | 6 |
| PERC | 24 | | DRUMLOOPS | 20 (4 tempo folders) |
| ACOUSTIC | 2 | | PHRASES | 10 |

Empty: BLIPS, PIANO, WAVES (these packs have nothing for them). No drum kits were built,
because these packs give too few kit-able one-shots per pack.

### Folders

31 folders per output. The largest is `02_SNARES/snare` with 33 files. **No folder is over 50.**
With so few files per category, each category holds one family, so the 50-file split isn't
exercised yet. It will be in Phase 2.

### Why 241 files were left out (a file can have more than one reason)

| Reason | Files | Comment |
|---|---:|---|
| over budget | 113 | A small library gets small budgets ("scale = library"). Expected, and it relaxes at full size. |
| recognized, but no category took it | 24 | **Routing problem**: 24 Brad Brunazzi `Custom One Shots/.../SD_*.wav` files (Fourier's labels: 23 kick, 1 tom). Fourier reads the `SD_` prefix as "snare drum", so the file is both kick and snare, and neither category takes it. |
| per-vendor cap | 22 | No vendor may supply more than 40% of a category. |
| clipped ("hygiene") | 20 | **17 WOST, 3 Lurka kicks and snares.** Loud modern club drums with intentional clipping. Fourier's clipping gate isn't a setting; the threshold is in its code. |
| mostly silent / too long / too many onsets / loop gates | ~40 | e.g. Geode "stabs" over 4 s, reverb tails, bass loops over 8 s for SUB |
| near-duplicate / sibling cap | 15 | |
| no name rule recognized it | 5 | 2 Geode "Music Sequences", the Geode "01 Sampler" demo, `WOST_FX_2`, `WOST_MISC_2` |

## Digitakt II loadability (`out/renders/digitakt_2_50`)

- **All 247 files are 48 kHz / 16-bit WAV, mono or stereo, and all are under 66 s.** Nothing the
  Digitakt II would reject. There are no source files in unsupported formats, sample rates or
  bit depths, because Fourier converts everything.
- Size: **97.4 MB** on disk. Loading all of it into one project would use about 26% of the
  400 MB project sample RAM and 247 of the 1016 slots.
- Unverified: the Digitakt II's maximum name length. The profile leaves it unchecked. The longest
  name here is short (Fourier tidies names), and Phase 2 will report the longest.

## For you to audition

- Ableton / XO: **`~/sample-work/out/renders/generic_folder`** (44.1 kHz / 24-bit). In Live,
  add it to Places, or drag it into the browser. XO can scan it as a folder.
- A listening page that also shows why each file is there and lets you rate it Keep / Drop / Misfiled:
  ```bash
  . ~/sample-work/fourier.env && fourier open report
  ```
  Ratings are stored in `~/sample-work/fourier-home` and apply from the next build on.
- `fourier why "<name>"` tells you where a file went, or why it was left out.

## The `SD_` routing fix: findings (2026-10-26)

- **Cause:** Fourier's snare rule (`DRUM_NAME_RULES`, `src/fourier/packs/curate_config.py:1130`)
  treats `sd` before `_` as "snare drum". `SD_Falcon_Kick` then names two drums, so the name decides
  nothing. A vote, KICKS 2 to SNARES 1, still left it unplaced. The pack-prefix exception
  (`_DRUM_PREFIX_RE`, `rules.py:588`) only covers codes like `sd_qz030`.
- **Scope in the test set:** 30 misrouted files. 24 were placed nowhere (23 kicks, 1 tom), and
  6 hats and toms were filed in SNARES. A further 76 `SD_` files were left out by budget or gates,
  which is normal.
- **Scope in the full library:** 3,743 audio files open with a drum abbreviation and `_`, and
  1,186 of them are `SD_` + another drum word. The `SD_` is a **vendor prefix** in every pack I
  checked: seven 2024 `SD_*` packs (Seismic 2, AURORA, SATIN, CAICOS...), Vintage Drum Machines
  808/909 (`909 Kicks/SD_Kick_Alauda.wav`) and Slate 808. Not one of them uses it to mean "snare".
- **An overlay can't fix it.** Overriding `DRUM_NAME_RULES` from YAML turns each rule's category
  into a regex (`'KICKS'` becomes `re.compile('KICKS')`; `layers.from_plain` coerces every tuple
  item to the first item's type). That would break routing. This looks like an upstream bug.
- **Ratings only half-fix it.** `fourier review rate ... misfiled` only applies to files already in
  the master: an import dry run matched 6 of 30 rows. `scripts/folder_ratings.py` wrote those rows to
  `config/ratings/brad-brunazzi-sd.csv`, which is **not imported**. Ratings are unchanged; a backup is in
  `tmp/ratings.before.json`.

## Phase 1b: rebuild with the `SD_` fix (2026-10-26)

You chose a local patch, since an overlay can't do it. Fourier is on local branch
`local/sd-vendor-prefix` (3 commits on `131ee62`). The patches are also saved in `config/patches/`.

**What the patch changes** (`src/fourier/packs/rules.py`, `curate_config.py`):

1. `_drum_named`: `SD_` followed by a letter opens a vendor prefix. If the rest of the name names
   one drum, that drum wins (`SD_Falcon_Kick` → KICKS, `SD_DMX_Tom_1` → TOMS). `SD_01`, `SD 3` and
   `909 SD` still mean snare.
2. `_drum_named_in`: if the rest of an `SD_` name names no drum, a folder that names one decides
   (`Hi Hats/SD_OberHat_Open` → HATS). A drum word in the name still beats the folder
   (`Cymbals & Percussion/SD_LINDRUM_Clap` stays in CLAPS).
3. KICKS's name filter (`noise`) dropped every name starting with `sd_` before selection, without
   logging a reason. So the kicks never reached the pool even once routing named them kicks. It now
   lets `SD_` + a word through and still blocks `SD_01`, `SD 3` and `sd-...`.

**Tests:** 20 new cases in `tests/test_routing_signals.py`. The default-settings snapshot was updated
for the KICKS filter. Full suite: **2048 passed, 15 skipped**, up from 2028 passed before the patch.

**Result** (full detail in `phase1b/summary.md`, build log
`phase1b-build-output.txt`):

| | Phase 1 | Phase 1b |
|---|---:|---:|
| Files in the master (from source) | 239 | 242 |
| `SD_` files placed nowhere by routing | 24 | **0** |
| KICKS candidates / picked | 43 / 26 | 59 / 28 |
| SNARES | 33 | 31 |
| TOMS | 25 | 26 |
| CYMBALS | 10 | 12 |
| `SD_` hats/toms/percussion in SNARES | 8 | **2** (see below) |
| Clipped files dropped ("hygiene") | 20 | 20 (as you asked) |
| Verify | PASS 120/1 warn | PASS 121/1 warn |
| Renders | 247 files | 250 files, 134.4 MB generic / 97.5 MB Digitakt |

The `SD_` kicks are now real candidates. Only 2 more made it in (`SD_Choji_Kick_(Wet)`,
`SD_LINDRUM_Kick_2`), and the others are left out as `over_budget` (14) or `vendor_capped` (8). That
is normal at this library size: budgets scale with the library, and Brad Brunazzi already supplies
40% of KICKS. At the full size the budgets are much larger.

Changes in the Digitakt render: `+` 2 kicks, 3 snares (`SD_Senju_Snare`,
`SD_LINDRUM_Weird_Snare_Sweep_Down`, 2 Lurka snares that were displaced before), 1 tom, and
cabasa/tambourine in CYMBALS. `−` 6 hats, toms and congas from `02_SNARES`. No folder is over 50.
Every file is 48 kHz/16-bit.

**Still wrong:**
- **2 files:** `Hi Hats/Wet/SD_OberHat_Loose_(Wet)` and `SD_OberHat_Open_(Wet)` are in SNARES. The
  nearest folder is `Wet`, which names no drum, and Fourier's hat rule doesn't read camelCase
  `OberHat`; it does for `Kick`, `Snare` and `Cymb`. Adding camelCase `Hat` would be a fourth
  change to the drum rules. I haven't made it.
- `SD_LINDRUM_Cabasa_1` and `SD_LINDRUM_Tamb_1` go to CYMBALS because their folder is
  "Cymbals & Percussion". Before the patch the cabasa was in SNARES, and the tambourine wasn't
  picked.

`config/ratings/brad-brunazzi-sd.csv` is no longer needed and was never imported.

## Decisions before Phase 2

1. ~~`SD_` kicks~~: fixed by the local patch (Phase 1b). Optional: the camelCase `Hat` rule for
   the 2 `OberHat (Wet)` files.
2. **Clipped WOST drums:** dropped, as Fourier does (your call, 2026-10-26).
3. Anything that sounds wrong, or in the wrong category, when you audition `out/renders/generic_folder` again.
