#!/usr/bin/env python3
"""Shared matching for Phase 3: which source file a +Drive sample came from, and where that
source now lives in the new library (a render of the master).

Inputs (formats are ours, as the device's own exports are unverified; see README Phase 3):
- a +Drive listing: a CSV with a `path` column (the +Drive path, e.g. "/Drums/909/BD 01.wav")
  and, when known, `size` (bytes) and `seconds`; or a plain text file, one path per line; or a
  folder holding a copy of the +Drive's files (sizes are then read, and bytes hashed).
- the source library, from Fourier's database (read-only): every scanned file's path, name,
  size, duration, sample rate, channels and hash.
- the new library: the master's manifest.json and a render folder (e.g. digitakt_2_50).

Matching a +Drive sample to a source, strongest first:
1. hash: the +Drive file's bytes equal a source's (only with a folder copy; rare, since
   Transfer converts every file to 16-bit / 48 kHz on upload, manual p.73);
2. name + size: the same file name (case and extension aside) and the size the source has
   once converted to 16-bit / 48 kHz WAV, within SIZE_TOL;
3. name + duration: the same name and duration within DUR_TOL_S.
A name that matches several sources is decided by size or duration; if that leaves more than
one, or none, the sample is unmatched. Nothing is guessed from the name alone.
"""
from __future__ import annotations

import collections
import csv
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

W = Path.home() / "sample-work"
DT_RATE, DT_BYTES_PER_SAMPLE, WAV_HEADER = 48000, 2, 44
SIZE_TOL = 0.01          # 1% (Transfer's header chunks and resampling length vary a little)
SIZE_TOL_MIN = 4096      # or 4 KB, whichever is more
DUR_TOL_S = 0.02
AUDIO = (".wav", ".aif", ".aiff", ".flac", ".mp3")


def stem_key(name: str) -> str:
    """A file name as matching compares it: no folder, no extension, lowercase."""
    return os.path.splitext(os.path.basename(name))[0].strip().lower()


def predicted_size(frames_s: float, channels: int) -> int:
    """Bytes of a 16-bit / 48 kHz WAV of this length and channel count (Transfer's output)."""
    return WAV_HEADER + round(frames_s * DT_RATE) * max(1, min(2, channels)) * DT_BYTES_PER_SAMPLE


def size_close(a: int, b: int) -> bool:
    return abs(a - b) <= max(SIZE_TOL_MIN, SIZE_TOL * max(a, b))


@dataclass
class Source:
    path: str
    size: int
    seconds: float
    channels: int
    md5: str | None


@dataclass
class DriveFile:
    path: str
    size: int | None = None
    seconds: float | None = None
    md5: str | None = None


@dataclass
class Match:
    source: Source | None
    how: str                     # hash | name+size | name+duration | ambiguous | none
    candidates: list = field(default_factory=list)


def load_sources(db_path: Path, roots: list[str] | None = None) -> list[Source]:
    """Every scanned library file (read-only), optionally only those under `roots`."""
    import duckdb
    db = duckdb.connect(str(db_path), read_only=True)
    rows = db.execute("select path, file_size_bytes, duration_s, channels, file_hash from samples").fetchall()
    roots = [r.rstrip("/") + "/" for r in (roots or [])]
    return [Source(p, s or 0, d or 0.0, c or 1, h) for p, s, d, c, h in rows
            if not roots or any(p.startswith(r) for r in roots)]


def load_drive(listing: Path, hash_files: bool = True) -> list[DriveFile]:
    """A +Drive listing: a CSV (path[, size][, seconds]), a text file of paths, or a folder copy."""
    if listing.is_dir():
        out = []
        for dp, _, fs in os.walk(listing):
            for n in sorted(fs):
                if n.lower().endswith(AUDIO):
                    p = Path(dp) / n
                    out.append(DriveFile("/" + str(p.relative_to(listing)), p.stat().st_size,
                                         _seconds(p), _md5(p) if hash_files else None))
        return out
    text = listing.read_text(encoding="utf-8-sig")
    first = text.splitlines()[0] if text else ""
    if "," in first and "path" in [c.strip().lower() for c in first.split(",")]:
        out = []
        for r in csv.DictReader(text.splitlines()):
            r = {k.strip().lower(): (v or "").strip() for k, v in r.items()}
            out.append(DriveFile(r["path"], int(r["size"]) if r.get("size") else None,
                                 float(r["seconds"]) if r.get("seconds") else None))
        return out
    return [DriveFile(line.strip()) for line in text.splitlines() if line.strip()]


