"""The one-off scripts in scripts/ stay where they are and keep compiling: they are run by
path (and symlinked into a working tree) while the package grows next to them."""
import py_compile
from pathlib import Path

import pytest

SCRIPTS = sorted((Path(__file__).parents[1] / "scripts").glob("*.py"))


def test_scripts_exist():
    names = {p.name for p in SCRIPTS}
    assert {"drive_listing.py", "upload_tree.py", "delete_replaced.py", "drive_match.py"} <= names


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_script_compiles(script, tmp_path):
    py_compile.compile(str(script), cfile=str(tmp_path / "x.pyc"), doraise=True)
