"""Category evaluation: labels, baselines, metrics, predictions and the `eval` commands."""
import csv
import json

import pytest

from sample_shepherd.cli import main
from sample_shepherd.evaluate import CATEGORIES, baselines, labels as L, metrics, predictions, report


# ----------------------------------------------------------------------------- baselines

@pytest.mark.parametrize("text,expect", [
    ("SD_OberHat-Open02.wav", "sd ober hat open 02"),
    ("Kick01.WAV", "kick 01"),
    ("808Kick (Wet).aif", "808 kick wet"),
    ("FLO_FEB_D#m_08_Synth_140BPM", "flo feb d m 08 synth 140 bpm"),
])
def test_words(text, expect):
    assert baselines.words(text) == expect


@pytest.mark.parametrize("path,name,folder,rules", [
    # the vendor SD_ prefix: naive name rules see snare + kick and abstain
    ("Brunazzi/Custom One Shots/Kicks/SD_Falcon_Kick.wav", None, "KICKS", "KICKS"),
    # nearest folder is Wet (says nothing), so the folder baseline looks one level up
    ("Brunazzi/Custom One Shots/Hi Hats/Wet/SD_OberHat_Loose_(Wet).wav", None, "HATS", "HATS"),
    ("Pack/Snares/SD 3.wav", "SNARES", "SNARES", "SNARES"),
    ("Pack/Cymbals & Percussion/SD_LINDRUM_Clap.wav", None, None, "CLAPS"),
    ("Pack/Loops/Hat_Loop_128bpm.wav", "HATS", None, "DRUMLOOPS"),
    ("Pack/Loops/Bass_Loop_140bpm.wav", "SUB", None, "PHRASES"),
    ("Pack/Bass Drums/AcmeBassDrum.wav", "KICKS", "KICKS", "KICKS"),
    ("Pack/Vocals/Acapella_95bpm.wav", "VOX", "VOX", "VOX"),
    ("Pack/Misc/Untitled_01.wav", None, None, None),
])
def test_baselines(path, name, folder, rules):
    assert baselines.name(path) == name
    assert baselines.folder(path) == folder
    assert baselines.rules(path) == rules


def test_majority_breaks_ties_by_name():
    labs = [L.Label("a", "SNARES"), L.Label("b", "KICKS"), L.Label("c", "SNARES"), L.Label("d", "KICKS")]
    assert baselines.majority("x", labs) == "KICKS"
    assert baselines.majority("x", []) is None


# ----------------------------------------------------------------------------- metrics

def test_metrics_by_hand():
    truth = ["KICKS", "KICKS", "KICKS", "SNARES", "HATS"]
    pred = ["KICKS", "SNARES", None, "SNARES", "HATS"]
    r = metrics.evaluate("x", list("abcde"), truth, pred, ci_rounds=200)
    assert (r.n, r.correct, r.decided) == (5, 3, 4)
    assert r.accuracy == pytest.approx(0.6)
    assert r.coverage == pytest.approx(0.8)
    assert r.accuracy_decided == pytest.approx(0.75)
    k, s = r.per_class["KICKS"], r.per_class["SNARES"]
    assert (k.precision, k.recall) == (1.0, pytest.approx(1 / 3))
    assert (s.precision, s.recall) == (0.5, 1.0)
    assert k.f1 == pytest.approx(0.5)
    assert r.macro_f1 == pytest.approx((0.5 + 2 / 3 + 1.0) / 3)
    assert r.confusion["KICKS"] == {"KICKS": 1, "SNARES": 1, metrics.NONE: 1}
    assert [e[0] for e in r.errors] == ["b", "c"]
    assert 0 <= r.ci[0] <= r.accuracy <= r.ci[1] <= 1


def test_bootstrap_is_deterministic_and_degenerate_cases():
    hits = [True, False, True, True]
    assert metrics.bootstrap_ci(hits, 300) == metrics.bootstrap_ci(hits, 300)
    assert metrics.bootstrap_ci([True] * 5) == (1.0, 1.0)
    assert metrics.bootstrap_ci([]) == (0.0, 0.0)


def test_evaluate_rejects_mismatched_lengths():
    with pytest.raises(ValueError):
        metrics.evaluate("x", ["a"], ["KICKS"], [])


# ----------------------------------------------------------------------------- labels

def write(path, rows, header=("path", "category", "provenance", "note")):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    return path


def test_bundled_labels_are_valid_and_cover_every_category():
    labs = L.load_labels(L.bundled_labels())
    assert len(labs) >= 80
    assert {lab.category for lab in labs} == set(CATEGORIES)
    assert all(lab.provenance for lab in labs)


