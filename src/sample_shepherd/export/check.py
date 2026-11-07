"""Check a rendered folder against its profile: files per folder, folder depth, and each
WAV's sample rate and bit depth. Reads only."""
from __future__ import annotations

import os
import struct
from dataclasses import dataclass
from pathlib import Path

from sample_shepherd.export.profiles import Profile

AUDIO = (".wav", ".aif", ".aiff", ".flac")


@dataclass
class Issue:
    path: str
    problem: str


def wav_format(path: Path) -> tuple[int, int] | None:
    """(sample rate, bits per sample) from a WAV's fmt chunk, or None if it isn't readable."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(12)
            if len(head) < 12 or head[:4] not in (b"RIFF", b"RF64") or head[8:12] != b"WAVE":
                return None
            while True:
                ch = fh.read(8)
                if len(ch) < 8:
                    return None
                cid, size = ch[:4], struct.unpack("<I", ch[4:])[0]
                if cid == b"fmt ":
                    fmt = fh.read(16)
                    _, _, rate, _, _, bits = struct.unpack("<HHIIHH", fmt)
                    return rate, bits
                fh.seek(size + (size & 1), 1)
    except OSError:
        return None


# Elektron devices keep sample names to 32 characters (ELEKTRON_NAME_MAX_LEN in Elektroid).
ELEKTRON_NAME_MAX = 32


def default_name_limit(prof: Profile) -> int | None:
    return ELEKTRON_NAME_MAX if any(p.startswith(("digitakt", "rytm", "model_samples")) for p in prof.chain) else None


def check_render(root: Path, prof: Profile, max_issues: int = 10_000, max_name_length: int | None = None) -> tuple[dict[str, int], list[Issue]]:
    root = Path(root)
    issues: list[Issue] = []
    stats = {"files": 0, "folders": 0, "wav_checked": 0}
    for dp, _, fs in os.walk(root):
        audio = [f for f in fs if f.lower().endswith(AUDIO) and not f.startswith(".")]
        if not audio:
            continue
        rel = Path(dp).relative_to(root)
        stats["folders"] += 1
        stats["files"] += len(audio)
        depth = len(rel.parts)
        if prof.folder_depth is not None and depth > prof.folder_depth:
            issues.append(Issue(rel.as_posix(), f"{depth} folder levels, profile allows {prof.folder_depth}"))
        if prof.files_per_folder and len(audio) > prof.files_per_folder:
            issues.append(Issue(rel.as_posix(), f"{len(audio)} files, profile allows {prof.files_per_folder}"))
        if max_name_length:
            seen: dict[str, str] = {}
            for f in sorted(audio):
                stem = Path(f).stem
                p = (rel / f).as_posix()
                if len(stem) > max_name_length:
                    issues.append(Issue(p, f"name is {len(stem)} characters; the device keeps {max_name_length}"))
                key = stem[:max_name_length].lower()
                if key in seen:
                    issues.append(Issue(p, f"same first {max_name_length} characters as {seen[key]}"))
                seen.setdefault(key, f)
        for f in audio:
            if not f.lower().endswith(".wav"):
                continue
            fmt = wav_format(Path(dp) / f)
            stats["wav_checked"] += 1
            p = (rel / f).as_posix()
            if fmt is None:
                issues.append(Issue(p, "not a readable WAV"))
                continue
            rate, bits = fmt
            if prof.sample_rate and rate != prof.sample_rate:
                issues.append(Issue(p, f"{rate} Hz, profile wants {prof.sample_rate}"))
            if prof.bit_depth and bits != prof.bit_depth:
                issues.append(Issue(p, f"{bits}-bit, profile wants {prof.bit_depth}"))
        if len(issues) >= max_issues:
            break
    return stats, issues
