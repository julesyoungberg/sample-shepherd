"""The --json event stream the desktop app reads: stdout carries only schema-valid events."""
import json
import os
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest

from conftest import FAKE_CLI, make_wav
from sample_shepherd import events
from sample_shepherd.cli import main

SCHEMA = json.loads(events.schema_path().read_text(encoding="utf-8"))


@pytest.fixture
def run_json(tmp_path, monkeypatch, capfd):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.delenv("SAMPLE_SHEPHERD_CONFIG", raising=False)

    def _run(*args):
        code = main(["--json", "--elektroid-cli", str(FAKE_CLI), *args])
        out = capfd.readouterr()
        evs = [json.loads(line) for line in out.out.splitlines()]
        for ev in evs:
            jsonschema.validate(ev, SCHEMA)
        return code, evs, out.err
    return _run


def test_stray_output_cannot_corrupt_the_stream(capfd):
    with events.json_mode() as ev:
        ev.emit("start", cmd="test", dry_run=False)
        print("a stray print")
        subprocess.run([sys.executable, "-c", "print('a child process print')"], check=True)
        os.write(1, b"raw write to fd 1\n")
        ev.emit("result", ok=True, exit=0, summary={})
    out = capfd.readouterr()
    assert [json.loads(line)["type"] for line in out.out.splitlines()] == ["start", "result"]
    assert "a stray print" in out.err and "a child process print" in out.err and "raw write" in out.err
    print("stdout is back")
    assert capfd.readouterr().out == "stdout is back\n"


def test_tools_reports_each_tool(run_json, tmp_path):
    fourier = tmp_path / "bin" / "fourier"
    fourier.parent.mkdir()
    fourier.write_text("#!/bin/sh\necho 'fourier 0.1.2'\n")
    fourier.chmod(0o755)
    (tmp_path / "sample-shepherd.toml").write_text(f'[fourier]\ncommand = "{fourier}"\n')
    code, evs, err = run_json("tools")
    assert code == 0, err
    assert [e["type"] for e in evs] == ["start", "row", "row", "result"]
    tools = {e["name"]: e for e in evs if e["type"] == "row"}
    assert tools["fourier"]["found"] and tools["fourier"]["version"] == "fourier 0.1.2"
    assert tools["elektroid-cli"]["found"] and tools["elektroid-cli"]["path"] == str(FAKE_CLI)
    assert "sync" in tools["elektroid-cli"]["enables"]
    assert evs[-1] == {"v": 1, "type": "result", "ok": True, "exit": 0, "summary": {"missing": []}}


def test_tools_names_what_is_missing(run_json, tmp_path):
    (tmp_path / "sample-shepherd.toml").write_text('[fourier]\ncommand = "/nowhere/fourier"\n')
    code, evs, _ = run_json("tools")
    row = next(e for e in evs if e.get("name") == "fourier")
    assert code == 0 and not row["found"] and row["path"] is None and row["version"] is None
    assert evs[-1]["summary"] == {"missing": ["fourier"]}


def test_plan_streams_each_row_and_totals(run_json, tmp_path):
    make_wav(tmp_path / "render" / "01_KICKS" / "BD 01.wav")
    make_wav(tmp_path / "render" / "01_KICKS" / "BD 02.wav")
    (tmp_path / "listing.csv").write_text("path,size,hash\n/01_KICKS/BD 01,1000,0000000a\n/01_KICKS/OLD,500,0000000b\n")
    (tmp_path / "used.csv").write_text("path,size,hash\n/elsewhere/X,10,0000000c\n")
    code, evs, err = run_json("plan", "--listing", "listing.csv", "--export", "render", "--used", "used.csv",
                              "--prune", "--out", "plan.csv", "--dry-run")
    assert code == 0, err
    rows = [e for e in evs if e["type"] == "row"]
    assert [(r["action"], r["device_path"]) for r in rows] == [
        ("upload", "/01_KICKS/BD 02"), ("delete", "/01_KICKS/OLD"), ("skip-exists", "/01_KICKS/BD 01")]
    assert rows[0]["local_path"].endswith("BD 02.wav") and rows[1]["hash"] == "0000000b"
    summary = evs[-1]["summary"]
    assert summary["upload"] == 1 and summary["delete"] == 1 and summary["skip-exists"] == 1
    assert summary["delete_bytes"] == 500 and summary["est_seconds"] > 0
    assert summary["out"] is None and not (tmp_path / "plan.csv").exists()