def test_load_labels_checks(tmp_path):
    ok = write(tmp_path / "ok.csv", [["A/Kick.wav", "kicks", "listened", ""], ["A/Todo.wav", "", "listened", ""]])
    labs = L.load_labels(ok)
    assert [(x.path, x.category) for x in labs] == [("A/Kick.wav", "KICKS")]   # blank row: not labeled yet
    with pytest.raises(ValueError, match="unknown category"):
        L.load_labels(write(tmp_path / "bad.csv", [["A/x.wav", "DRUMS", "", ""]]))
    with pytest.raises(ValueError, match="already labeled"):
        L.load_labels(write(tmp_path / "dup.csv", [["A/x.wav", "KICKS", "", ""], ["/a/X.aif", "SNARES", "", ""]]))
    with pytest.raises(ValueError, match="no category"):
        L.load_labels(write(tmp_path / "cols.csv", [["A/x.wav"]], header=("path",)))


def test_ratings_json_uses_target_for_misfiled(tmp_path):
    root = "/Users/me/packs"
    store = {"version": 1, "ratings": {
        f"{root}/A/Kicks/SD_Kick.wav": {"verdict": "misfiled", "category": "SNARES", "target": "KICKS"},
        f"{root}/A/Hats/Hat 1.wav": {"verdict": "keep", "category": "HATS"},
        f"{root}/A/Loops/Bad.wav": {"verdict": "drop", "category": "DRUMLOOPS"},
        f"{root}/A/X.wav": {"verdict": "misfiled", "category": "FX"},            # no target
        "/elsewhere/Y.wav": {"verdict": "keep", "category": "PADS"},
    }}
    f = tmp_path / "ratings.json"
    f.write_text(json.dumps(store))
    labs, skipped = L.labels_from_ratings(f, root)
    assert {(x.path, x.category, x.provenance) for x in labs} == {
        ("A/Kicks/SD_Kick.wav", "KICKS", "rated-misfiled"), ("A/Hats/Hat 1.wav", "HATS", "rated-keep")}
    assert len(skipped) == 3


def test_ratings_csv_category_is_where_it_belongs(tmp_path):
    f = write(tmp_path / "r.csv", [["/r/A/SD_Kick.wav", "misfiled", "KICKS", "file"],
                                   ["/r/A/Snare.wav", "drop", "", "file"]],
              header=("path", "rating", "category", "scope"))
    labs, skipped = L.labels_from_ratings(f, "/r/")
    assert [(x.path, x.category) for x in labs] == [("A/SD_Kick.wav", "KICKS")]
    assert len(skipped) == 1


def test_merge_human_ratings_win():
    old = [L.Label("A/x.wav", "SNARES", "synthetic"), L.Label("A/y.wav", "PADS", "listened")]
    new = [L.Label("a/X.WAV", "KICKS", "rated-misfiled"), L.Label("A/y.wav", "SYNTH", "folder-rule"),
           L.Label("A/z.wav", "FX", "rated-keep")]
    merged, added, changed, confirmed = L.merge(old, new)
    assert (added, changed, confirmed) == (1, 1, 0)
    assert [x.category for x in merged] == ["KICKS", "PADS", "FX"]
    # a human label that agrees still replaces a rule-made one, so it counts as human
    merged, added, changed, confirmed = L.merge([L.Label("A/k.wav", "KICKS", "folder-rule")],
                                                [L.Label("A/k.wav", "KICKS", "listened")])
    assert (added, changed, confirmed) == (0, 0, 1) and merged[0].provenance == "listened"


# ----------------------------------------------------------------------------- predictions

def manifest(tmp_path, cats):
    master = tmp_path / "master"
    master.mkdir()
    (master / "manifest.json").write_text(json.dumps({
        "src_roots": ["/lib"],
        "categories": {c: {"entries": [{"src": s, "out": f"fam/{s.rsplit('/', 1)[-1]}"} for s in srcs]}
                       for c, srcs in cats.items()}}))
    return master


def test_manifest_predictions_align_by_tail(tmp_path):
    master = manifest(tmp_path, {"KICKS": ["2024/Acme/Kicks/K1.wav", "old/Other/Kicks/K1.wav"],
                                 "SNARES": ["2024/Acme/Snares/S1.wav"]})
    preds = predictions.load_predictions(master)
    labs = [L.Label("Acme/Snares/S1.wav", "SNARES"), L.Label("2024/Acme/Kicks/K1.wav", "KICKS"),
            L.Label("K1.wav", "KICKS"), L.Label("Acme/Pads/P1.wav", "PADS")]
    # a tail that matches two files counts only if they agree (they do here: both KICKS)
    assert predictions.align(labs, preds) == ["SNARES", "KICKS", "KICKS", None]


