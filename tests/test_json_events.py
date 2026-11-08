"""The --json event stream the desktop app reads: stdout carries only schema-valid events."""
import json
import os
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest

from conftest import FAKE_CLI
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


def test_errors_become_error_events(run_json, tmp_path):
    code, evs, err = run_json("export", "check", str(tmp_path / "no-render"), "--profile", "nope")
    assert code == 2
    assert [e["type"] for e in evs] == ["start", "error"]
    assert evs[-1]["code"] == "user_error" and "nope" in evs[-1]["msg"]


def test_human_output_goes_to_stderr(run_json):
    code, evs, err = run_json("config", "show")
    assert code == 0 and "work_dir:" in err
    assert evs[0] == {"v": 1, "type": "start", "cmd": "config show", "dry_run": False}
