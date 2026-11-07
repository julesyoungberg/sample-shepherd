"""Baselines: simple category guesses from the path alone, to measure real systems against.

A system that can't beat these isn't earning its complexity. Each baseline is a function
`(path, labels) -> category or None`; None means it abstains (decides nothing), which
the metrics count as a miss but report separately as lower coverage.

- `majority`: always the most common category in the label set. The floor; it peeks at the
  labels, so it's slightly optimistic.
- `name`: keywords in the file name only. Ambiguous names (two categories) abstain. This is
  what naive tools do, and it reads a vendor's "SD_" prefix as "snare drum".
- `folder`: the nearest folder that names exactly one category ("Kicks", "Hi Hats").
- `rules`: a careful hand-written router: a drum word in the name, with a vendor "SD_" prefix
  read as a prefix, then the folder, then tonal and FX words, with "loop"/"bpm" moving a sample
  to DRUMLOOPS or PHRASES. A strong path-only baseline (tuned on the synthetic seed rows).
"""
from __future__ import annotations

import collections
import re
from typing import Callable, Sequence

from sample_shepherd.evaluate.labels import Label

Baseline = Callable[[str, Sequence[Label]], "str | None"]

# category -> words, matched on the tokenized, lowercase text (see `words`)
DRUM_WORDS = {
    "KICKS": r"kicks?|kik|bd|bass ?drums?|bassdrum",
    "SNARES": r"snares?|snr|sd|rims?|rimshots?|rim ?shots?",
    "CLAPS": r"claps?|clp|handclaps?",
    "HATS": r"hi ?hats?|hihats?|hats?|hh|open ?hat|closed ?hat",
    "CYMBALS": r"cymbals?|cymb|crash(?:es)?|rides?|china|splash",
    "TOMS": r"toms?|tomtoms?|floor ?tom",
    "PERC": r"percs?|percussion|congas?|bongos?|shakers?|tambourines?|tamb|cowbells?|claves?|"
            r"cabasa|guiro|woodblocks?|maracas?|timbales?|triangle",
}
OTHER_WORDS = {
    "VOX": r"vox|vocals?|voice|voices|acapellas?|a cappella|chants?|shouts?|adlibs?|choir",
    "FX": r"fx|sfx|risers?|impacts?|sweeps?|whoosh(?:es)?|noise|foley|downlifters?|uplifters?|"
          r"transitions?|glitch(?:es)?|ambience|texture",
    "BLIPS": r"blips?|bleeps?|zaps?|beeps?",
    "WAVES": r"single ?cycle|waveforms?|wavetables?|akwf",
    "PADS": r"pads?|drones?|atmos|atmosphere|soundscapes?",
    "PIANO": r"pianos?|rhodes|wurli(?:tzer)?|ep|e piano|grand",
    "ACOUSTIC": r"guitars?|strings?|violins?|cellos?|brass|horns?|flutes?|sax(?:ophone)?|"
                r"marimbas?|kalimbas?|harps?|trumpets?|orchestra(?:l)?",
    "STABS": r"stabs?|chords?|hits?",
    "SUB": r"sub|subs|808|basses|bass|reese",
    "SYNTH": r"synths?|leads?|plucks?|arps?|keys|bells?|mallets?",
}
DRUM_LOOP_WORDS = r"drums?|beats?|breaks?|breakbeats?|grooves?|tops?|fills?|" + "|".join(DRUM_WORDS.values())
LOOP_WORDS = r"loops?|bpm|\d{2,3} ?bpm|phrases?|riffs?|melod(?:y|ies)|progressions?|prog|seq"

# folders that say nothing about the category
SKIP_FOLDERS = re.compile(r"^(?:wet|dry|one ?shots?|oneshots?|custom one shots|samples?|"
                          r"processed|raw|misc|other|wav|audio|\d+)$", re.I)


