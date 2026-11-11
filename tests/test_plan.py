import pytest

from conftest import make_wav
from sample_shepherd.config import Transfer
from sample_shepherd.sync.listing import Listed
from sample_shepherd.sync.plan import PlanError, PlanRow, make_plan, set_excluded, summarize
from sample_shepherd.sync.projects import UsedSample


@pytest.fixture
def render(tmp_path):
    r = tmp_path / "render"
    make_wav(r / "01_KICKS" / "hard" / "BD 01.wav")
    make_wav(r / "01_KICKS" / "hard" / "BD 02.wav")
    make_wav(r / "02_SNARES" / "SD 01.wav")
    return r


LISTING = [
    Listed("/01_KICKS/hard/BD 01", 1000, "00000001"),     # already there
    Listed("/01_KICKS/hard/OLD KICK", 1000, "00000002"),  # not in export
    Listed("/01_KICKS/hard/USED KICK", 1000, "00000003"), # not in export, used by path
    Listed("/01_KICKS/hard/SAME BYTES", 1000, "00000004"),# not in export, hash of a used sample
    Listed("/factory/BD", 500, "00000005"),
    Listed("/other/thing", 500, "00000006"),
]
USED = [UsedSample("/01_KICKS/hard/used kick", 1000, "00000003"), UsedSample("/elsewhere/x", 1000, "00000004")]


def by_action(rows):
    out = {}
    for r in rows:
        out.setdefault(r.action, []).append(r.device_path)
    return out


def test_uploads_skip_existing(render):
    rows = make_plan(LISTING, None, render)
    a = by_action(rows)
    assert a["upload"] == ["/01_KICKS/hard/BD 02", "/02_SNARES/SD 01"]
    assert a["skip-exists"] == ["/01_KICKS/hard/BD 01"]
    assert "delete" not in a


def test_dest_prefix(render):
    rows = make_plan([], None, render, folders=["02_SNARES"], dest="/new")
    assert by_action(rows) == {"upload": ["/new/02_SNARES/SD 01"]}


def test_prune_never_deletes_used_or_outside(render):
    rows = make_plan(LISTING, USED, render, prune=True, protected=["/factory"])
    a = by_action(rows)
    assert a["delete"] == ["/01_KICKS/hard/OLD KICK"]
    assert sorted(a["keep-used"]) == ["/01_KICKS/hard/SAME BYTES", "/01_KICKS/hard/USED KICK"]
    assert "/other/thing" not in sum(a.values(), [])


def test_replace_list_and_protected(render):
    rows = make_plan(LISTING, USED, None, replace=["/factory/BD", "/other/thing", "/gone"], protected=["/factory"])
    a = by_action(rows)
    assert a == {"keep-protected": ["/factory/BD"], "delete": ["/other/thing"], "skip-missing": ["/gone"]}


def test_deletes_need_a_usage_list(render):
    with pytest.raises(PlanError, match="--used"):
        make_plan(LISTING, None, render, prune=True)
    with pytest.raises(PlanError, match="empty"):
        make_plan(LISTING, [], render, prune=True)


def test_summary_estimates_time(render):
    rows = make_plan([], None, render)
    text = summarize(rows, Transfer(bytes_per_second=1000, seconds_per_call=1))
    assert "upload 3 files" in text and "estimated time" in text


def test_sectioned_render_with_nested_folders(tmp_path):
    """A four-level render (SECTION/CATEGORY/...): --folders names a category under its
    section, and --prune stays inside that category, never the whole section."""
    r = tmp_path / "render4"
    make_wav(r / "DRUMS" / "01_KICKS" / "hard" / "BD 01.wav")
    make_wav(r / "DRUMS" / "02_SNARES" / "SD 01.wav")
    listing = [
        Listed("/DRUMS/01_KICKS/hard/OLD KICK", 1000, "00000011"),
        Listed("/DRUMS/03_CLAPS/CP 01", 1000, "00000012"),   # same section, not named
    ]
    rows = make_plan(listing, USED, r, folders=["DRUMS/01_KICKS"], prune=True)
    a = by_action(rows)
    assert a["upload"] == ["/DRUMS/01_KICKS/hard/BD 01"]
    assert a["delete"] == ["/DRUMS/01_KICKS/hard/OLD KICK"]
    assert "/DRUMS/03_CLAPS/CP 01" not in sum(a.values(), [])
    with pytest.raises(PlanError):
        make_plan([], None, r, folders=["01_KICKS"])


def test_exclude_and_include_rows_by_id():
    rows = [PlanRow("upload", "/A"), PlanRow("delete", "/B", hash="0000000b"), PlanRow("keep-used", "/C")]
    set_excluded(rows, [1, 2], True)
    assert [r.action for r in rows] == ["excluded-upload", "excluded-delete", "keep-used"]
    set_excluded(rows, [1, 2], True)       # again: no change, not an error
    set_excluded(rows, [2], False)
    assert [r.action for r in rows] == ["excluded-upload", "delete", "keep-used"]
    assert summarize(rows, Transfer()).splitlines()[1].startswith("delete 1 files")
    assert "excluded: 1" in summarize(rows, Transfer())


def test_edit_can_only_turn_off_or_back_on_what_plan_chose():
    rows = [PlanRow("upload", "/A"), PlanRow("keep-used", "/C")]
    with pytest.raises(PlanError, match="row 2 is keep-used"):
        set_excluded(rows, [2], True)
    with pytest.raises(PlanError, match="row 2 is keep-used"):
        set_excluded(rows, [2], False)      # including never turns a kept sample into a delete
    with pytest.raises(PlanError, match="no row 3"):
        set_excluded(rows, [3], True)
    assert [r.action for r in rows] == ["upload", "keep-used"]