def test_csv_predictions_and_abstain(tmp_path):
    f = write(tmp_path / "p.csv", [["/x/A/K.wav", "kicks"], ["/x/A/S.wav", ""]], header=("path", "category"))
    preds = predictions.load_predictions(f)
    assert predictions.align([L.Label("A/K.wav", "KICKS"), L.Label("A/S.wav", "SNARES")], preds) == ["KICKS", None]


def test_sample_sheet_is_seeded_blank_and_skips_labeled(tmp_path):
    master = manifest(tmp_path, {"KICKS": [f"P/K{i}.wav" for i in range(20)], "PADS": ["P/Pad.wav"]})
    rows = report.sample_sheet(master, 5, seed=1, exclude=[L.Label("P/K0.wav", "KICKS")])
    assert rows == report.sample_sheet(master, 5, seed=1, exclude=[L.Label("P/K0.wav", "KICKS")])
    assert len(rows) == 6 and all(r["category"] == "" for r in rows)
    assert "P/K0.wav" not in {r["path"] for r in rows}


# ----------------------------------------------------------------------------- CLI

@pytest.fixture
def run(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.delenv("SAMPLE_SHEPHERD_CONFIG", raising=False)

    def _run(*args):
        code = main(list(args))
        out = capsys.readouterr()
        return code, out.out + out.err
    return _run


def test_cli_eval_bundled_set_and_floor(run, tmp_path):
    code, out = run("eval", "categories", "--fail-under", "rules=0.9")
    assert code == 0, out
    assert "majority" in out and "per category: rules" in out and "confusion" in out
    code, out = run("eval", "categories", "--fail-under", "majority=0.9")
    assert code == 1 and "below the floor" in out
    code, out = run("eval", "categories", "--fail-under", "nope")
    assert code == 2


def test_cli_eval_predictions_json_and_dry_run(run, tmp_path):
    labels = write(tmp_path / "l.csv", [["Acme/Kicks/K1.wav", "KICKS", "listened", ""],
                                        ["Acme/Snares/S1.wav", "SNARES", "listened", ""]])
    master = manifest(tmp_path, {"KICKS": ["2024/Acme/Kicks/K1.wav", "2024/Acme/Snares/S1.wav"]})
    out_json = tmp_path / "res.json"
    code, out = run("eval", "categories", "--labels", str(labels), "--baselines",
                    "--predictions", str(master), "--json", str(out_json), "--dry-run")
    assert code == 0 and "(dry run" in out and not out_json.exists()
    code, out = run("eval", "categories", "--labels", str(labels), "--baselines", "folder",
                    "--predictions", str(master), "--json", str(out_json))
    assert code == 0, out
    res = json.loads(out_json.read_text())["results"]
    assert [r["system"] for r in res] == ["folder", "master"]
    assert res[1]["accuracy"] == 0.5 and res[1]["by_provenance"]["listened"] == {"correct": 1, "n": 2}


def test_cli_import_ratings(run, tmp_path):
    ratings = tmp_path / "ratings.json"
    ratings.write_text(json.dumps({"ratings": {"/lib/A/Kick.wav": {"verdict": "keep", "category": "KICKS"}}}))
    target = tmp_path / "labels.csv"
    code, out = run("eval", "import-ratings", str(ratings), "--labels", str(target), "--root", "/lib", "--dry-run")
    assert code == 0 and not target.exists()
    code, out = run("eval", "import-ratings", str(ratings), "--labels", str(target), "--root", "/lib")
    assert code == 0, out
    assert [(x.path, x.category) for x in L.load_labels(target)] == [("A/Kick.wav", "KICKS")]


def test_cli_sample_refuses_overwrite(run, tmp_path):
    master = manifest(tmp_path, {"KICKS": ["P/K1.wav", "P/K2.wav"]})
    sheet = tmp_path / "sheet.csv"
    code, out = run("eval", "sample", str(master), "--out", str(sheet), "--per-category", "1")
    assert code == 0 and len(L.load_labels(sheet)) == 0           # nothing labeled yet
    code, out = run("eval", "sample", str(master), "--out", str(sheet))
    assert code == 2 and "already exists" in out
    code, out = run("eval", "sample", str(master), "--out", str(sheet), "--dry-run")
    assert code == 2 and "already exists" in out
