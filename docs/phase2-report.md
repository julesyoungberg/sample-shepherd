# Phase 2 report: full build of `sample packs` (2026-10-26/27)

The source library was only read. Everything is under `~/sample-work/out/full/`. Nothing was
published or released, no device paths are locked, and the Digitakt II was not connected.

**Short version:** the full build is done. It has 10,830 files in 317 subfolders, none over 50
files, and every Digitakt file is 48 kHz/16-bit. That's 5.7 GB on the Digitakt and 7.9 GB for
Ableton/XO. **Verify failed 5 of 126 checks**, so Fourier kept the new master aside
(`out/full/master.next`) instead of putting it in place. Three of the failures need a listening
decision from you, one is caused by our folder settings, and one is a folder-naming check.
Previews of the held-back build are rendered for you to browse.

Detail: [phase2/summary.md](phase2/summary.md) (categories, why files were left out, Digitakt checks),
[phase2/structure.md](phase2/structure.md) (every subfolder and its file count). Also CSVs in
`phase2/` (`picked`, `dropped`, `folders`, `digitakt-files`, `structure`), and the logs
`phase2-build-output.txt`, `phase2-analyze-output.txt`, `phase2-build-time.txt` and
`phase2-render-*.txt`.

## Settings

- Library: the 4 year folders of `sample packs` (`2024`, `2025`, `2026`, `old`) as separate
  entries, so each pack folder is a vendor for the 40% cap. `Sounds` isn't included.
- `preset = "balanced"`, `retune = "off"`, Fourier's other fixes on, **`scale = "off"`** (the full
  `balanced` budgets, about 10,500 files).
- `config/overlay.yaml`: `MAX_PER_FAMILY: 50`, `FOLDER_MAX: 24`, `FOLDER_MIN_FILES: 6`.
  `fourier config explain` confirms each one is active.
- The Fourier checkout is the local `SD_` patch (branch `local/sd-vendor-prefix`).
- Outputs: `out/full/master` (empty: verify kept the build out), `out/full/master.next` (the build),
  `out/full/preview/{digitakt_2_50,generic_folder}` (renders of `master.next`, preview only).
  Phase 1's outputs in `out/` are untouched. Fourier refused to overwrite them with a different
  library, which is why the full build got its own folder.

## Timings and disk

| Step | Time |
|---|---|
| Scan (44,392 audio files; about 8,000 non-audio files such as `.asd` and presets skipped) | ~5 min |
| Audio features, 1 thread (31,412 files) | 83 min |
| CLAP fingerprints on the GPU (43,912 files) | 13 min |
| Quality, loop trims, root notes, keys, sound model, 1 thread | 56 min |
| Build: curate, process, verify (`-j 6`) | 12 min |
| Each preview render | 25 s |

That's about 3 h 15 min from start to finish, including two crashes (below).
**Disk: 24 GB in `~/sample-work`**, about 950 GB still free.

**Crash, and what I did:** analysis was killed twice by a bus error (SIGBUS) inside libsndfile's
MP3 decoder (`mpeg_init`). The macOS crash report shows it on one of Fourier's analysis threads.
Each of the 655 MP3s opens fine on its own, so it's most likely two threads opening MP3s at the
same time. Nothing was lost, because Fourier saves its analysis in batches. I re-ran the threaded
steps on 1 thread, which is slower but safe. This is a bug in the audio library, not in Fourier's
logic. A future fix would be one lock around MP3 decoding.

**Unreadable source files** (left out, not changed):
- 2 corrupt WAVs: `old/Breaks/Breaks/Black_Blood_-_A.I.E.wav` and `Black_Heat_-_Love_The_Life_You_Live.wav`.
- 4 acapella MP3s in `2024/Acapellas/` that libsndfile can't decode: Jamiroquai, 50 Cent,
  Brandy & Monica, Usher.

## Result

10,086 of 44,392 source files are in the master. With 206 kit files and 538 slice-ready loops,
the render has 10,830 files.

