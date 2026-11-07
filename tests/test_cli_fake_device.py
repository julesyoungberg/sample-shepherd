"""End to end through the CLI, against tests/fake/elektroid-cli (no real device)."""
import pytest

from conftest import FAKE_CLI, add_slot, calls, make_wav
from sample_shepherd.cli import main
from sample_shepherd.util import read_csv


@pytest.fixture
def run(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.delenv("SAMPLE_SHEPHERD_CONFIG", raising=False)

    def _run(*args):
        code = main(["--elektroid-cli", str(FAKE_CLI), "--work-dir", str(tmp_path / "work"), *args])
        out = capsys.readouterr()
        return code, out.out + out.err
    return _run


@pytest.fixture
def world(tmp_path, fake_device):
    """A device holding an old kick (used by a project) and an unused one, plus a render."""
    drive = fake_device / "drive"
    (drive / "01_KICKS" / "hard").mkdir(parents=True)
    (drive / "01_KICKS" / "hard" / "USED KICK").write_bytes(b"u" * 100)
    (drive / "01_KICKS" / "hard" / "OLD KICK").write_bytes(b"o" * 100)
    (drive / "factory").mkdir()
    (drive / "factory" / "BD").write_bytes(b"f" * 100)
    add_slot(fake_device, 1, "SONG A", [{"FileName": "Samples/01_KICKS/hard/USED KICK.wav", "FileSize": 100, "Hash": 1}])
    add_slot(fake_device, 2, "SONG B", [{"FileName": "Samples/factory/BD.wav", "FileSize": 100, "Hash": 2}])
    render = tmp_path / "render"
    make_wav(render / "01_KICKS" / "hard" / "BD 01.wav")
    make_wav(render / "01_KICKS" / "soft" / "BD 02.wav")
    make_wav(render / "02_SNARES" / "SD 01.wav")
    return render


def test_device_ls_and_info(run, fake_device):
    code, out = run("device", "ls")
    assert code == 0 and "1: Elektron Digitakt II (42)" in out
    code, out = run("device", "info")
    assert "filesystems: data, preset-takt-ii, project, sample, raw" in out


def test_full_flow(run, world, fake_device, tmp_path):
    w = tmp_path / "work"
    # listing (dry run makes one ls call, writes nothing)
    code, out = run("device", "listing", "--out", str(w / "listing.csv"), "--dry-run")
    assert code == 0 and not (w / "listing.csv").exists()
    code, out = run("device", "listing", "--out", str(w / "listing.csv"))
    assert code == 0, out
    paths = [r["path"] for r in read_csv(w / "listing.csv")]
    assert paths == ["/01_KICKS/hard/OLD KICK", "/01_KICKS/hard/USED KICK", "/factory/BD"]

    # backup: dry run writes nothing; real run makes one folder per slot
    code, out = run("projects", "backup", "--out", str(w / "backups"), "--dry-run")
    assert code == 0 and "to back up: 2" in out and not (w / "backups").exists()
    code, out = run("projects", "backup", "--out", str(w / "backups"))
    assert code == 0, out
    assert (w / "backups" / "slot-0001" / "SONG A.dt2prj").is_file()
    assert (w / "backups" / "slot-0002" / "SONG B.dt2prj").is_file()
    assert len(read_csv(w / "backups" / "backup-index.csv")) == 2
    # a second run backs up nothing new
    code, out = run("projects", "backup", "--out", str(w / "backups"))
    assert "already backed up" in out and "to back up: 0" in out

    code, out = run("projects", "used", "--backups", str(w / "backups"), "--out", str(w / "used.csv"))
    assert code == 0 and "2 project files (2 of 2 slots) use 2 distinct samples" in out

    code, out = run("plan", "--listing", str(w / "listing.csv"), "--used", str(w / "used.csv"),
                    "--export", str(world), "--folders", "01_KICKS", "--prune", "--out", str(w / "plan.csv"))
    assert code == 0, out
    plan = {(r["action"], r["device_path"]) for r in read_csv(w / "plan.csv")}
    assert plan == {("upload", "/01_KICKS/hard/BD 01"), ("upload", "/01_KICKS/soft/BD 02"),
                    ("delete", "/01_KICKS/hard/OLD KICK"), ("keep-used", "/01_KICKS/hard/USED KICK")}

    # sync dry run: no device calls at all
    n = len(calls(fake_device))
    code, out = run("sync", "--plan", str(w / "plan.csv"), "--dry-run")
    assert code == 0 and len(calls(fake_device)) == n

    # deletes without --yes: refused before touching the device
    code, out = run("sync", "--plan", str(w / "plan.csv"), "--used", str(w / "used.csv"))
    assert code == 2 and "--yes" in out and len(calls(fake_device)) == n

    code, out = run("sync", "--plan", str(w / "plan.csv"), "--used", str(w / "used.csv"), "--yes")
    assert code == 0, out
    drive = fake_device / "drive"
    assert (drive / "01_KICKS" / "hard" / "BD 01").is_file()
    assert (drive / "01_KICKS" / "soft" / "BD 02").is_file()
    assert not (drive / "01_KICKS" / "hard" / "OLD KICK").exists()
    assert (drive / "01_KICKS" / "hard" / "USED KICK").is_file()
    assert (drive / "factory" / "BD").is_file()
    assert not (drive / "02_SNARES").exists()

    # rerun: everything is in the log, nothing is sent again
    n = len(calls(fake_device))
    code, out = run("sync", "--plan", str(w / "plan.csv"), "--used", str(w / "used.csv"), "--yes")
    assert code == 0 and len(calls(fake_device)) == n


def test_failed_upload_resumes_and_holds_deletes(run, world, fake_device, tmp_path, monkeypatch):
    w = tmp_path / "work"
    run("device", "listing", "--out", str(w / "listing.csv"))
    run("projects", "backup", "--out", str(w / "backups"))
    run("projects", "used", "--backups", str(w / "backups"), "--out", str(w / "used.csv"))
    run("plan", "--listing", str(w / "listing.csv"), "--used", str(w / "used.csv"), "--export", str(world),
        "--folders", "01_KICKS", "--prune", "--out", str(w / "plan.csv"))

    monkeypatch.setenv("FAKE_ELEKTROID_FAIL", "BD 02")
    code, out = run("sync", "--plan", str(w / "plan.csv"), "--used", str(w / "used.csv"), "--yes")
    assert code == 1 and "deletes skipped" in out
    drive = fake_device / "drive"
    assert (drive / "01_KICKS" / "hard" / "BD 01").is_file()
    assert (drive / "01_KICKS" / "hard" / "OLD KICK").is_file()      # held back

    monkeypatch.delenv("FAKE_ELEKTROID_FAIL")
    code, out = run("sync", "--plan", str(w / "plan.csv"), "--used", str(w / "used.csv"), "--yes")
    assert code == 0, out
    assert "1 to do" in out                                            # only BD 02 again
    assert (drive / "01_KICKS" / "soft" / "BD 02").is_file()
    assert not (drive / "01_KICKS" / "hard" / "OLD KICK").exists()


def test_sync_never_overwrites(run, world, fake_device, tmp_path):
    w = tmp_path / "work"
    run("device", "listing", "--out", str(w / "listing.csv"))
    run("plan", "--listing", str(w / "listing.csv"), "--export", str(world), "--out", str(w / "plan.csv"))
    # the file appears on the device after the listing was taken
    (fake_device / "drive" / "02_SNARES").mkdir()
    (fake_device / "drive" / "02_SNARES" / "SD 01").write_bytes(b"theirs")
    code, out = run("sync", "--plan", str(w / "plan.csv"))
    assert code == 0, out
    assert (fake_device / "drive" / "02_SNARES" / "SD 01").read_bytes() == b"theirs"
    log = read_csv(w / "plan-log.csv")
    assert {r["result"] for r in log if r["device_path"] == "/02_SNARES/SD 01"} == {"skipped-exists"}


def test_plan_refuses_prune_without_used(run, world, fake_device, tmp_path):
    w = tmp_path / "work"
    run("device", "listing", "--out", str(w / "listing.csv"))
    code, out = run("plan", "--listing", str(w / "listing.csv"), "--export", str(world), "--prune",
                    "--out", str(w / "plan.csv"))
    assert code == 2 and "--used" in out and not (w / "plan.csv").exists()


def test_missing_elektroid_is_a_clear_error(run, monkeypatch, tmp_path):
    code = main(["--elektroid-cli", str(tmp_path / "nope"), "--work-dir", str(tmp_path), "device", "ls"])
    assert code == 3


def test_listing_backup_and_used_only_read_the_device(run, world, fake_device, tmp_path):
    w = tmp_path / "work"
    run("device", "listing", "--out", str(w / "listing.csv"))
    run("projects", "backup", "--out", str(w / "backups"))
    run("projects", "used", "--backups", str(w / "backups"), "--out", str(w / "used.csv"))
    ops = {c.split()[0] for c in calls(fake_device)}
    assert ops <= {"elektron:sample:ls", "elektron:project:ls", "elektron:project:dl"}


def test_export_render_and_install_dry_runs(run, tmp_path):
    code, out = run("export", "render", "digitakt_2_50_3", "--from", "m", "--out", "o", "--dry-run")
    assert code == 0 and "render digitakt_2_50_3 --from m --out o" in out
    code, out = run("export", "render", "no_such_profile", "--dry-run")
    assert code == 2
    code, out = run("organize", "install-fourier", "--dir", str(tmp_path / "f"), "--dry-run")
    assert code == 0 and "git -C" in out and "0008-" in out and not (tmp_path / "f").exists()


def test_export_check_cli(run, tmp_path):
    make_wav(tmp_path / "r" / "KICKS" / "a" / "k.wav")
    code, out = run("export", "check", str(tmp_path / "r"), "--profile", "digitakt_2_50_3")
    assert code == 0 and "OK" in out
    make_wav(tmp_path / "r" / "KICKS" / "a" / "bad.wav", rate=44100)
    code, out = run("export", "check", str(tmp_path / "r"), "--profile", "digitakt_2_50_3")
    assert code == 1 and "44100 Hz" in out


def test_interrupted_backup_is_redone(run, world, fake_device, tmp_path, monkeypatch):
    w = tmp_path / "work"
    monkeypatch.setenv("FAKE_ELEKTROID_FAIL", "SONG B")
    code, out = run("projects", "backup", "--out", str(w / "b"))
    assert code == 3
    assert (w / "b" / "slot-0001" / "SONG A.dt2prj").is_file()
    assert not (w / "b" / "slot-0002").exists()          # the half file stays in slot-0002.part
    monkeypatch.delenv("FAKE_ELEKTROID_FAIL")
    code, out = run("projects", "backup", "--out", str(w / "b"))
    assert code == 0 and "to back up: 1" in out
    assert (w / "b" / "slot-0002" / "SONG B.dt2prj").is_file() and not (w / "b" / "slot-0002.part").exists()
    assert [r["slot"] for r in read_csv(w / "b" / "backup-index.csv")] == ["1", "2"]


def test_used_refuses_an_incomplete_backup(run, world, fake_device, tmp_path, monkeypatch):
    w = tmp_path / "work"
    used = ["projects", "used", "--backups", str(w / "b"), "--out", str(w / "used.csv")]
    # one slot failed: its half download sits in slot-0002.part
    monkeypatch.setenv("FAKE_ELEKTROID_FAIL", "SONG B")
    run("projects", "backup", "--out", str(w / "b"))
    monkeypatch.delenv("FAKE_ELEKTROID_FAIL")
    code, out = run(*used)
    assert code == 2 and "interrupted download: slot-0002.part" in out and "slot 2 (SONG B) has no backup" in out
    assert not (w / "used.csv").exists()
    code, out = run(*used, "--allow-partial")
    assert code == 0 and "1 of 2 slots" in out

    # a folder with no slots.csv (e.g. backups made by hand) can't be shown complete
    (w / "b" / "slots.csv").unlink()
    code, out = run(*used)
    assert code == 2 and "no slots.csv" in out


def test_read_only_device_commands_dry_run_without_contacting_it(run, world, fake_device):
    for args, shown in [(("device", "ls"), " ld"), (("device", "info"), " info 1"),
                        (("projects", "ls"), " elektron:project:ls 1:/")]:
        code, out = run(*args, "--dry-run")
        assert code == 0 and "would run:" in out and shown in out, out
    assert calls(fake_device) == []


def test_config_init(run, tmp_path):
    target = tmp_path / "xdg" / "sample-shepherd" / "config.toml"
    code, out = run("config", "init", "--dry-run")
    assert code == 0 and str(target) in out and not target.exists()
    code, out = run("config", "init")
    assert code == 0 and target.is_file()
    code, out = run("config", "show")
    assert str(target) in out and "elektroid-cli" in out
    code, out = run("config", "init")
    assert code == 2 and "already exists" in out