def words(text: str) -> str:
    """'SD_OberHat-Open02.wav' -> 'sd ober hat open 02': split camelCase, digits and separators."""
    text = re.sub(r"\.(wav|wave|aif|aiff|flac|mp3|ogg)$", "", text, flags=re.I)
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    text = re.sub(r"([A-Za-z])(\d)", r"\1 \2", text)
    text = re.sub(r"(\d)([A-Za-z])", r"\1 \2", text)
    text = re.sub(r"[_\-.,()\[\]{}~#@&+]+", " ", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def _rx(alts: str) -> re.Pattern:
    return re.compile(rf"(?<![a-z])(?:{alts})(?![a-z])")


_DRUM = {c: _rx(w) for c, w in DRUM_WORDS.items()}
_OTHER = {c: _rx(w) for c, w in OTHER_WORDS.items()}
_ALL = {**_DRUM, **_OTHER}
_DRUM_LOOP = _rx(DRUM_LOOP_WORDS)
_LOOP = re.compile(rf"(?<![a-z])(?:{LOOP_WORDS})(?![a-z])|\d{{2,3}} ?bpm")
_VENDOR_SD = re.compile(r"^sd (?=[a-z]{2,})")


def named(text: str, table=None) -> set[str]:
    t = words(text)
    cats = {c for c, rx in (table or _ALL).items() if rx.search(t)}
    # "bass" alone names a SUB, but "bass drum" is a kick: let KICKS win that tie
    if "KICKS" in cats and re.search(r"bass ?drum", t):
        cats.discard("SUB")
    return cats


def _parts(path: str) -> tuple[list[str], str]:
    p = path.replace("\\", "/").strip("/").split("/")
    return p[:-1], p[-1]


def majority(path: str, labels: Sequence[Label]) -> str | None:
    counts = collections.Counter(lab.category for lab in labels)
    return min(counts, key=lambda c: (-counts[c], c)) if counts else None


def name(path: str, labels: Sequence[Label] = ()) -> str | None:
    cats = named(_parts(path)[1])
    return cats.pop() if len(cats) == 1 else None


def _folder_category(folders: list[str], table=None) -> str | None:
    for part in reversed(folders):
        if SKIP_FOLDERS.match(part.strip()):
            continue
        cats = named(part, table)
        if len(cats) == 1:
            return cats.pop()
        if cats:
            return None                    # the nearest real folder is ambiguous: decide nothing
    return None


def folder(path: str, labels: Sequence[Label] = ()) -> str | None:
    return _folder_category(_parts(path)[0])


def rules(path: str, labels: Sequence[Label] = ()) -> str | None:
    folders, file = _parts(path)
    t = words(file)
    loop = bool(_LOOP.search(t)) or any(_LOOP.search(words(f)) for f in folders[-2:])

    # 1. a drum word in the name; "SD_" followed by a word is a vendor prefix, not a snare
    t_drum = _VENDOR_SD.sub("", t)
    drums = {c for c, rx in _DRUM.items() if rx.search(t_drum)}
    if loop and (drums or _DRUM_LOOP.search(t)):
        return "DRUMLOOPS"
    if len(drums) == 1:
        return drums.pop()

    # 2. the nearest folder that names one category (drums or otherwise)
    by_folder = _folder_category(folders)
    if by_folder in DRUM_WORDS and not drums:
        return "DRUMLOOPS" if loop else by_folder
    if drums and by_folder in drums:
        return by_folder

    # 3. other words in the name, VOX and FX first (a vocal chop is VOX, loop or not)
    others = [c for c in OTHER_WORDS if _OTHER[c].search(t)]
    for c in ("VOX", "FX", "BLIPS", "WAVES"):
        if c in others:
            return c
    if others:
        return "PHRASES" if loop else others[0]
    if by_folder in ("VOX", "FX", "BLIPS", "WAVES"):
        return by_folder
    if by_folder:
        return "PHRASES" if loop else by_folder
    if loop:
        return "DRUMLOOPS" if _DRUM_LOOP.search(" ".join(words(f) for f in folders)) else "PHRASES"
    return None


BASELINES: dict[str, Baseline] = {
    "majority": majority,
    "name": name,
    "folder": folder,
    "rules": rules,
}
