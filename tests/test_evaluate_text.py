from scripts.evaluate_text import edit_distance, error_metrics, prepare_text


def test_edit_distance_and_rates():
    assert edit_distance("kitten", "sitting") == 3
    metrics = error_metrics("one two three", "one too three")
    assert metrics["word_edits"] == 1
    assert metrics["wer"] == 1 / 3


def test_normalization_is_explicit():
    source = "  Mixed\n  CASE  "
    assert prepare_text(source) == source
    assert prepare_text(source, casefold=True, collapse_whitespace=True) == "mixed case"

