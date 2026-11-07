"""docs/cli/reference.md is generated from the argparse parser; it must match the code."""
from pathlib import Path

from sample_shepherd import cli_reference

DOC = Path(__file__).resolve().parents[1] / "docs" / "cli" / "reference.md"


def test_reference_doc_is_current():
    assert DOC.read_text(encoding="utf-8") == cli_reference.render(), (
        "docs/cli/reference.md is out of date: run "
        "`python -m sample_shepherd.cli_reference > docs/cli/reference.md`")


def test_reference_lists_every_command_and_flag():
    text = cli_reference.render()
    for heading in ("## `sync`", "### `projects backup`", "### `config init`"):
        assert heading in text
    assert "`--yes`" in text and "`--dry-run`" in text