| Category | Files | Subfolders | Digitakt MB | | Category | Files | Subfolders | Digitakt MB |
|---|---:|---:|---:|---|---|---:|---:|---:|
| KICKS | 853 | 24 | 49 | | SUB | 814 | 19 | 184 |
| SNARES | 775 | 23 | 50 | | SYNTH | 558 | 16 | 228 |
| CLAPS | 466 | 12 | 20 | | STABS | 199 | 6 | 50 |
| HATS | 775 | 23 | 36 | | PADS | 647 | 16 | 779 |
| CYMBALS | 220 | 6 | 46 | | PIANO | 124 | 3 | 97 |
| TOMS | 198 | 5 | 14 | | ACOUSTIC | 244 | 8 | 214 |
| PERC | 773 | 20 | 47 | | FX | 852 | 24 | 417 |
| DRUMLOOPS | 1,383 | 28 | 1,770 | | BLIPS | 98 | 3 | 8 |
| PHRASES | 477 | 11 | 914 | | VOX | 630 | 18 | 250 |
| KITS (sets) | 206 | 24 | 15 | | SLICE (sets) | 538 | 28 | 559 |

WAVES is empty: nothing in the library matches it.

**Why the other 34,306 files were left out** (a file can have several reasons; full list in `phase2/dropped.csv`):
- **over budget (19,179):** the categories were full, especially FX, which had 12,443 candidates.
- **filters:** sound and loop checks (3,150 + 1,224 + 730 + ...), too many onsets (2,241),
  too long (1,259), clipped (1,049, as you chose).
- **duplicates:** sibling caps (2,376), byte-identical twins (969), near-duplicates (440).
- **not recognised: 705 files.** Their names and folders hold no word Fourier knows. The biggest
  groups are `3990_Vimana-Full/VIMANA_PART_6` (123), **`2024/Acapellas` (119)**,
  `4899_Metaphor-Full` (41) and `Horror SFX Complete/Ambient` (29). Fourier doesn't know the word
  "acapella". A `words = { VOX = ["acapella", "acapellas"] }` line in `fourier.toml` would fix that.
  I haven't added it, since it changes the picks.

## Folder structure (the thing to review)

All 317 subfolders hold **50 files or fewer**. The median is 33–50, depending on the category.
There's no numbered overflow from the 50-file cap. The `-2`, `-3` you'll see in `04_HATS/closed-clicky-2`
and `19_VOX/short-2` come from Fourier's naming: two sound groups that came out with the same
description.

Where the groups are logical (they lead with a type word):
- **HATS:** `closed-…` / `open-…`
- **DRUMLOOPS:** by tempo (`120-125bpm`, `160-165bpm-jungle-breakbeat`, `…-tops-hi-hat`, `classic-breaks`)
- **FX:** `foley-…`, `impact-…`, `riser-…`, `noise-glitch-…`, `sweep-…`, `whoosh-…`
- **SUB:** `808-sub`, `wobble`, `detuned`, `fm-plucky`, `pure-sine-sub`
- **PADS:** `cinematic-swell`, `granular-texture`, `fifths`, `warm-analog`
- **ACOUSTIC:** `plucked-harp`, `string-violin`, `wind-flute`
- **VOX:** `hey-shout`, `vocal-ad-lib`, `pitched-vocal-stab`

**Where they're weak: KICKS and SNARES.** Most of their 24 and 23 subfolders are combinations of
sound traits (`clicky-gated-punchy`, `tonal-snappy-long-tail`, …), with only a few anchors like
`808-tonal-long-tail`, `vintage-drum-machine-*`, `breakbeat-*` and `lo-fi-dusty`. They're
accurate descriptions, but hard to browse, because neighbouring folders sound alike. If you want a
third level, this is where it would help most: e.g. `01_KICKS/808/…`, `01_KICKS/vintage/…`,
`03_HATS/closed/…`, `17_FX/impact/…`, `08_DRUMLOOPS/120-125bpm/…`. Many folder names already
start with the word that would become that parent folder.

## Verify: the 5 failures

