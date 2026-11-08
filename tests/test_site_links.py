"""The landing page links to repo files on GitHub; those files must exist."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_site_repo_links_point_to_existing_files():
    content = (ROOT / "site/src/lib/content.js").read_text()
    page = (ROOT / "site/src/routes/+page.svelte").read_text()
    paths = re.findall(r"repoFile\(\s*'([^']+)'", page) + re.findall(r"path:\s*'([^']+)'", content)
    assert paths, "no repo links found; did repoFile() move?"
    missing = [p for p in paths if not (ROOT / p).is_file()]
    assert not missing, f"site links to files that don't exist: {missing}"
