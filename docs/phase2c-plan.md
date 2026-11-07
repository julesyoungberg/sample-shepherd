# Phase 2c plan: drop the verify failures, fix SUB names, finer groups

Status: **built 2026-11-06, verify passed, master in place at `out/full2/master`.** Both
previews re-rendered from it. Nothing is published, released or on the device.

## Result

- verify: **PASS** (121 pass, 4 warnings, 0 fail). The first rebuild failed on one more loop off
  the beat (`Evelyn_-_400_Breakbeats_-_175_breaking_sky.wav`, 44 ms short), which came in once the
  others were dropped. It's dropped too (38 drops in all, in `config/phase2b-drops.csv`), and the
  second rebuild passed.
- 29,849 source files, 31,455 per render with kits and slices; 1,111 folders, none over 50.
  Live/XO render 22.1 GB, Digitakt render 16.0 GB, master 23 GB.
- SUB has no "punchy" folders now (e.g. `dark-swelling-sustained`, `wobble-short`, `808-sub`).
- Groups after the rebuild: FX foley-doors-wood (41), foley-metal (36), foley-chains (25),
  foley-scifi (22), foley (19), foley-glass (17), foley-kitchen (15), foley-tonal (15),
  foley-paper (12), foley-clicks (11), foley-plastic (8), foley-footsteps (5), foley-mechanical (2),
  foley-water (2); HATS closed-clicky (19), closed-tonal (9), closed-machine (7), closed (6).
- **Python repair:** between the two rebuilds, Homebrew removed its python@3.13, which the
  Fourier venv was built on. Python 3.13.16 now lives in `vendor/python` (uv-managed), and the venv
  is recreated from the lock file with the same 85 packages. The old venv is in
  `tmp/venv.broken-20261106`. Homebrew wasn't touched.
- Reports: `reports/phase2c-build-output.txt` (`.1.txt`: the first rebuild),
  `reports/phase2c/structure.md`, `reports/phase2c-render-*.txt`.

## Your answers, applied

1. **Digitakt size:** decided when you plug it in (device session 1). Clearing samples no
   project uses (Phase 3) should leave room for the 16.1 GB render. Nothing changes until then.
2. **The verify failures:** done as you said, with one correction.
   - **37 files dropped** (38 after the rebuild, see Result): 32 loops off whole beats (14
     DRUMLOOPS, 18 PHRASES), the cowbell with DC offset, the FX file with a click and 3
     near-mono hats/snares. They're stored as Drop ratings (`config/phase2b-drops.csv`, imported; ratings
     backed up in `tmp/ratings.before-phase2c.json`), so the next build leaves them out.
   - **The 4 SUB "punchy" folders weren't 4 files.** They're 4 folders holding 111 bass
     sounds, named from Fourier's phrase "punchy bass". Rather than drop them, Fourier patch
     0007 keeps drum words out of tonal folder names. The next build names those folders from
     their tonal traits instead (dark, swelling, sustained, ...).
3. **Acapellas:** your call, see below.
4. **Finer groups:** done (patch 0008), and re-rendered:

| Where | Before | Now |
|---|---|---|
| FX foley (233 folders) | one `foley` list | foley-chains (28), foley-metal (38), foley-doors-wood (38), foley-scifi (20), foley-kitchen (17), foley-clicks (17), foley-tonal (15), foley (15), foley-glass (14), foley-paper (12), foley-plastic (8), foley-footsteps (7), foley-mechanical (4) |
| HATS closed (45 folders) | one `closed` list | closed-clicky (21), closed-tonal (10), closed-machine (7), closed (5), closed-acoustic (2) |

The foley folders with no material in their name (the numbered `foley-clicky-N` ones) are
grouped by what most of their files' own names say: "SilverwareInHands" is kitchen,
"WoodSticksOnConcrete" is wood, "BiomechCloneComponent" is sci-fi. A word list per group is in
`FOLDER_GROUPS` (curate_config.py); you can extend it after browsing.

## The rebuild, if you approve

```bash
. ~/sample-work/fourier.env && cd ~/sample-work
fourier build > reports/phase2c-build-output.txt 2>&1
fourier render generic_folder_3 --from <master> --out out/full2/preview/generic_folder_3
fourier render digitakt_2_50_3  --from <master> --out out/full2/preview/digitakt_2_50_3
```

- **Expected:** 29,826 source files (29,863 minus the 37), the 4 SUB folders renamed, and
  **verify passing**.
- **What a passing verify does:** Fourier puts the build in place as the master,
  `out/full2/master` (local, inside `~/sample-work`). That's not a publish or a release, and
  nothing goes to the device. But it's the step you asked me to hold for approval, so approving
  the rebuild approves that too. The Phase 2 master in `out/full/` stays untouched.
- **Time:** about 25–30 minutes for the build, a few minutes per render.
- **Disk:** about the same as now (the held build in `master.next` is replaced, about 23 GB).

## Acapellas (needs your decision)

The 143 files in `2024/Acapellas` are whole songs: median 3.5 minutes, the longest 8 minutes,
only 7 under 60 seconds, and one MP3 is unreadable. Fourier drops anything over 60 seconds
before it looks at categories, and that's hard-coded. Two ways to get them a folder:

- **A. A plain `ACAPELLAS` folder next to the Live/XO render (recommended).** A small script
  of ours copies the 142 readable files into `out/full2/extras/ACAPELLAS/` as they are (0.85 GB
  MP3), or converted to WAV (about 7.7 GB). It stays off the Digitakt, and it's ready in a few
  minutes with no Fourier patch.
- **B. A real Fourier category.** It would be levelled and named like the rest, but it needs
  a patch to the 60-second rule, adds about 7.7 GB to the master and again to the render, and
  needs a way to keep it out of the Digitakt render. That's a larger change for 142 files
  that Live already finds in your User Library.
