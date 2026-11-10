"""sync is the last guard before an irreversible delete, so it re-checks every delete row
the way plan does, even when the plan CSV was hand-edited or is stale."""
import pytest

from sample_shepherd.sync.device import Device, DeviceError, Entry
from sample_shepherd.sync.plan import PlanRow
from sample_shepherd.sync.projects import UsedSample
from sample_shepherd.sync.run import run_sync
from sample_shepherd.util import StopRequested, read_csv


class MemoryDevice(Device):
    def __init__(self, files):
        self.files = dict(files)      # path -> hash
        self.deleted = []

    def list_devices(self): return []
    def ls(self, path):
        pre = path.rstrip("/") + "/"
        names = {p[len(pre):].split("/")[0] for p in self.files if p.startswith(pre)}
        if not names and path != "/":
            raise DeviceError("No such file or directory")
        return [Entry("F", n, 1, None) for n in sorted(names)]
    def mkdir(self, path): pass
    def upload(self, local, dest_dir): raise AssertionError("no uploads here")
    def delete(self, path):
        self.files.pop(path)
        self.deleted.append(path)
    def list_projects(self): return []
    def download_project(self, slot, dest_dir): raise AssertionError


def test_hand_edited_deletes_are_rechecked(tmp_path):
    dev = MemoryDevice({"/!!!RECORDINGS!!!/take1": "00000001", "/old/BD copy": "deadbeef",
                        "/old/no hash": "", "/old/really old": "00000002"})
    rows = [
        PlanRow("delete", "/!!!RECORDINGS!!!/take1", hash="00000001"),   # protected
        PlanRow("delete", "/old/BD copy", hash="DEADBEEF"),             # a used sample's content
        PlanRow("delete", "/old/no hash"),                              # can't be checked
        PlanRow("delete", "/01_kicks/bd 01", hash="00000009"),          # used by path (case aside)
        PlanRow("delete", "/old/really old", hash="00000002"),          # fine
    ]
    used = [UsedSample("/01_KICKS/BD 01", 100, "deadbeef")]
    stats = run_sync(dev, rows, tmp_path / "log.csv", used, do_delete=True, out=lambda m: None,
                     protected=["/!!!RECORDINGS!!!"])
    assert dev.deleted == ["/old/really old"]
    assert stats["refused"] == 4 and stats["deleted"] == 1
    results = {r["device_path"]: r["result"] for r in read_csv(tmp_path / "log.csv")}
    assert results["/!!!RECORDINGS!!!/take1"] == "refused: protected path"
    assert results["/old/BD copy"] == "refused: same content hash as a sample a project uses"
    assert results["/old/no hash"].startswith("refused: no content hash")
    assert results["/01_kicks/bd 01"] == "refused: a project uses it"


class FlakyDevice(MemoryDevice):
    """ls of one existing folder fails (a USB/MIDI hiccup); uploads are recorded."""

    def __init__(self, files, flaky):
        super().__init__(files)
        self.flaky, self.uploaded, self.made = flaky, [], []

    def ls(self, path):
        if path == self.flaky:
            raise DeviceError("timeout")
        return super().ls(path)

    def mkdir(self, path):
        self.made.append(path)

    def upload(self, local, dest_dir):
        self.uploaded.append((local.name, dest_dir))


def test_ls_error_is_a_failure_not_a_missing_folder(tmp_path):
    local = tmp_path / "BD 01.wav"
    local.write_bytes(b"x")
    dev = FlakyDevice({"/KICKS/BD 01": "1"}, flaky="/KICKS")
    rows = [PlanRow("upload", "/KICKS/BD 01", str(local), 1), PlanRow("upload", "/NEW/BD 01", str(local), 1)]
    stats = run_sync(dev, rows, tmp_path / "log.csv", None, do_delete=False, out=lambda m: None)
    assert stats["failed"] == 1 and stats["uploaded"] == 1
    assert dev.made == ["/NEW"]                       # /KICKS exists: never re-made, never uploaded into blind
    assert dev.uploaded == [("BD 01.wav", "/NEW")]


class RecordingDevice(MemoryDevice):
    def __init__(self):
        super().__init__({})
        self.uploaded = []

    def upload(self, local, dest_dir):
        self.uploaded.append(local.name)
        self.files[f"{dest_dir}/{local.stem}"] = "1"


def test_a_stop_request_ends_the_sync_between_files_and_a_rerun_resumes(tmp_path):
    rows = []
    for name in ("BD 01", "BD 02", "BD 03"):
        (tmp_path / f"{name}.wav").write_bytes(b"x")
        rows.append(PlanRow("upload", f"/KICKS/{name}", str(tmp_path / f"{name}.wav"), 1))
    dev = RecordingDevice()
    with pytest.raises(StopRequested):
        run_sync(dev, rows, tmp_path / "log.csv", None, do_delete=False, out=lambda m: None,
                 stop=lambda: len(dev.uploaded) == 1)
    assert dev.uploaded == ["BD 01.wav"]                     # the file in flight finished, no more
    assert [r["result"] for r in read_csv(tmp_path / "log.csv")] == ["ok"]
    stats = run_sync(dev, rows, tmp_path / "log.csv", None, do_delete=False, out=lambda m: None)
    assert dev.uploaded == ["BD 01.wav", "BD 02.wav", "BD 03.wav"] and stats["already_done"] == 1
