"""The --json event stream: one JSON object per line on stdout, for the desktop app.

Event shapes are in events.schema.json next to this file; the app generates its types from
it. `v` is the schema version, bumped on any breaking change.

In JSON mode stdout carries events and nothing else. `json_mode()` keeps the real stdout as
a private file descriptor for events and points fd 1 (and sys.stdout) at stderr, so a stray
print, a progress bar or a child process (Fourier, PyTorch) can't corrupt the stream.
"""
from __future__ import annotations

import json
import os
import sys
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import IO, Iterator

VERSION = 1


def schema_path() -> Path:
    return Path(__file__).resolve().parent / "events.schema.json"


class Events:
    """Writes events. With no stream (the default, human mode) every emit is a no-op, so
    commands can emit unconditionally."""

    def __init__(self, stream: IO[str] | None = None):
        self._stream = stream
        #: filled in by the command; sent in the final result event
        self.summary: dict[str, object] = {}

    @property
    def enabled(self) -> bool:
        return self._stream is not None

    def emit(self, type: str, **fields: object) -> None:
        if self._stream is None:
            return
        try:
            self._stream.write(json.dumps({"v": VERSION, "type": type, **fields}) + "\n")
            self._stream.flush()
        except BrokenPipeError:
            # The reader (the app) has gone, e.g. on cancel. Stop writing; the command
            # carries on and its exit code is unchanged.
            self._stream = None


def watch_for_stop(stdin: IO[str] | None) -> threading.Event:
    """Sets the returned flag when a `{"type": "stop"}` line arrives on stdin: the app's Stop
    button. A thread reads stdin because the command is busy (sync blocks in elektroid-cli
    during a transfer); the command checks the flag when it's safe to stop. Other lines are
    ignored."""
    flag = threading.Event()
    if stdin is None:           # started with no stdin: nothing can ask to stop
        return flag

    def read() -> None:
        for line in stdin:
            try:
                msg = json.loads(line)
            except ValueError:
                continue
            if isinstance(msg, dict) and msg.get("type") == "stop":
                flag.set()
                return

    threading.Thread(target=read, daemon=True).start()
    return flag


@contextmanager
def json_mode() -> Iterator[Events]:
    sys.stdout.flush()
    saved_fd1 = os.dup(1)
    stream = os.fdopen(os.dup(1), "w", encoding="utf-8")
    os.dup2(2, 1)
    saved_stdout, sys.stdout = sys.stdout, sys.stderr
    try:
        yield Events(stream)
    finally:
        try:
            stream.close()
        except BrokenPipeError:
            pass
        sys.stdout = saved_stdout
        os.dup2(saved_fd1, 1)
        os.close(saved_fd1)
