import pytest

from conftest import make_project
from sample_shepherd.sync import projects


def test_hash_decimal_to_hex():
    # The device lists a sample's hash in hex; a project manifest stores it in decimal.
    assert projects.hash_hex(3735928559) == "deadbeef"
    assert projects.hash_hex("196879037") == "0bbc22bd"
    assert projects.hash_hex("0x0BBC22BD") == "0bbc22bd"
    assert projects.hash_hex(None) is None


def test_device_path():
    assert projects.device_path("Samples/01_KICKS/hard/BD 01.wav") == "/01_KICKS/hard/BD 01"
    assert projects.device_path("Samples/factory/BD 01.WAV") == "/factory/BD 01"
    assert projects.device_path("drums/clap") == "/drums/clap"


def test_read_manifest(tmp_path):
    f = make_project(tmp_path / "a.dt2prj", [
        {"FileName": "Samples/factory/BD 01.wav", "FileSize": 1000, "Hash": 3735928559},
        {"fileName": "Samples/mine/vox.wav", "fileSize": "2000", "hash": "1"},
    ])
    got = projects.read_manifest(f)
    assert got == [projects.UsedSample("/factory/BD 01", 1000, "deadbeef"),
                   projects.UsedSample("/mine/vox", 2000, "00000001")]


def test_missing_samples_list_is_an_error_not_empty(tmp_path):
    f = make_project(tmp_path / "a.dt2prj", None)
    with pytest.raises(ValueError, match="no Samples list"):
        projects.read_manifest(f)


def test_not_a_zip(tmp_path):
    f = tmp_path / "bad.dt2prj"
    f.write_bytes(b"not a zip")
    with pytest.raises(ValueError, match="not a zip"):
        projects.read_manifest(f)


def test_used_samples_across_projects(tmp_path):
    shared = {"FileName": "Samples/kit/BD.wav", "FileSize": 10, "Hash": 1}
    make_project(tmp_path / "slot-0001" / "SONG A.dt2prj", [shared])
    make_project(tmp_path / "slot-0002" / "SONG B.dt2prj", [shared, {"FileName": "Samples/kit/SD.wav", "FileSize": 20, "Hash": 2}])
    used, files = projects.used_samples(tmp_path)
    assert len(files) == 2
    rows = projects.used_rows(used)
    assert rows[0][:3] == ["/kit/BD", 10, "00000001"]
    assert rows[0][3] == "slot-0001/SONG A.dt2prj; slot-0002/SONG B.dt2prj"
    assert rows[1][0] == "/kit/SD"


def test_slot_folder():
    assert projects.slot_folder("7") == "slot-0007"


def test_entry_without_file_name(tmp_path):
    f = make_project(tmp_path / "a.dt2prj", [{"FileSize": 10, "Hash": 3735928559}])
    assert projects.read_manifest(f) == [projects.UsedSample("", 10, "deadbeef")]   # still protects by hash
    f = make_project(tmp_path / "b.dt2prj", [{"FileSize": 10}])
    with pytest.raises(ValueError, match="neither FileName nor Hash"):
        projects.read_manifest(f)
