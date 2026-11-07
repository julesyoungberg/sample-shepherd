"""Project backups and the samples projects use.

An Elektron project download (.dt2prj on the Digitakt II) is a zip holding manifest.json and
the samples themselves. The manifest lists every sample the project references:

  {"Samples": [{"FileName": "Samples/<+Drive path>.wav", "FileSize": 123456, "Hash": 3735928559}]}

Projects reference samples by hash and size, so this list is exactly what must never be
deleted from the device.
"""
from __future__ import annotations

import collections
import hashlib
import json
import posixpath
import zipfile
from dataclasses import dataclass
from pathlib import Path

USED_HEADER = ["path", "size", "hash", "projects"]


@dataclass(frozen=True)
class UsedSample:
    path: str      # device path as `drive ls` writes it: from the root, no extension
    size: int | None
    hash: str | None   # 8 lowercase hex digits, as elektroid-cli lists it


def _get(d: dict, key: str):
    for k, v in d.items():
        if k.lower() == key.lower():
            return v
    return None


def device_path(file_name: str) -> str:
    """'Samples/01_KICKS/hard/BD 01.wav' -> '/01_KICKS/hard/BD 01'."""
    p = file_name.replace("\\", "/").lstrip("/")
    head, _, rest = p.partition("/")
    if head.lower() == "samples" and rest:
        p = rest
    root, ext = posixpath.splitext(p)
    if ext.lower() in (".wav", ".aif", ".aiff", ".flac", ".mp3"):
        p = root
    return "/" + p


def hash_hex(value) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, str):
        value = value.strip()
        n = int(value, 16) if value.lower().startswith("0x") else int(value)
    else:
        n = int(value)
    return f"{n & 0xFFFFFFFF:08x}"


def read_manifest(project_file: Path) -> list[UsedSample]:
    """The samples one project backup references. Raises ValueError for a file that isn't a
    project zip with a manifest."""
    try:
        with zipfile.ZipFile(project_file) as z:
            names = [n for n in z.namelist() if posixpath.basename(n).lower() == "manifest.json"]
            if not names:
                raise ValueError(f"{project_file}: no manifest.json in the project zip")
            doc = json.loads(z.read(min(names, key=len)).decode("utf-8-sig"))
    except zipfile.BadZipFile:
        raise ValueError(f"{project_file}: not a zip (is it a project backup?)") from None
    samples = _get(doc, "Samples") if isinstance(doc, dict) else None
    if samples is None:
        # Never read a missing list as "uses nothing": that would make every sample look
        # deletable. Only some devices' packages list samples (see README, Supported devices).
        raise ValueError(f"{project_file}: manifest.json has no Samples list; this device's "
                         f"project packages don't say which samples they use")
    out = []
    for s in samples:
        fn = _get(s, "FileName")
        if not fn:
            continue
        size = _get(s, "FileSize")
        out.append(UsedSample(device_path(fn), int(size) if size not in (None, "") else None,
                              hash_hex(_get(s, "Hash"))))
    return out


PROJECT_SUFFIXES = (".dt2prj", ".dtprj", ".arprj", ".msprj")


def used_samples(backup_dir: Path, suffixes: tuple[str, ...] = PROJECT_SUFFIXES) -> tuple[dict[UsedSample, list[str]], list[Path]]:
    """{sample: [project files using it]} over every project backup under backup_dir, plus
    the project files read."""
    files = sorted(p for p in Path(backup_dir).rglob("*")
                   if p.is_file() and p.suffix.lower() in suffixes
                   and not any(d.endswith(".part") for d in p.relative_to(backup_dir).parts[:-1]))
    used: dict[UsedSample, list[str]] = collections.defaultdict(list)
    for f in files:
        label = str(f.relative_to(backup_dir))
        for s in read_manifest(f):
            used[s].append(label)
    return dict(used), files


def used_rows(used: dict[UsedSample, list[str]]) -> list[list]:
    return [[s.path, "" if s.size is None else s.size, s.hash or "", "; ".join(sorted(set(p)))]
            for s, p in sorted(used.items(), key=lambda kv: kv[0].path)]


def load_used(path: Path) -> list[UsedSample]:
    from sample_shepherd.util import read_csv
    return [UsedSample(r["path"], int(r["size"]) if r.get("size") else None, r.get("hash") or None)
            for r in read_csv(path)]


def slot_folder(slot: str) -> str:
    return f"slot-{int(slot):04d}" if slot.isdigit() else f"slot-{slot}"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
