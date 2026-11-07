"""Configuration: a TOML file, overridden by command-line flags.

Lookup order for the file: --config, $SAMPLE_SHEPHERD_CONFIG, ./sample-shepherd.toml,
$XDG_CONFIG_HOME/sample-shepherd/config.toml (~/.config/... by default). No file is fine:
every setting has a default, and no default points at anyone's home layout except
`work_dir`, which defaults to the current directory.

Relative paths in the file are read relative to the file's own folder.
"""
from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

ENV_VAR = "SAMPLE_SHEPHERD_CONFIG"


@dataclass
class Transfer:
    """Measured device transfer speed, used for time estimates only."""
    bytes_per_second: float = 77_000      # Digitakt II over USB via elektroid-cli, measured 2026-11-06
    seconds_per_call: float = 1.6         # fixed cost of each elektroid-cli call


@dataclass
class Config:
    path: Path | None = None              # the file this came from, if any
    work_dir: Path = field(default_factory=Path.cwd)
    device_backend: str = "elektron"
    device_id: str = "1"                  # elektroid-cli device number (`sample-shepherd device ls`)
    elektroid_cli: str = "elektroid-cli"  # a path, or a name on PATH
    fourier_command: str = "fourier"
    fourier_env: dict[str, str] = field(default_factory=dict)
    profile_dirs: list[Path] = field(default_factory=list)
    protected: list[str] = field(default_factory=lambda: ["/factory"])
    transfer: Transfer = field(default_factory=Transfer)

    @property
    def lock_file(self) -> Path:
        """One lock per device, the same for every sample-shepherd process of this user
        whatever its working folder or config: $SAMPLE_SHEPHERD_LOCK_DIR, else
        $XDG_RUNTIME_DIR, else the system temp folder."""
        import tempfile
        base = (os.environ.get("SAMPLE_SHEPHERD_LOCK_DIR") or os.environ.get("XDG_RUNTIME_DIR")
                or tempfile.gettempdir())
        dev = "".join(c if c.isalnum() or c in "-_" else "_" for c in self.device_id)
        return Path(base) / f"sample-shepherd-{self.device_backend}-{dev}.lock"


def find_config_file(explicit: str | None = None) -> Path | None:
    if explicit:
        p = Path(explicit).expanduser()
        if not p.is_file():
            raise FileNotFoundError(f"config file not found: {p}")
        return p
    if os.environ.get(ENV_VAR):
        p = Path(os.environ[ENV_VAR]).expanduser()
        if not p.is_file():
            raise FileNotFoundError(f"${ENV_VAR} points at a missing file: {p}")
        return p
    local = Path.cwd() / "sample-shepherd.toml"
    if local.is_file():
        return local
    xdg = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    user = xdg / "sample-shepherd" / "config.toml"
    return user if user.is_file() else None


def _path(base: Path, value: str) -> Path:
    p = Path(os.path.expandvars(value)).expanduser()
    return p if p.is_absolute() else (base / p)


def load(explicit: str | None = None) -> Config:
    path = find_config_file(explicit)
    cfg = Config(path=path)
    if path is None:
        return cfg
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    base = path.parent
    known = {"work_dir", "device", "elektroid", "fourier", "export", "sync", "transfer"}
    unknown = set(data) - known
    if unknown:
        raise ValueError(f"{path}: unknown settings {sorted(unknown)} (known: {sorted(known)})")
    if "work_dir" in data:
        cfg.work_dir = _path(base, data["work_dir"])
    dev = data.get("device", {})
    cfg.device_backend = dev.get("backend", cfg.device_backend)
    cfg.device_id = str(dev.get("id", cfg.device_id))
    el = data.get("elektroid", {})
    if "cli" in el:
        cli = el["cli"]
        cfg.elektroid_cli = str(_path(base, cli)) if ("/" in cli or cli.startswith("~")) else cli
    fo = data.get("fourier", {})
    cfg.fourier_command = fo.get("command", cfg.fourier_command)
    if "/" in cfg.fourier_command or cfg.fourier_command.startswith("~"):
        cfg.fourier_command = str(_path(base, cfg.fourier_command))
    cfg.fourier_env = {k: os.path.expanduser(os.path.expandvars(str(v)))
                       for k, v in fo.get("env", {}).items()}
    ex = data.get("export", {})
    cfg.profile_dirs = [_path(base, d) for d in ex.get("profile_dirs", [])]
    sy = data.get("sync", {})
    cfg.protected = list(sy.get("protected", cfg.protected))
    tr = data.get("transfer", {})
    cfg.transfer = Transfer(float(tr.get("bytes_per_second", cfg.transfer.bytes_per_second)),
                            float(tr.get("seconds_per_call", cfg.transfer.seconds_per_call)))
    return cfg
