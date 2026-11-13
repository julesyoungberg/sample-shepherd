"""The library index: a SQLite cache of a curated library (a Fourier master, or any folder of
samples) that the desktop app's browser queries. One row per audio file: path, folder,
category, duration, sample rate, channels, size, content hash and, when given Fourier's
ratings, the review verdict.

The library is only read. The index is incremental: a file whose size and modification time
match its row is not read again, so a rerun after a small change is quick.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from sample_shepherd.evaluate import CATEGORIES
from sample_shepherd.sync.projects import sha256
from sample_shepherd.util import AUDIO, wav_info

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS samples (
    path        TEXT PRIMARY KEY,   -- relative to the library root, forward slashes
    folder      TEXT NOT NULL,      -- the path's folder ('' at the top)
    category    TEXT,               -- e.g. KICKS, from the folder names; NULL if none matches
    duration    REAL,               -- seconds; NULL when the header doesn't say (non-WAV)
    sample_rate INTEGER,
    channels    INTEGER,
    size        INTEGER NOT NULL,
    mtime_ns    INTEGER NOT NULL,
    sha256      TEXT NOT NULL,
    rating      TEXT                -- Fourier's review verdict (keep, drop, misfiled); NULL if unrated
);
CREATE INDEX IF NOT EXISTS samples_folder ON samples (folder);
CREATE INDEX IF NOT EXISTS samples_category ON samples (category);
"""

_NUMBERED = re.compile(r"^\d+_")      # a render numbers category folders: 01_KICKS


def category_of(rel: str) -> str | None:
    """The first folder named after a category. Both layouts work: KICKS/... and, at four
    levels, DRUMS/01_KICKS/... (the section folder isn't a category, except VOX and FX,
    which are both)."""
    for part in rel.split("/")[:-1]:
        name = _NUMBERED.sub("", part).upper()
        if name in CATEGORIES:
            return name
    return None


@dataclass
class Changes:
    """What an index run does: files to read (new or changed) and rows to drop."""
    add: list[str] = field(default_factory=list)
    update: list[str] = field(default_factory=list)
    unchanged: int = 0
    remove: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)   # unreadable: "path: reason"
    bytes_to_read: int = 0
    stats: dict[str, os.stat_result] = field(default_factory=dict)

    def counts(self) -> dict[str, int]:
        return {"added": len(self.add), "updated": len(self.update),
                "unchanged": self.unchanged, "removed": len(self.remove), "skipped": len(self.skipped)}


def _check_paths(root: Path, db: Path) -> None:
    if not root.is_dir():
        raise ValueError(f"not a folder: {root}")
    if root.resolve() in db.resolve().parents:
        raise ValueError(f"{db} is inside the library {root}; the library is read-only, "
                         f"so put the index somewhere else")


def _connect_ro(db: Path) -> sqlite3.Connection | None:
    return sqlite3.connect(f"{db.resolve().as_uri()}?mode=ro", uri=True) if db.exists() else None


def _check_root(con: sqlite3.Connection, root: Path, db: Path) -> None:
    row = con.execute("SELECT value FROM meta WHERE key = 'root'").fetchone()
    if row and row[0] != str(root.resolve()):
        raise ValueError(f"{db} already indexes {row[0]}; pass another --db for {root}")


def _walk(root: Path, skipped: list[str]):
    """(relative path, stat) for each audio file. A file that can't be read (a broken
    symlink, no permission) goes in `skipped`: one bad file in a big library shouldn't stop
    the rest being indexed."""
    for dp, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        for f in sorted(files):
            if f.lower().endswith(AUDIO) and not f.startswith("."):
                p = Path(dp) / f
                rel = p.relative_to(root).as_posix()
                try:
                    yield rel, p.stat()
                except OSError as e:
                    skipped.append(f"{rel}: {e.strerror or e}")


def scan(root: Path, db: Path) -> Changes:
    """Compare the library with the index. Reads only; doesn't create the index."""
    root, db = Path(root), Path(db)
    _check_paths(root, db)
    known: dict[str, tuple[int, int]] = {}
    con = _connect_ro(db)
    if con:
        with con:
            _check_root(con, root, db)
            known = {p: (s, m) for p, s, m in con.execute("SELECT path, size, mtime_ns FROM samples")}
        con.close()
    ch = Changes()
    for rel, st in _walk(root, ch.skipped):
        ch.stats[rel] = st
        old = known.pop(rel, None)
        if old == (st.st_size, st.st_mtime_ns):
            ch.unchanged += 1
            continue
        (ch.add if old is None else ch.update).append(rel)
        ch.bytes_to_read += st.st_size
    ch.remove = sorted(known)
    return ch


def load_ratings(path: Path) -> dict[str, str]:
    """{master path: verdict} from Fourier's ratings.json. Each rating records `out`, the
    file's path in the master, so it matches index rows without the manifest."""
    store = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(store, dict) or not isinstance(store.get("ratings"), dict):
        raise ValueError(f"{path}: not a Fourier ratings file (no 'ratings')")
    return {r["out"]: r["verdict"].lower() for r in store["ratings"].values()
            if isinstance(r, dict) and r.get("out") and r.get("verdict")}


def index(root: Path, db: Path, changes: Changes | None = None,
          ratings: dict[str, str] | None = None) -> dict[str, int]:
    """Bring the index at `db` up to date with the library at `root`. Returns counts.
    `ratings` (from `load_ratings`) replaces every row's rating; without it they're kept."""
    root, db = Path(root), Path(db)
    ch = changes or scan(root, db)
    db.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db)
    try:
        with con:
            con.executescript(SCHEMA)
            _check_root(con, root, db)
            con.execute("INSERT OR REPLACE INTO meta VALUES ('root', ?)", (str(root.resolve()),))
            for rel in ch.add + ch.update:
                try:
                    digest = sha256(root / rel)
                except OSError as e:          # unreadable, or gone since the scan
                    ch.skipped.append(f"{rel}: {e.strerror or e}")
                    (ch.add if rel in ch.add else ch.update).remove(rel)
                    continue
                st, info = ch.stats[rel], wav_info(root / rel)
                folder = rel.rpartition("/")[0]
                con.execute(
                    "INSERT OR REPLACE INTO samples VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, "
                    "(SELECT rating FROM samples WHERE path = ?))",
                    (rel, folder, category_of(rel), info and info.seconds, info and info.rate,
                     info and info.channels, st.st_size, st.st_mtime_ns, digest, rel))
            con.executemany("DELETE FROM samples WHERE path = ?", [(p,) for p in ch.remove])
            if ratings is not None:
                con.execute("UPDATE samples SET rating = NULL")
                con.executemany("UPDATE samples SET rating = ? WHERE path = ?", [(v, p) for p, v in ratings.items()])
    finally:
        con.close()
    return ch.counts()