| Check | What failed | Cause | Options |
|---|---|---|---|
| allocation follows cluster size | DRUMLOOPS (24 of 28 folders at 50), FX (13 of 24), PHRASES (9 of 11) | **Our overlay.** The 50-file ceiling plus these categories' folder limits mean most folders are full. Spare budget from small categories also flows here. | (a) give FX more folders (`FOLDER_MAX` 32); (b) lower these categories' weights (`categories = { DRUMLOOPS = 0.8, PHRASES = 0.7 }`); (c) accept it (the folders are fine to browse; the check is Fourier's design rule). PHRASES' folder count is fixed in Fourier's code, so only (b) or (c) clears PHRASES. |
| loops are whole beats at their tempo | 15 loops about 0.12–0.14 beats off (40–120 ms) | Tempo or length doesn't fit, e.g. `Aluminum20a`, `ScrewsOnWoodTabletop65` (foley, not loops), and a few Evelyn and Impressions breaks | Listen to them: Drop or Misfiled each one (`fourier review rate <file> drop`). The full list is in `phase2-build-output.txt` under "loops are whole beats". |
| one-shots end quietly | `17_FX/noise-glitch-stutter-gated/Sample_0079.wav` (ends at -33 dB) | the file ends with a click | Drop it, or accept it |
| stereo only where it's real | `04_HATS/closed-clicky-squashed/GS_STRTS_Hat_18.wav` | almost mono, but kept stereo | Drop it, or accept it |
| tonal folders use tonal words | `10_SUB/punchy-plucky` (18 files) | a naming rule; a SUB folder shouldn't use drum words like "punchy" | Accept it, or tweak the naming rules (more work) |

There are also 5 warnings (no action needed): categories with fewer candidates than their budgets,
small categories with more folders than Fourier's 45-files-a-folder norm (expected with our
overlay), 111 pairs of near-identical folder names, 63 stereo files partly out of phase, and one VOX file 4.3 dB quieter than its folder.

**I didn't change anything to make verify pass.** Ratings are your listening call, and forcing
`master.next` into place would skip Fourier's safety check.

## Digitakt II fit

- **All 10,830 files are 48 kHz/16-bit WAV, mono or stereo, under 66 s.** Transfer won't need to
  convert anything.
- 5.7 GB for the whole library, within the profile's 10 GB share of the 20 GB +Drive (manual
  p.29). Whether it fits beside what's already on your +Drive depends on the free space we capture
  in device session 1.
- One project holds 400 MB of samples (p.17). The drum categories together are about 280 MB.
- **Unverified:** the device's maximum name or path length (the profile has no limit, so
  `render --check` can't test it). Measured in the render: the longest folder name is 38
  characters, the longest file name 52, and the longest path 101. Fourier cuts long file names
  in the middle with `~`. Check on the device how much of a name it shows.
- **Unverified:** non-ASCII characters. 19 file paths contain characters like `—` or `’`. The
  profile doesn't ask for ASCII-only names. Check that Transfer and the device show them; if not,
  setting `ascii_names: true` in our device profile would spell them out.

## Upload order (for device session 2, from a `v1` release, never from this preview)

Drums first, smallest and most-used:

| # | Folders | MB | Running total |
|---|---|---:|---:|
| 1 | `01_KICKS` | 49 | 49 |
| 2 | `02_SNARES` | 50 | 99 |
| 3 | `04_HATS` | 36 | 135 |
| 4 | `03_CLAPS`, `07_PERC`, `06_TOMS`, `05_CYMBALS` | 127 | 262 |
| 5 | `00_KITS` (ready-made kits that use the drums above) | 15 | 277 |
| 6 | `10_SUB`, `12_STABS`, `11_SYNTH`, `18_BLIPS` | 470 | 747 |
| 7 | `19_VOX`, `17_FX` | 667 | 1,414 |
| 8 | `08_DRUMLOOPS`, `00_SLICE` | 2,329 | 3,743 |
| 9 | `09_PHRASES`, `13_PADS`, `14_PIANO`, `15_ACOUSTIC` | 2,004 | 5,747 |

You can stop after any step and still have a complete set of categories so far.

## Next steps

1. **You: browse the structure.** In Live, add `~/sample-work/out/full/preview/generic_folder` to
   Places, or point XO at it. Decide:
   - **(a)** whether two levels are logical enough, or you want the third level, mainly for KICKS and SNARES;
   - **(b)** how to handle each verify failure (table above);
   - **(c)** whether to add `acapella` as a VOX word.
2. **Me, after your answers:** apply them (overlay or ratings), rebuild (about 12 min now that
   analysis is cached), and repeat until verify passes and you're happy with it.
3. **Then:** `fourier publish`, then `fourier render digitakt_2_50 --release v1`. That's the step
   that locks device paths, so it needs your explicit go-ahead.
4. **Device session 1:** follow [device-session-1-checklist.md](device-session-1-checklist.md):
   back up, then capture the +Drive listing, free space and project sample lists.
5. **Phase 3:** run `scripts/project_coverage.py` and `scripts/delete_list.py` on that data. Both
   are written and self-tested on made-up input (`tmp/phase3-selftest/`); neither has been run on
   real data.
6. **Device session 2:** upload v1 in the order above, then verify file counts and sizes against
   the manifest.
