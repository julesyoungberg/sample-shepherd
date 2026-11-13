# Our patches to Fourier Samples

sample-shepherd's `organize` layer is [Fourier Samples](https://github.com/bvk7787/fourier-samples)
(Apache-2.0), run as the separate `fourier` command. Fourier has no Python API or plugin hook
for curation rules, so our changes to it are kept as `git format-patch` files in
[config/patches](../config/patches), not as a fork or vendored copy.

- **Base:** `bvk7787/fourier-samples` at `131ee62` (v0.1.2, still upstream `main` on 2026-11-07).
- **Branch name used locally:** `local/adaptive-folders`.
- **All 8 apply cleanly** to the base with `git am` (checked 2026-11-07).

## Install the patched build

```bash
sample-shepherd organize install-fourier --dir ~/opt/fourier-samples --dry-run   # shows the steps
sample-shepherd organize install-fourier --dir ~/opt/fourier-samples
```

That clones the base, creates the branch, runs `git am` on the patches (git needs your
`user.name` and `user.email`), and `uv sync --frozen --extra clap` into `<dir>/.venv`. Then set
`[fourier] command = "~/opt/fourier-samples/.venv/bin/fourier"` in your config.

Stock Fourier from PyPI (`pip install 'sample-shepherd[organize]'`) works for Fourier's own
profiles, but rejects our overlay (`unknown tunable 'FOLDER_ADAPTIVE'`) and has no
three-level folders, so our `*_3` profiles need the patched build.

## Refresh the patches

After changing the local branch, or rebasing it onto a newer upstream:

```bash
cd <fourier checkout>
git rebase <new upstream commit> local/adaptive-folders      # only when moving the base
.venv/bin/python -m pytest -n auto -q                         # Fourier's own suite
git format-patch -o <sample-shepherd>/config/patches <base>..local/adaptive-folders
```

Then update the base commit here and in `src/sample_shepherd/organize/fourier.py`
(`FOURIER_BASE`).

## What each patch does

| Patch | What | Our config needs it? | Fit for upstream |
|---|---|---|---|
| 0001 | A vendor's `SD_` name prefix ("SD_Falcon_Kick") is a prefix, not "snare drum" | Changes classification of such packs | Generic. Good candidate |
| 0002 | Lets `SD_<word>` names through the KICKS name filter | With 0001 | Same |
| 0003 | The folder overrules an `SD_` name only when the name names no drum | With 0001 | Same |
| 0004 | Adaptive folder counts (`FOLDER_ADAPTIVE`, `DIR_CAPS`) and a third folder level (`folder_depth: 3`, groups from `FOLDER_GROUPS`) | **Yes:** `config/overlay.yaml` and the `*_3` profiles | Largest (~1.7k lines). Needs an issue and the maintainer's go-ahead first |
| 0005 | A one-tempo family name ("140bpm-clean") counts as its tempo for groups | Changes output | Generic |
| 0006 | Groups FX foley folders by the material in their name | Changes output | Generic |
| 0007 | Keeps a phrase's drum word out of a tonal folder's name (fixes a verify failure) | Changes output | Generic |
| 0008 | Finer groups: foley by its files' names, closed hats by folder words | Changes output | Generic |
| 0009 | Section folders above the categories at four levels (`CATEGORY_SECTIONS`: DRUMS, LOOPS, TONAL, VOX, FX) | **Yes:** the `*_4` profiles | Generic; builds on 0004 |

## Offering them upstream

Not done yet. Fourier's CONTRIBUTING asks for an
issue and a maintainer's go-ahead before a PR, tests with invented names (Acme, Northwind)
rather than real pack sample names (0001–0003's tests use names like `SD_Falcon_Kick`, so
rename those first), the synthetic golden re-run (`tests/golden/synthetic_build.py --check`),
and a `config/tunables.yaml` entry for each new tunable. A sensible order: 0001–0003 as one
small issue, then 0007, then 0004 with a design discussion.
