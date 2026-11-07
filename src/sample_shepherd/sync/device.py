"""The device interface every sync backend implements, and the backend registry.

A backend is a small class: list what's connected, list/mkdir/upload/delete on the sample
storage, and list/download projects. Everything above it (backup, used-sample lists,
planning, the resumable sync) is shared. To add a device family, see docs/adding-a-device.md.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


class DeviceError(RuntimeError):
    pass


@dataclass(frozen=True)
class DeviceInfo:
    number: str        # how the backend addresses it (elektroid-cli: 0 is the computer, 1 the first device)
    id: str
    name: str


@dataclass(frozen=True)
class Entry:
    kind: str          # "D" folder, "F" file
    name: str
    size: int | None   # bytes; approximate when the backend prints rounded sizes
    hash: str | None   # backend-specific content hash, lowercase hex, if it has one


@dataclass(frozen=True)
class ProjectSlot:
    slot: str
    name: str
    size: int | None
    valid: bool = True  # the backend says the slot holds data


class Device(ABC):
    """One connected device. Methods raise DeviceError on failure."""

    #: file suffix of a downloaded project backup (e.g. ".dt2prj")
    project_suffix: str = ""
    #: how a sample's name appears on the device: True if the extension is dropped on upload
    strips_extension: bool = True

    def describe(self, op: str) -> str:
        """How the backend would carry out a read-only `op` ("list_devices", "info",
        "list_projects"), for --dry-run output. Must not touch the device."""
        return op

    @abstractmethod
    def list_devices(self) -> list[DeviceInfo]: ...

    def info(self) -> dict[str, object]:
        """What the device supports: at least {"filesystems": [...]}, when the backend knows."""
        return {"filesystems": []}

    @abstractmethod
    def ls(self, path: str) -> list[Entry]:
        """List one folder of the sample storage. Raises DeviceError if it doesn't exist."""

    @abstractmethod
    def mkdir(self, path: str) -> None:
        """Create a folder (and its parents) on the sample storage."""

    @abstractmethod
    def upload(self, local: Path, dest_dir: str) -> None:
        """Upload one file into a sample-storage folder. Must never overwrite."""

    @abstractmethod
    def delete(self, path: str) -> None:
        """Delete one sample-storage file."""

    @abstractmethod
    def list_projects(self) -> list[ProjectSlot]: ...

    @abstractmethod
    def download_project(self, slot: str, dest_dir: Path) -> Path:
        """Download one project into dest_dir; return the file written."""

    def walk(self, root: str = "/", progress=None):
        """Yield (path, Entry) for every file under root, depth first, read-only."""
        stack, folders = [root], 0
        while stack:
            d = stack.pop()
            folders += 1
            for e in self.ls(d):
                p = d.rstrip("/") + "/" + e.name
                if e.kind == "D":
                    stack.append(p)
                else:
                    yield p, e
            if progress and folders % 50 == 0:
                progress(folders)


def get_backend(cfg) -> Device:
    """The configured backend for the configured device."""
    if cfg.device_backend == "elektron":
        from sample_shepherd.sync.elektron import ElektronDevice
        return ElektronDevice(cli=cfg.elektroid_cli, device=cfg.device_id)
    raise DeviceError(f"unknown device backend {cfg.device_backend!r} (known: elektron)")
