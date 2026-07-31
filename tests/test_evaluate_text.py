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
