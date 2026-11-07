"""Evaluate how samples get sorted into categories, against hand-labeled ground truth.

Fourier decides each sample's category (KICKS, PADS, ...) from its name, its folder and its
sound. This package measures how good those decisions are, the same way for every system:

- labels: a CSV of library paths and the category each belongs in (no audio).
- systems: simple baselines that read only the path (`baselines`), and any real system's
  output, such as a Fourier master's manifest.json (`predictions`).
- metrics: accuracy with a bootstrap interval, coverage (how often a system decides at all),
  macro-F1, per-category precision and recall, and a confusion matrix (`metrics`).

`sample-shepherd eval` is the command line for it. Nothing here reads audio or a device.
"""

# Fourier's taxonomy (config/taxonomy.yaml at the patched base, 131ee62): every category a
# sample can be routed to. KITS and SLICE in a render are sets made from these, not categories.
CATEGORIES = (
    "KICKS", "SNARES", "CLAPS", "HATS", "CYMBALS", "TOMS", "PERC",
    "DRUMLOOPS", "PHRASES",
    "SUB", "SYNTH", "STABS", "PADS", "PIANO", "ACOUSTIC", "WAVES",
    "FX", "BLIPS", "VOX",
)
