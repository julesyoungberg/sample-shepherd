from conftest import make_wav
from sample_shepherd.export import profiles
from sample_shepherd.export.check import check_render, wav_format


def test_bundled_profiles_resolve():
    dirs = profiles.search_dirs()
    p = profiles.resolve("digitakt_2_50_3", dirs)
    assert p.chain == ["digitakt_2_50_3", "digitakt_2_50", "digitakt_2"]
    assert (p.folder_depth, p.files_per_folder, p.sample_rate, p.bit_depth) == (3, 50, 48000, 16)
    g = profiles.resolve("generic_folder_3", dirs)
    assert (g.folder_depth, g.files_per_folder, g.sample_rate, g.bit_depth) == (3, None, 44100, 24)


def test_wav_format(tmp_path):
    assert wav_format(make_wav(tmp_path / "a.wav", 44100, 24)) == (44100, 24)
    (tmp_path / "b.wav").write_bytes(b"nope")
    assert wav_format(tmp_path / "b.wav") is None


def test_check_render(tmp_path):
    prof = profiles.Profile("t", "t", ["t"], folder_depth=2, files_per_folder=2, sample_rate=48000, bit_depth=16)
    r = tmp_path / "r"
    for i in range(3):
        make_wav(r / "KICKS" / "hard" / f"k{i}.wav")          # 3 files > 2
    make_wav(r / "SNARES" / "a" / "b" / "s.wav")                # depth 3 > 2
    make_wav(r / "HATS" / "x" / "h.wav", rate=44100, bits=24)   # wrong format
    stats, issues = check_render(r, prof)
    assert stats["files"] == 5
    probs = sorted(i.problem for i in issues)
    assert probs == ["24-bit, profile wants 16", "3 files, profile allows 2",
                     "3 folder levels, profile allows 2", "44100 Hz, profile wants 48000"]