def test_errors_become_error_events(run_json, tmp_path):
    code, evs, err = run_json("export", "check", str(tmp_path / "no-render"), "--profile", "nope")
    assert code == 2
    assert [e["type"] for e in evs] == ["start", "error"]
    assert evs[-1]["code"] == "user_error" and "nope" in evs[-1]["msg"]


def test_human_output_goes_to_stderr(run_json):
    code, evs, err = run_json("config", "show")
    assert code == 0 and "work_dir:" in err
    assert evs[0] == {"v": 1, "type": "start", "cmd": "config show", "dry_run": False}


def test_a_crash_still_ends_the_stream_with_an_error(monkeypatch, capfd):
    def boom(cfg, a):
        raise RuntimeError("a bug")
    monkeypatch.setattr("sample_shepherd.cli.cmd_tools", boom)
    with pytest.raises(RuntimeError):
        main(["--json", "tools"])
    evs = [json.loads(line) for line in capfd.readouterr().out.splitlines()]
    jsonschema.validate(evs[-1], SCHEMA)
    assert evs[-1]["code"] == "internal" and "a bug" in evs[-1]["msg"]


def test_a_closed_reader_ends_quietly(tmp_path):
    read_end, write_end = os.pipe()
    os.close(read_end)          # the app has gone away before the CLI writes anything
    env = {**os.environ, "XDG_CONFIG_HOME": str(tmp_path)}
    env.pop("SAMPLE_SHEPHERD_CONFIG", None)
    r = subprocess.run([sys.executable, "-m", "sample_shepherd", "--json", "tools"], stdout=write_end,
                       stderr=subprocess.PIPE, text=True, cwd=tmp_path, env=env)
    os.close(write_end)
    assert r.returncode == 0 and "Traceback" not in r.stderr and "BrokenPipe" not in r.stderr


def test_sync_reports_progress_and_stops_between_files_when_asked(tmp_path, fake_device):
    """The app's view of a sync: progress after each file, and a stop line on stdin ends the
    run after the file in flight, through the usual "stopped, rerun to resume" exit."""
    from conftest import make_wav
    lines = ["action,device_path,local_path,size,reason,hash"]
    for i in range(6):
        wav = make_wav(tmp_path / "export" / f"BD {i}.wav")
        lines.append(f"upload,/KICKS/BD {i},{wav},{wav.stat().st_size},new,")
    (tmp_path / "plan.csv").write_text("\n".join(lines) + "\n")
    env = {**os.environ, "XDG_CONFIG_HOME": str(tmp_path / "xdg")}
    env.pop("SAMPLE_SHEPHERD_CONFIG", None)
    p = subprocess.Popen([sys.executable, "-m", "sample_shepherd", "--json", "--elektroid-cli", str(FAKE_CLI),
                          "sync", "--plan", str(tmp_path / "plan.csv")],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                         cwd=tmp_path, env=env)
    evs = []
    for line in p.stdout:
        evs.append(json.loads(line))
        jsonschema.validate(evs[-1], SCHEMA)
        if evs[-1]["type"] == "progress" and evs[-1]["done"] == 1:
            p.stdin.write('{"type": "stop"}\n')
            p.stdin.flush()
    assert p.wait() == 130, p.stderr.read()
    progress = [e for e in evs if e["type"] == "progress"]
    assert progress[0]["total"] == 6 and progress[0]["bytes"] > 0
    assert evs[-1]["type"] == "error" and evs[-1]["code"] == "stopped"
    uploaded = len(list((fake_device / "drive" / "KICKS").iterdir()))
    assert uploaded == progress[-1]["done"] < 6
