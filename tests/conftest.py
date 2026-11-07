import io
import json
import struct
import wave
import zipfile
from pathlib import Path

import pytest

FAKE_CLI = Path(__file__).parent / "fake" / "elektroid-cli"


def make_project(path: Path, samples: list[dict], extra: dict | None = None) -> Path:
    """A fake .dt2prj: a zip with manifest.json (and a placeholder sample entry, no audio)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {"Version": 1, "Samples": samples} if samples is not None else {"Version": 1}
    manifest.update(extra or {})
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("manifest.json", json.dumps(manifest))
        z.writestr("project.bin", b"\x00" * 64)
    return path


def make_wav(path: Path, rate: int = 48000, bits: int = 16, frames: int = 480, channels: int = 1) -> Path:
    """A short silent WAV, made at test time (no audio is ever committed)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(bits // 8)
        w.setframerate(rate)
        w.writeframes(b"\x00" * (bits // 8) * channels * frames)
    return path


@pytest.fixture
def fake_device(tmp_path, monkeypatch):
    """A fake device folder for tests/fake/elektroid-cli; returns its root."""
    root = tmp_path / "device"
    (root / "drive").mkdir(parents=True)
    (root / "projects").mkdir()
    monkeypatch.setenv("FAKE_ELEKTROID_ROOT", str(root))
    monkeypatch.delenv("FAKE_ELEKTROID_FAIL", raising=False)
    return root


def add_slot(root: Path, slot: int, name: str, samples: list[dict]) -> None:
    make_project(root / "projects" / f"{slot}.dt2prj", samples)
    (root / "projects" / f"{slot}.name").write_text(name)


def calls(root: Path) -> list[str]:
    log = root / "calls.log"
    return log.read_text().splitlines() if log.exists() else []


@pytest.fixture(autouse=True)
def no_retry_sleep(monkeypatch):
    monkeypatch.setattr("sample_shepherd.sync.elektron.time.sleep", lambda s: None)


@pytest.fixture(autouse=True)
def private_lock_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("SAMPLE_SHEPHERD_LOCK_DIR", str(tmp_path / "locks"))
