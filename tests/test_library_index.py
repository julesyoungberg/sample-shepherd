import os
import sqlite3

import pytest

from conftest import make_wav
from sample_shepherd.cli import main
from sample_shepherd.organize import library


def rows(db):
    with sqlite3.connect(db) as con:
        con.row_factory = sqlite3.Row
        return {r["path"]: dict(r) for r in con.execute("SELECT * FROM samples")}


def snapshot(root):
    return {p: (p.stat().st_mtime_ns, p.read_bytes()) for p in root.rglob("*") if p.is_file()}


def test_index_reads_the_master_and_updates_incrementally(tmp_path):
    master = tmp_path / "master"
    kick = make_wav(master / "DRUMS/01_KICKS/punchy/Kick 1.wav", frames=24000)
    make_wav(master / "PADS/warm/Pad.wav", rate=44100, frames=44100, channels=2)
    hat = make_wav(master / "HATS/Hat.wav")
    (master / "notes.txt").write_text("not audio")
    db = tmp_path / "app" / "library.sqlite"
    before = snapshot(master)

    assert library.index(master, db) == {"added": 3, "updated": 0, "unchanged": 0, "removed": 0}
    got = rows(db)
    k = got["DRUMS/01_KICKS/punchy/Kick 1.wav"]
    assert (k["folder"], k["category"], k["duration"], k["sample_rate"], k["channels"]) == \
        ("DRUMS/01_KICKS/punchy", "KICKS", 0.5, 48000, 1)
    assert k["size"] == kick.stat().st_size and len(k["sha256"]) == 64 and k["rating"] is None
    p = got["PADS/warm/Pad.wav"]
    assert (p["category"], p["duration"], p["sample_rate"], p["channels"]) == ("PADS", 1.0, 44100, 2)

    # Unchanged files are skipped by size and mtime; a changed one is read again, a gone one dropped.
    make_wav(kick, frames=48000)
    os.utime(kick, ns=(1, 1))
    hat.unlink()
    assert library.index(master, db) == {"added": 0, "updated": 1, "unchanged": 1, "removed": 1}
    got = rows(db)
    assert set(got) == {"DRUMS/01_KICKS/punchy/Kick 1.wav", "PADS/warm/Pad.wav"}
    assert got["DRUMS/01_KICKS/punchy/Kick 1.wav"]["duration"] == 1.0

    del before[hat]
    assert {p: v for p, v in snapshot(master).items() if p != kick} == {p: v for p, v in before.items() if p != kick}


def test_index_refuses_a_db_inside_the_master_or_another_masters_db(tmp_path):
    master = tmp_path / "master"
    make_wav(master / "KICKS/K.wav")
    with pytest.raises(ValueError, match="inside the library"):
        library.index(master, master / "cache" / "library.sqlite")
    assert not (master / "cache").exists()

    db = tmp_path / "library.sqlite"
    library.index(master, db)
    other = tmp_path / "other"
    make_wav(other / "SNARES/S.wav")
    with pytest.raises(ValueError, match="already indexes"):
        library.index(other, db)


def test_cli_library_index_dry_run_writes_nothing(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.delenv("SAMPLE_SHEPHERD_CONFIG", raising=False)
    master = tmp_path / "master"
    make_wav(master / "KICKS/K.wav")
    db = tmp_path / "library.sqlite"

    assert main(["library", "index", str(master), "--db", str(db), "--dry-run"]) == 0
    assert "1 to add" in capsys.readouterr().out
    assert not db.exists()

    assert main(["library", "index", str(master), "--db", str(db)]) == 0
    assert "1 added" in capsys.readouterr().out
    assert len(rows(db)) == 1