def _seconds(p: Path) -> float | None:
    try:
        import soundfile as sf
        return sf.info(str(p)).duration
    except Exception:
        return None


def _md5(p: Path) -> str:
    h = hashlib.md5()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Matcher:
    def __init__(self, sources: list[Source]):
        self.by_name: dict[str, list[Source]] = collections.defaultdict(list)
        self.by_hash: dict[str, list[Source]] = collections.defaultdict(list)
        for s in sources:
            self.by_name[stem_key(s.path)].append(s)
            if s.md5:
                self.by_hash[s.md5].append(s)

    def match(self, f: DriveFile) -> Match:
        if f.md5 and len(self.by_hash.get(f.md5, ())) == 1:
            return Match(self.by_hash[f.md5][0], "hash")
        cands = self.by_name.get(stem_key(f.path), [])
        if not cands:
            return Match(None, "none")
        if f.size is not None:
            hit = [s for s in cands if size_close(f.size, predicted_size(s.seconds, s.channels))]
            if len(hit) == 1:
                return Match(hit[0], "name+size")
            if len(hit) > 1:
                cands = hit
        if f.seconds is not None:
            hit = [s for s in cands if abs(f.seconds - s.seconds) <= DUR_TOL_S]
            if len(hit) == 1:
                return Match(hit[0], "name+duration")
            if len(hit) > 1:
                cands = hit
        if len(cands) > 1:
            return Match(None, "ambiguous", cands)
        return Match(None, "name only" if f.size is None and f.seconds is None else "none", cands)


def new_paths(master: Path, render: Path) -> dict[str, str]:
    """{source absolute path: its path in the render, from the render's root}. The render's
    folders are the master's with a play-order prefix ("KICKS" -> "01_KICKS") and, in a
    three-level render, a group folder between category and family ("04_HATS/closed/..."),
    so a manifest entry (category, family/file) is found by stripping that prefix and taking
    the innermost folder as the family; a name the device's rules changed is found by its
    stem within the same family folder."""
    man = json.loads((master / "manifest.json").read_text())
    roots = [os.path.expanduser(r) for r in man["src_roots"]]
    files: dict[tuple[str, str], dict[str, str]] = collections.defaultdict(dict)   # (cat, family) -> stem -> rel
    for dp, _, fs in os.walk(render):
        rel = Path(dp).relative_to(render)
        if not rel.parts:
            continue
        cat = re.sub(r"^\d+_", "", rel.parts[0])
        fam = rel.parts[-1] if len(rel.parts) > 1 else ""
        for n in fs:
            if n.lower().endswith(AUDIO):
                files[(cat, fam)][stem_key(n)] = str(rel / n)
    out = {}
    for cat, c in man["categories"].items():
        for e in c.get("entries", []):
            fam, _, name = e["out"].rpartition("/")
            rel = files.get((cat, fam), {}).get(stem_key(name))
            if not rel:
                continue
            for r in roots:
                p = os.path.join(r, e["src"])
                if os.path.exists(p):
                    out.setdefault(p, "/" + rel)
                    break
    return out


def read_projects(folder: Path) -> dict[str, set[str]]:
    """{project: the +Drive paths it uses}: one text file per project in `folder`, one +Drive
    path per line (blank lines and lines starting with # ignored). The file's stem names the
    project."""
    out = {}
    for p in sorted(folder.glob("*.txt")):
        out[p.stem] = {ln.strip() for ln in p.read_text(encoding="utf-8-sig").splitlines()
                       if ln.strip() and not ln.lstrip().startswith("#")}
    return out


def norm_drive(path: str) -> str:
    """A +Drive path as compared between the listing and the project lists."""
    return "/" + path.strip().strip("/").lower()


if __name__ == "__main__":
    print(__doc__)
    sys.exit(0)
