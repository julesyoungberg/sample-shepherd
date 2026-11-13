"""Small shared helpers: sizes, durations, estimates, CSV files, WAV headers, the device lock."""
from __future__ import annotations

import contextlib
import csv
import os
import re
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence

UNITS = {"B": 1, "KiB": 1024, "MiB": 1024**2, "GiB": 1024**3, "TiB": 1024**4}
_SIZE = re.compile(r"^([\d.]+)\s*([A-Za-z]+)$")


def parse_human_size(text: str) -> int:
    """'4.05MiB' -> bytes. elektroid-cli prints 4 significant digits, so this is approximate."""
    m = _SIZE.match(text.strip())
    if not m or m.group(2) not in UNITS:
        raise ValueError(f"not a size: {text!r}")
    return round(float(m.group(1)) * UNITS[m.group(2)])


def fmt_bytes(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if abs(n) < 1000 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.2f} {unit}"
        n /= 1000
    return f"{n:.2f} GB"


def fmt_duration(seconds: float) -> str:
    seconds = max(0, round(seconds))
    if seconds < 90:
        return f"{seconds} s"
    if seconds < 90 * 60:
        return f"{seconds / 60:.0f} min"
    return f"{seconds / 3600:.1f} h"


def estimate_seconds(total_bytes: int, calls: int, bytes_per_second: float, seconds_per_call: float) -> float:
    return total_bytes / bytes_per_second + calls * seconds_per_call


#: what counts as an audio file, by extension
AUDIO = (".wav", ".aif", ".aiff", ".flac")


@dataclass
class WavInfo:
    rate: int
    bits: int
    channels: int
    seconds: float | None      # None when the header has no data chunk size to go by


def wav_info(path: Path) -> WavInfo | None:
    """A WAV's format from its header (fmt and data chunks), or None if it isn't readable.
    Reads only the chunk headers, not the audio."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(12)
            if len(head) < 12 or head[:4] not in (b"RIFF", b"RF64") or head[8:12] != b"WAVE":
                return None
            fmt = None
            while True:
                ch = fh.read(8)
                if len(ch) < 8:
                    break
                cid, size = ch[:4], struct.unpack("<I", ch[4:])[0]
                if cid == b"fmt ":
                    raw = fh.read(16)
                    if len(raw) < 16:
                        return None
                    _, channels, rate, byte_rate, _, bits = struct.unpack("<HHIIHH", raw)
                    fmt = (channels, rate, byte_rate, bits)
                    fh.seek(size - 16 + (size & 1), 1)
                elif cid == b"data" and fmt:
                    # RF64 keeps the real size elsewhere and writes 0xFFFFFFFF here
                    known = fmt[2] > 0 and size != 0xFFFFFFFF
                    return WavInfo(fmt[1], fmt[3], fmt[0], size / fmt[2] if known else None)
                else:
                    fh.seek(size + (size & 1), 1)
            return WavInfo(fmt[1], fmt[3], fmt[0], None) if fmt else None
    except (OSError, struct.error):
        return None


def read_csv(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, header: Sequence[str], rows: Iterable[Sequence]) -> None:
    """Write via a temporary file and rename, so a crash never leaves half a CSV."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    with open(tmp, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    os.replace(tmp, path)


class AppendLog:
    """An append-only CSV log, flushed after every row, so a run can resume after any stop."""

    def __init__(self, path: Path, header: Sequence[str]):
        self.path = Path(path)
        self.header = list(header)
        self.rows = read_csv(self.path) if self.path.exists() else []
        self._fh = None

    def __enter__(self) -> "AppendLog":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        new = not self.path.exists() or self.path.stat().st_size == 0
        self._fh = open(self.path, "a", newline="", encoding="utf-8")
        self._w = csv.writer(self._fh)
        if new:
            self._w.writerow(self.header)
        return self

    def write(self, *values) -> None:
        self._w.writerow(values)
        self._fh.flush()
        self.rows.append(dict(zip(self.header, (str(v) for v in values))))

    def __exit__(self, *exc) -> None:
        self._fh.close()


class DeviceBusy(RuntimeError):
    pass


class StopRequested(Exception):
    """The user asked a long command to stop (the app's Stop button). Logged work is kept."""


@contextlib.contextmanager
def device_lock(lock_file: Path) -> Iterator[None]:
    """Only one process may talk to a device at a time: concurrent MIDI access can corrupt a
    transfer. Every sample-shepherd command that talks to a device holds this lock. It can't
    see other tools (Elektron Transfer, a hand-run elektroid-cli), so don't run those alongside."""
    import fcntl

    lock_file = Path(lock_file)
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    fh = open(lock_file, "a+")
    try:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            fh.seek(0)
            raise DeviceBusy(f"another sample-shepherd process is using the device "
                             f"(lock: {lock_file}; holder: {fh.read().strip() or 'unknown'})") from None
        fh.seek(0)
        fh.truncate()
        fh.write(f"pid {os.getpid()}\n")
        fh.flush()
        yield
    finally:
        fh.close()
