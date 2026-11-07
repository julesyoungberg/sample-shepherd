"""Elektron devices through elektroid-cli (github.com/dagargo/elektroid, GPLv3, run as a
separate program). Covers what Elektroid supports: Digitakt I/II, Digitone, Syntakt,
Analog Rytm, Model:Samples and others.

Output formats parsed here come from Elektroid's source (src/elektroid-cli.c and
src/connectors/elektron.c, checked at commit 053d3fd, 2026-11-03):

  ld:               "%d: id: %s; name: %s"
  sample:ls:        "%c %10s %08x %s"                 type, size, hash, name
  project:ls:       "%c %04x %d %d %10s %10s %-32s"   type, ops, valid, metadata, size, slot, name

Older Elektroid releases (and its README) print data/project listings as
"type index perms valid metadata size name"; parse_project_ls reads both.
"""
from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path
from typing import Callable, Sequence

from sample_shepherd.sync.device import Device, DeviceError, DeviceInfo, Entry, ProjectSlot
from sample_shepherd.util import parse_human_size

LD_LINE = re.compile(r"^(\d+): id: (.*?); name: (.*)$")
SAMPLE_LINE = re.compile(r"^([DF])\s+(\S+)\s+([0-9a-fA-F]{8})\s(.*)$")
DATA_LINE_OLD = re.compile(r"^([DF])\s+(-?\d+) ([0-9a-fA-F]{4}) ([01]) ([01])\s+(\S+) (.*)$")
DATA_LINE = re.compile(r"^([DF]) ([0-9a-fA-F]{4}) (\d) (\d) (.{10}) (.{10}) (.*)$")
FS_LINE = re.compile(r"^Filesystems:\s*(.*)$")
INFO_SUFFIX = re.compile(r"\s*\[ .* \]\s*$")

Runner = Callable[[Sequence[str]], "subprocess.CompletedProcess[bytes]"]


def _subprocess_runner(args: Sequence[str]) -> "subprocess.CompletedProcess[bytes]":
    try:
        return subprocess.run(list(args), capture_output=True)
    except FileNotFoundError:
        raise DeviceError(f"elektroid-cli not found: {args[0]!r}. Build it (see README, "
                          f"'Elektroid') and set [elektroid] cli in your config.") from None


def parse_ld(text: str) -> list[DeviceInfo]:
    out = []
    for line in text.splitlines():
        m = LD_LINE.match(line.strip())
        if m:
            out.append(DeviceInfo(m.group(1), m.group(2).strip(), m.group(3).strip()))
    return out


def parse_info(text: str) -> dict[str, object]:
    """`info N` -> {"name": ..., "filesystems": [...], ...}. Filesystems may carry an
    extension list in parentheses, e.g. "project (dt2prj, dtprj)"."""
    out: dict[str, object] = {"filesystems": []}
    for line in text.splitlines():
        m = FS_LINE.match(line.strip())
        if m:
            parts = re.split(r",\s*(?![^()]*\))", m.group(1).strip())
            out["filesystems"] = [re.sub(r"\s*\(.*\)$", "", p).strip() for p in parts if p.strip()]
        elif ":" in line:
            k, _, v = line.partition(":")
            out[k.strip().lower().replace(" ", "_")] = v.strip()
    return out


def parse_sample_ls(text: str) -> list[Entry]:
    out = []
    for line in text.splitlines():
        m = SAMPLE_LINE.match(line)
        if m:
            size = None if m.group(2) == "?B" else parse_human_size(m.group(2))
            out.append(Entry(m.group(1), m.group(4).rstrip(), size, m.group(3).lower()))
    return out


def parse_project_ls(text: str) -> list[ProjectSlot]:
    out = []
    for line in text.splitlines():
        old = DATA_LINE_OLD.match(line)
        if old:
            if old.group(1) == "F":
                size_text = old.group(6)
                out.append(ProjectSlot(old.group(2), INFO_SUFFIX.sub("", old.group(7)).rstrip(),
                                       None if size_text == "?B" else parse_human_size(size_text),
                                       valid=old.group(4) == "1"))
            continue
        m = DATA_LINE.match(line)
        if not m or m.group(1) != "F":
            continue
        size_text, slot = m.group(5).strip(), m.group(6).strip()
        name = INFO_SUFFIX.sub("", m.group(7)).rstrip()
        size = parse_human_size(size_text) if size_text and size_text != "?B" else None
        out.append(ProjectSlot(slot, name, size, valid=m.group(3) == "1"))
    return out


class ElektronDevice(Device):
    project_suffix = ".dt2prj"
    strips_extension = True

    def __init__(self, cli: str = "elektroid-cli", device: str = "1", *,
                 sample_fs: str = "sample", project_fs: str = "project",
                 runner: Runner | None = None, tries: int = 3, sleep=None):
        self.cli, self.device = cli, str(device)
        self.sample_fs, self.project_fs = sample_fs, project_fs
        self.runner = runner or _subprocess_runner
        self.tries, self.sleep = tries, sleep or (lambda s: time.sleep(s))

    def _run(self, *args: str, tries: int | None = None) -> str:
        err = ""
        n = self.tries if tries is None else tries
        for i in range(n):
            r = self.runner([self.cli, *args])
            if r.returncode == 0:
                return r.stdout.decode("utf-8", errors="replace")
            err = r.stderr.decode("utf-8", errors="replace").strip()[-300:]
            if i + 1 < n:
                self.sleep(2 * (i + 1))
        raise DeviceError(f"elektroid-cli {' '.join(args)}: {err or 'failed'}")

    def _p(self, path: str) -> str:
        return f"{self.device}:{path if path.startswith('/') else '/' + path}"

    def list_devices(self) -> list[DeviceInfo]:
        return parse_ld(self._run("ld", tries=1))

    def info(self) -> dict[str, object]:
        return parse_info(self._run("info", self.device, tries=1))

    def ls(self, path: str) -> list[Entry]:
        return parse_sample_ls(self._run(f"elektron:{self.sample_fs}:ls", self._p(path)))

    def mkdir(self, path: str) -> None:
        self._run(f"elektron:{self.sample_fs}:mkdir", self._p(path))

    def upload(self, local: Path, dest_dir: str) -> None:
        self._run(f"elektron:{self.sample_fs}:ul", str(local), self._p(dest_dir))

    def delete(self, path: str) -> None:
        self._run(f"elektron:{self.sample_fs}:rm", self._p(path), tries=1)

    def list_projects(self) -> list[ProjectSlot]:
        return parse_project_ls(self._run(f"elektron:{self.project_fs}:ls", self._p("/")))

    def download_project(self, slot: str, dest_dir: Path) -> Path:
        dest_dir = Path(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)
        before = {p.name for p in dest_dir.iterdir()}
        self._run(f"elektron:{self.project_fs}:dl", self._p(f"/{slot}"), str(dest_dir))
        new = [p for p in dest_dir.iterdir() if p.name not in before and p.is_file()]
        if len(new) != 1:
            raise DeviceError(f"project slot {slot}: expected one downloaded file in {dest_dir}, "
                              f"found {[p.name for p in new]}")
        return new[0]
