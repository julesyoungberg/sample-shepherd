"""A read-only listing of the device's sample storage, as CSV: path,size,hash.

Paths start at the storage root and carry no extension (the device drops it on upload), e.g.
"/01_KICKS/hard/BD 01". Sizes are as precise as the backend reports them (elektroid-cli
rounds to 4 significant digits)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sample_shepherd.util import read_csv, write_csv

HEADER = ["path", "size", "hash"]


@dataclass(frozen=True)
class Listed:
    path: str
    size: int | None
    hash: str | None


def collect(device, root: str = "/", progress=None) -> list[Listed]:
    return sorted((Listed(p, e.size, e.hash) for p, e in device.walk(root, progress)),
                  key=lambda r: r.path)


def write(rows: list[Listed], out: Path) -> None:
    write_csv(out, HEADER, ([r.path, "" if r.size is None else r.size, r.hash or ""] for r in rows))


def load(path: Path) -> list[Listed]:
    return [Listed(r["path"], int(r["size"]) if r.get("size") else None, (r.get("hash") or "").lower() or None)
            for r in read_csv(path)]
