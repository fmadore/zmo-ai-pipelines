from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "evaluate_text.py"
SPEC = spec_from_file_location("evaluate_text", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
EVALUATE_TEXT = module_from_spec(SPEC)
SPEC.loader.exec_module(EVALUATE_TEXT)

edit_distance = EVALUATE_TEXT.edit_distance
error_metrics = EVALUATE_TEXT.error_metrics
prepare_text = EVALUATE_TEXT.prepare_text


def test_edit_distance_and_rates():
    assert edit_distance("kitten", "sitting") == 3
    metrics = error_metrics("one two three", "one too three")
    assert metrics["word_edits"] == 1
    assert metrics["wer"] == 1 / 3


def test_normalization_is_explicit():
    source = "  Mixed\n  CASE  "
    assert prepare_text(source) == source
    assert prepare_text(source, casefold=True, collapse_whitespace=True) == "mixed case"


def test_corpus_weighted_metrics_unicode_and_strata(tmp_path):
    import json

    from zmo_evaluate import evaluate_corpus

    (tmp_path / "ref.txt").write_text("é one two")
    (tmp_path / "a.txt").write_text("e\u0301 one two")
    (tmp_path / "b.txt").write_text("é one too")
    manifest = tmp_path / "corpus.json"
    manifest.write_text(
        json.dumps(
            {
                "fixtures": [
                    {
                        "id": "f1",
                        "reference": "ref.txt",
                        "hypotheses": {"A": "a.txt", "B": "b.txt"},
                        "language": "fr",
                        "script": "Latin",
                        "condition": "clean",
                        "kind": "ocr",
                    }
                ]
            }
        )
    )
    result = evaluate_corpus(manifest, unicode_nfc=True)
    overall = {r["variant"]: r for r in result["aggregates"] if r["dimension"] == "overall"}
    assert overall["A"]["cer"] == 0
    assert overall["B"]["wer"] == 1 / 3
    assert len(result["aggregates"]) == 10
    assert result["fixtures"][0]["reference_sha256"]
