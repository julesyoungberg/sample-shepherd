# Evaluating category sorting

The one place sample-shepherd makes a model-like decision is **which category each sample goes
in** (KICKS, SNARES, PADS, ... 19 in all). Fourier makes it, from the file name, its folders and
the sound (CLAP), with our patches on top. Until now we judged it by auditioning renders and
reading build logs. This adds a repeatable number, with baselines to compare it against.

```bash
sample-shepherd eval categories                          # baselines on the bundled seed labels
sample-shepherd eval categories --predictions ~/sample-work/out/master \
    --provenance listened rated-keep rated-misfiled      # Fourier's master, on human labels only
```

Nothing here reads audio, writes to the library, or touches a device.

## What gets compared

| System | What it is |
|---|---|
| `majority` | Always the most common labeled category. The floor. |
| `name` | Keywords in the file name only; abstains when the name names two categories. What a naive tool does: it reads a vendor's `SD_` prefix as "snare drum". |
| `folder` | The nearest folder that names exactly one category (`Kicks`, `Hi Hats`), skipping `Wet`, `One Shots` and the like. |
| `rules` | A careful hand-written router: a drum word in the name (with `SD_<word>` read as a vendor prefix), then the folder, then tonal and FX words, with `loop`/`bpm` moving a sample to DRUMLOOPS or PHRASES. A strong path-only baseline (tuned on the same synthetic rows, so read its seed-set score with that in mind). |
| `--predictions` | Any real system's output: a Fourier master folder (its `manifest.json`), or a `path,category` CSV from anything else. |

A sample a system doesn't place counts as **abstaining**. That's wrong for accuracy, but it is
reported apart as `coverage`. For a Fourier master this matters: a sample missing from the master
may be a routing miss, or just over its category's budget. Read `acc|decided` (accuracy when it
did decide) next to plain accuracy.

## Metrics

- **accuracy**, with a 95% bootstrap interval. With a few dozen labels the interval is wide, and
  that's the honest answer.
- **coverage** and **acc|decided** (above).
- **macro-F1** over the categories that have labels, so a rare category counts as much as KICKS.
- **per category** precision, recall and F1, a **confusion matrix**, and the **errors** list.
- **by provenance**: accuracy for each label source (next section), side by side.

`--json FILE` writes all of it; `--fail-under rules=0.9` exits 1 below a floor, for CI.

## The labels, and how far to trust them

`eval/labels/categories.csv` is the seed set: `path,category,provenance,note`, paths relative to
the library root (or a shorter tail of it), no audio. Every row says where its label came from:

| Provenance | Rows | What it is |
|---|---:|---|
| `folder-rule` | 30 | The Brad Brunazzi `SD_` files from phase 1, labeled by their pack folder (`config/ratings/brad-brunazzi-sd.csv`). |
| `documented` | 9 | Cases a phase report settles (e.g. `Cymbals & Percussion/SD_LINDRUM_Clap` is a clap; `Aluminum20a` is foley, not a loop). |
| `synthetic` | 47 | Invented names (Acme, Northwind), 2+ per category, each pinning down one naming pattern. |
| `listened`, `rated-keep`, `rated-misfiled` | 0 so far | A person auditioned it. **The only labels that measure real accuracy.** |

**Read the seed set as a regression suite, not an accuracy estimate.** The synthetic rows and the
`rules` baseline were written by the same person (Claude) in the same change, so `rules` scoring
0.97 on them says the rules do what they were written to do, nothing more. Nobody has listened to
any seed row. Path-only labels also can't catch what only the sound tells: a file named `Kick` that
is really a tom.

## Growing a real test set

Two ways to get human labels, both of which read only:

1. **From ratings you already make.** Rating in Fourier's listening page (`fourier open report`)
   records Keep / Drop / Misfiled. Import them:

   ```bash
   sample-shepherd eval import-ratings "$FOURIER_HOME/ratings.json" \
       --labels eval/labels/categories.csv \
       --root "~/Music/Ableton/User Library/Samples/sample packs" --dry-run
   ```

   A Keep confirms its category; a Misfiled gives the category it belongs in (its `target`). A
   Drop says nothing about the category and is skipped. Note the bias: you rate what you notice, so
   these lean toward mistakes.

2. **An unbiased sample.** Draw a fixed number of placed samples from each category of a master,
   in random order, with the category column left blank so you aren't anchored by Fourier's pick:

   ```bash
   sample-shepherd eval sample ~/sample-work/out/master --per-category 10 --out ~/sample-work/labels-1.csv
   # audition each path, fill in its category, then:
   sample-shepherd eval categories --labels ~/sample-work/labels-1.csv --predictions ~/sample-work/out/master
   ```

   190 rows (10 × 19) is roughly an hour of listening and gives intervals of roughly ±5 points.
   Commit the filled sheet into `eval/labels/` (paths only; it holds no audio).

Then every change to the patches, the overlay or the budgets can be scored before and after:
build, run `eval categories --predictions` on both masters, compare.

## Not covered yet

- **Duplicate and +Drive matching** (`scripts/drive_match.py`) is the other rule-based decision.
  It's deterministic with tolerances; scoring it needs device listings matched by hand, which
  waits until the live sync is finished.
- **Keep/drop curation.** The ratings so far are all Drops (38 in `config/ratings-snapshot.json`,
  39 in `config/phase2b-drops.csv`), so there's nothing to measure precision against yet.
