# Phase 2b results: keep more files, three folder levels

Report files named here (summaries, CSVs, build logs) are relative to `~/sample-work/reports/` and were never committed.

Plan: [phase2b-plan.md](phase2b-plan.md). Detail: `phase2b/summary.md` (why
files were left out), `phase2b/structure.md` (every group and folder).
Logs: `phase2b-build-output.txt`, `phase2b-render-*.txt`. Nothing is published, released or on the device.

## Result

- **29,863 of 44,392 source files are in the build** (Phase 2: 10,086). Plus 1,606 kit and slice
  files, so 31,469 in each render.
- 1,122 folders, **none over 50** (median about 30), in up to 9 groups per category. Seven small
  categories keep two levels (CYMBALS, TOMS, STABS, PIANO, ACOUSTIC, BLIPS and the sets).
- Build: 24 min (`-j 6`). Renders: a few minutes each.
- Disk: master 23 GB, Live/XO preview 21 GB, Digitakt preview 15 GB.
- **Digitakt preview: 16.1 GB.** That's too much for a 20 GB +Drive that already holds your samples
  (see the plan, option A).

| Where | Path |
|---|---|
| Held-back build (verify failed) | `out/full2/master.next` |
| Live / XO preview, three levels | `out/full2/preview/generic_folder_3` |
| Digitakt preview, three levels (unverified on the device) | `out/full2/preview/digitakt_2_50_3` |

## Groups in the biggest categories

| Category | Groups (folders) |
|---|---|
| FX (11,423 files) | foley-clicks (70), sweeps (51), foley-metal (49), impacts (40), noise (35), foley-doors-wood (29), foley (28), foley-tonal (24), whooshes (17), foley-glass (14), foley-paper (8), foley-footsteps (7), foley-mechanical (4), other (4) |
| DRUMLOOPS (3,490) | 060-100bpm (6), 100-120bpm (10), 120-130bpm (17), 130-140bpm (20), 140-160bpm (23), 160-200bpm (15), tops (26), classic-breaks (3) |
| SNARES (2,220) | snappy (23), tonal (23), breaks-lofi (8), bright (7), clap-snare (7), long (1) |
| KICKS (2,128) | punchy (26), tonal (18), long (11), drum-machine (7), dirty (5), 808 (4) |
| HATS (2,128) | closed (45), open (13), shaker (12), tambourine (1) |

FX/foley was one 233-folder list; it's now split by the material in its folder names (patch
0006, below). foley-clicks (70) is mostly numbered `foley-clicky-N` folders, which the names can't
split further. HATS/closed (45) is the other long list.

## Verify: 5 failures (held back in `master.next`)

| Check | Count | Phase 2 |
|---|---:|---|
| allocation follows cluster size | **passes now** | failed |
| loops are whole beats at their tempo | 32 loops | 15 |
| tonal folders use tonal words (SUB "punchy...") | 4 folders | 1 |
| stereo only where it's real (near-mono stereo) | 3 files | 1 |
| one-shots end quietly (`Sample_0079.wav` click) | 1 file | 1 |
| DC offset under 2% of peak (a GLITCHMAGIC cowbell) | 1 file | new |

These are the same kinds you said were acceptable. Promoting the build still needs verify to pass
(drop the 37 files, or add a local exception for these checks).

## Acapellas

The `acapella` word works (Fourier now labels them "vocal"), but 119 stay unplaced. Live only
auto-tags files under 60 s, so these songs have no Live tag and no sound label, and at a median
3.5 min they'd fail VOX's length limit anyway. One more MP3 (Sophie Ellis-Bextor) can't be read.
Putting them in a long-vocals folder for Live is a separate small change.

## Fixed during this run

The DRUMLOOPS group rule read only tempo ranges ("130-135bpm"), so 17 folders named for a single
tempo ("140bpm-clean") landed in "other". Fixed in Fourier patch 0005 (test added) and re-rendered.
No rebuild was needed.

Foley, after your review (2026-11-04): name rules ahead of the foley band put the 233 foley
folders under foley-metal (chain, metallic), foley-doors-wood, foley-glass, foley-paper,
foley-footsteps, foley-mechanical, foley-clicks and foley-tonal; 28 with no material word stay
"foley". Fourier patch 0006 (test added), both previews re-rendered, no rebuild.
