# Phase 2b plan: keep as many files as possible, three folder levels

Status: **prepared, dry run done, waiting for your go-ahead to build.** Nothing has been built,
rendered, published or released. The Phase 2 build (`out/full/`) is untouched, so we can compare.

## Where the 34,306 left-out files went

Each left-out file is counted once, by its strongest reason:

| Why it was left out | Files | Digitakt size | This plan |
|---|---:|---:|---|
| **Only by a size cap** (over the category budget, per-vendor 40% share, per-pack-folder cap) | 20,236 | ~12.3 GB | **kept now** |
| A quality or fit gate (too long, too many onsets, no tempo, a loop that isn't a whole bar, silence, ...) | 11,788 | | still left out, as you said |
| Duplicates (twins, near-duplicates, copies) | 1,426 | | still left out |
| Unrecognised (no rule or sound said what it is) | 856 | | still left out, except the acapellas (below) |

Of the 20,236, I keep everything except the **1,790 left out only by the multisample cap**: the
same patch at other notes or velocities (at most 3 a folder). They're close to duplicates, so I
treated them like duplicates. Say if you want them back (`SIBLING_CAP`).

## Expected result

About **28,500 source files** (Phase 2: 10,086), plus kits and slice sets.

| Category | Phase 2 | Added | | Category | Phase 2 | Added |
|---|---:|---:|---|---|---:|---:|
| FX | 852 | 9,676 | | SUB | 814 | 187 |
| DRUMLOOPS | 1,383 | 2,159 | | PADS | 647 | 102 |
| SNARES | 775 | 1,392 | | BLIPS | 98 | 66 |
| HATS | 775 | 1,351 | | ACOUSTIC | 244 | 55 |
| KICKS | 853 | 1,280 | | CYMBALS | 220 | 21 |
| PHRASES | 477 | 979 | | PIANO | 124 | 17 |
| PERC | 773 | 450 | | TOMS | 198 | 5 |
| CLAPS | 466 | 369 | | STABS | 199 | 3 |
| VOX | 630 | 332 | | SYNTH | 558 | 2 |

Most of the new FX is foley: Live tags 9,641 of the library's files "Field & Foley".

## The Digitakt doesn't have room for all of it (needs your decision)

The Digitakt render would be about **16–18 GB**. The +Drive is 20 GB in total and already holds
your current samples. Most of the growth is in three categories: FX (+4.9 GB), DRUMLOOPS
(+3.2 GB) and PHRASES (+2.0 GB). The drum one-shots add only about 0.6 GB together.

Options:
- **A. Two builds from the same analysis (recommended).** A *full* build with everything, for
  Live and XO, and a *Digitakt* build that keeps everything in the drum and small categories but
  caps FX, DRUMLOOPS and PHRASES (e.g. at their Phase 2 sizes). That's about **7 GB** on the
  device. Each build is about 30 minutes; the analysis is shared and already done.
- B. One build, and the Digitakt gets all of it. It probably won't fit next to what's already on
  the +Drive. We'll know after the free-space check in device session 1.
- C. One build now for Live and XO, and decide the Digitakt later. Nothing on the device changes
  until a `v1` release anyway.

Option C costs nothing now: I can build the full set and you decide A or B later.

## What changed (all reversible; Phase 2 settings saved in `tmp/`)

**Fourier patch 0004** (local branch `local/adaptive-folders`, saved in `config/patches/`; tests:
2,052 passed, plus 7 new):
- `FOLDER_ADAPTIVE`: a category gets as many folders as its files need, about 1 per 40 files. A
  folder that would go over 50 files splits by sound (KMeans) instead of leaving files out. Folders
  under 6 files join their nearest neighbour.
- `DIR_CAPS`: switches off the per-pack-folder cap.
- **The third folder level, render-time: `CATEGORY/group/family`.** It applies only to categories
  with more than 12 folders; smaller ones keep two levels. Group names come from **Live 12's own
  auto-tags**, which Fourier reads from Live's database (43,948 of your 44,392 samples carry one),
  plus Fourier's bands and the folder names. Examples:
  - HATS: closed / open / shaker / tambourine
  - PERC: hand-drums / wood / metal / shakers
  - FX: foley / impacts / risers / sweeps / noise / ...
  - DRUMLOOPS: 060-100bpm ... 160-200bpm / tops / classic-breaks
  - VOX: vocals / chops / shouts / speech
  - SYNTH: lead / bass / bells / keys
  - KICKS and SNARES: Live only tags these "Kick" and "Snare Hit", so their groups come from
    Fourier's sound words: kicks are 808 / drum-machine / long / tonal / punchy / dirty; snares are
    rim / clap-snare / snappy / tonal / bright / breaks-lofi.

  The rules are one setting (`FOLDER_GROUPS`), so they're easy to change after you browse.
- verify: the folder-count checks follow adaptive folders.

**Config:**
- `config/overlay.yaml`: the folder settings above, budgets effectively unlimited, and no per-vendor cap.
- `config/fourier.toml`: outputs go to `out/full2/`. It adds the words `acapella` and `acapellas`
  for VOX, and two new device profiles:
  - `generic_folder_3`: three levels, for Live and XO.
  - `digitakt_2_50_3`: three levels. **Preview only**, because it's unverified whether the
    +Drive browser opens folders that deep (checklist, section 5). `digitakt_2_50` (two levels)
    stays available.

**Our scripts:** `drive_match.py` and `folder_structure.py` now read three-level renders. Checked
on the Phase 2 render: all 10,086 files map as before.

## Your earlier answers, applied

1. Third level: done as described, only where a category needs it.
2. Verify failures:
   - The allocation failure was caused by the caps. With folders splitting instead of filling to
     50, it should clear.
   - The other four (15 loops off the beat, the FX click, the near-mono hat, the `punchy-plucky`
     SUB name) you're fine with. But Fourier only puts a build in place when verify passes, and
     there's no override. So before a release, either drop those few files (`fourier review rate
     ... drop`, 17 files out of about 28,500), or I add a local exception for those checks. We
     can decide once we see the new build's own failures.
3. Acapellas as VOX: added. **But 133 of the 142 are whole songs** (median 3.5 min). The length
   gate will still leave those out, and the Digitakt can't hold more than 66 s anyway. Only about
   9 will come through. If you want the full songs for Live, a separate long-vocals folder for the
   generic render would do it.

## The build, if you approve

```bash
. ~/sample-work/fourier.env && cd ~/sample-work
fourier build -j 6 > reports/phase2b-build-output.txt 2>&1      # master in out/full2/master(.next)
fourier render generic_folder_3 --from <master> --out out/full2/preview/generic_folder_3
fourier render digitakt_2_50_3  --from <master> --out out/full2/preview/digitakt_2_50_3
python -I scripts/build_report.py   --master <master> --renders out/full2/preview --out reports/phase2b
python -I scripts/folder_structure.py --root out/full2/preview/generic_folder_3 --out reports/phase2b
```

- **Time:** about 30–45 minutes for the build (analysis is cached), and a few minutes per render.
- **Disk:** about 70 GB new (master ~25 GB, Live/XO preview ~27 GB, Digitakt preview ~17 GB).
  About 950 GB is free.
- Nothing is published or released, and nothing touches the source library or the device.
