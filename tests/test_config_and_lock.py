import pytest

from sample_shepherd import config
from sample_shepherd.util import DeviceBusy, device_lock, parse_human_size


def test_defaults_without_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.delenv(config.ENV_VAR, raising=False)
    cfg = config.load()
    assert cfg.path is None and cfg.work_dir == tmp_path and cfg.elektroid_cli == "elektroid-cli"


def test_file_paths_relative_to_file(tmp_path, monkeypatch):
    f = tmp_path / "conf" / "sample-shepherd.toml"
    f.parent.mkdir()
    f.write_text('''
work_dir = "../work"
[device]
id = 2
[elektroid]
cli = "../vendor/bin/elektroid-cli"
[fourier]
command = "fourier"
env = { FOURIER_HOME = "~/fh" }
[sync]
protected = ["/factory", "/!!!RECORDINGS!!!"]
[transfer]
bytes_per_second = 100000
''')
    monkeypatch.setenv(config.ENV_VAR, str(f))
    cfg = config.load()
    assert cfg.work_dir == tmp_path / "conf" / ".." / "work"
    assert cfg.device_id == "2"
    assert cfg.elektroid_cli.endswith("vendor/bin/elektroid-cli")
    assert cfg.fourier_command == "fourier"
    assert not cfg.fourier_env["FOURIER_HOME"].startswith("~")
    assert cfg.protected[1] == "/!!!RECORDINGS!!!"
    assert cfg.transfer.bytes_per_second == 100000 and cfg.transfer.seconds_per_call == 1.6


def test_unknown_setting_is_an_error(tmp_path):
    f = tmp_path / "c.toml"
    f.write_text("typo = 1\n")
    with pytest.raises(ValueError, match="unknown settings"):
        config.load(str(f))


def test_example_config_parses():
    from pathlib import Path
    cfg = config.load(str(Path(__file__).parents[1] / "examples" / "sample-shepherd.toml"))
    assert cfg.device_backend == "elektron"


def test_device_lock_is_exclusive(tmp_path):
    lock = tmp_path / "x.lock"
    with device_lock(lock):
        # flock locks are per open file, so a second open in the same process conflicts too
        with pytest.raises(DeviceBusy):
            with device_lock(lock):
                pass
    with device_lock(lock):
        pass


def test_parse_human_size():
    assert parse_human_size("512B") == 512
    assert parse_human_size("1.5KiB") == 1536
    with pytest.raises(ValueError):
        parse_human_size("12 parsecs")
