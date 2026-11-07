"""Device profiles: YAML files in Fourier's profile format (docs/adding-a-profile.md).

A profile names an id, optionally `extends:` another, and sets `paths:` and `audio:` values
as `{value: ..., status: ...}`. Fourier renders with them; sample-shepherd also reads them
to check a render (files per folder, folder depth, sample rate, bit depth).

Search order: [export] profile_dirs from the config, then $FOURIER_DEVICES (from the
[fourier] env or the environment), then the profiles bundled with sample-shepherd. The
base profiles Fourier ships (digitakt_2, generic_folder, ...) are found in Fourier's own
config/devices when that's on the list; if not, BASE_FACTS stands in for checking.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

# Facts from Fourier's own base profiles (fourier-samples 0.1.2, config/devices), used only
# when the base profile file isn't available to read.
BASE_FACTS = {
    "digitakt_2": {"folder_depth": 2, "files_per_folder": 128, "sample_rate": 48000, "bit_depth": 16},
    "generic_folder": {"folder_depth": 2, "files_per_folder": None, "sample_rate": 44100, "bit_depth": 24},
}
KEYS = ("folder_depth", "files_per_folder", "sample_rate", "bit_depth")


def bundled_dir() -> Path:
    pkg = Path(__file__).resolve().parent.parent / "profiles"
    if pkg.is_dir():
        return pkg
    return Path(__file__).resolve().parents[3] / "config" / "devices"   # running from a checkout


def search_dirs(cfg=None) -> list[Path]:
    dirs = list(cfg.profile_dirs) if cfg else []
    env = (cfg.fourier_env.get("FOURIER_DEVICES") if cfg else None) or os.environ.get("FOURIER_DEVICES")
    if env:
        dirs.append(Path(env).expanduser())
    dirs.append(bundled_dir())
    seen, out = set(), []
    for d in dirs:
        if d.resolve() not in seen and d.is_dir():
            seen.add(d.resolve())
            out.append(d)
    return out


def find(profile_id: str, dirs: list[Path]) -> Path | None:
    for d in dirs:
        for ext in (".yaml", ".yml"):
            p = d / f"{profile_id}{ext}"
            if p.is_file():
                return p
    return None


def list_profiles(dirs: list[Path]) -> list[tuple[str, str, Path]]:
    out, seen = [], set()
    for d in dirs:
        for p in sorted(d.glob("*.y*ml")):
            doc = yaml.safe_load(p.read_text()) or {}
            pid = doc.get("id", p.stem)
            if pid not in seen:
                seen.add(pid)
                out.append((pid, doc.get("name", ""), p))
    return out


def _value(node):
    return node.get("value") if isinstance(node, dict) else node


@dataclass
class Profile:
    id: str
    name: str
    chain: list[str]
    folder_depth: int | None = None
    files_per_folder: int | None = None
    sample_rate: int | None = None
    bit_depth: int | None = None


def resolve(profile_id: str, dirs: list[Path]) -> Profile:
    """The profile with its `extends:` chain applied (nearest wins)."""
    chain, docs, cur = [], [], profile_id
    while cur:
        if cur in chain:
            raise ValueError(f"profile {profile_id}: extends loop at {cur}")
        chain.append(cur)
        p = find(cur, dirs)
        if p is None:
            if cur in BASE_FACTS:
                docs.append({"_facts": BASE_FACTS[cur]})
                break
            raise FileNotFoundError(f"profile {cur!r} not found in {[str(d) for d in dirs]}")
        doc = yaml.safe_load(p.read_text()) or {}
        docs.append(doc)
        cur = doc.get("extends")
    prof = Profile(profile_id, docs[0].get("name", profile_id), chain)
    for doc in reversed(docs):          # base first, nearest last
        if "_facts" in doc:
            for k, v in doc["_facts"].items():
                setattr(prof, k, v)
            continue
        paths, audio = doc.get("paths") or {}, doc.get("audio") or {}
        for k in ("folder_depth", "files_per_folder"):
            if k in paths:
                setattr(prof, k, _value(paths[k]))
        for k in ("sample_rate", "bit_depth"):
            if k in audio:
                setattr(prof, k, _value(audio[k]))
    return prof
