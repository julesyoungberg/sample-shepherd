"""Run Fourier as an external command, and set up the patched build our config needs."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

FOURIER_REPO = "https://github.com/bvk7787/fourier-samples"
FOURIER_BASE = "131ee62"            # fourier-samples v0.1.2, the commit our patches apply to
PATCH_BRANCH = "local/adaptive-folders"


def patches_dir() -> Path:
    pkg = Path(__file__).resolve().parent.parent / "patches"
    if pkg.is_dir():
        return pkg
    return Path(__file__).resolve().parents[3] / "config" / "patches"


def list_patches() -> list[Path]:
    return sorted(patches_dir().glob("*.patch"))


def patch_subject(p: Path) -> str:
    lines = p.read_text(errors="replace").splitlines()
    for i, line in enumerate(lines):
        if line.startswith("Subject:"):
            text = line[8:]
            for more in lines[i + 1:]:          # RFC 822 continuation lines
                if not more.startswith((" ", "\t")):
                    break
                text += more
            return (text.split("]", 1)[-1] if "]" in text else text).strip()
    return p.stem


def env_for(cfg) -> dict[str, str]:
    env = dict(os.environ)
    env.update(cfg.fourier_env)
    return env


def resolve_command(cfg) -> str | None:
    cmd = cfg.fourier_command
    if "/" in cmd:
        return cmd if Path(cmd).is_file() else None
    path = env_for(cfg).get("PATH")
    return shutil.which(cmd, path=path)


def command(cfg, *args: str) -> list[str]:
    return [resolve_command(cfg) or cfg.fourier_command, *args]


def run(cfg, *args: str, dry_run: bool = False, out=print) -> int:
    cmd = command(cfg, *args)
    out("$ " + " ".join(_quote(c) for c in cmd))
    if dry_run:
        return 0
    if resolve_command(cfg) is None:
        out(f"fourier not found ({cfg.fourier_command!r}). See `sample-shepherd organize doctor`.")
        return 127
    return subprocess.run(cmd, env=env_for(cfg)).returncode


def install_steps(target: Path, python: str | None = None) -> list[list[str]]:
    """The commands that build the patched Fourier our config needs, into `target`."""
    target = Path(target)
    sync = ["uv", "sync", "--frozen", "--directory", str(target), "--extra", "clap"]
    if python:
        sync += ["--python", python]
    return [
        ["git", "clone", FOURIER_REPO, str(target)],
        ["git", "-C", str(target), "switch", "-c", PATCH_BRANCH, FOURIER_BASE],
        ["git", "-C", str(target), "am", *[str(p) for p in list_patches()]],
        sync,
    ]


def _quote(s: str) -> str:
    return f"'{s}'" if (" " in s or not s) else s
