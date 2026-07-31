"""Calculate character and word error rates for checked research fixtures."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def edit_distance(reference, hypothesis) -> int:
    """Levenshtein distance using memory proportional to the shorter sequence."""
    if len(reference) < len(hypothesis):
        reference, hypothesis = hypothesis, reference
    previous = list(range(len(hypothesis) + 1))
    for row, reference_item in enumerate(reference, start=1):
        current = [row]
        for column, hypothesis_item in enumerate(hypothesis, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[column] + 1,
                    previous[column - 1] + (reference_item != hypothesis_item),
                )
            )
        previous = current
    return previous[-1]


def prepare_text(text: str, *, casefold: bool = False, collapse_whitespace: bool = False) -> str:
    if casefold:
        text = text.casefold()
    if collapse_whitespace:
        text = re.sub(r"\s+", " ", text).strip()
    return text


def error_metrics(reference: str, hypothesis: str) -> dict:
    reference_words = reference.split()
    hypothesis_words = hypothesis.split()
    character_edits = edit_distance(reference, hypothesis)
    word_edits = edit_distance(reference_words, hypothesis_words)
    return {
        "reference_characters": len(reference),
        "character_edits": character_edits,
        "cer": character_edits / max(1, len(reference)),
        "reference_words": len(reference_words),
        "word_edits": word_edits,
        "wer": word_edits / max(1, len(reference_words)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare a model transcription with a manually checked reference."
    )
    parser.add_argument("reference", type=Path)
    parser.add_argument("hypothesis", type=Path)
    parser.add_argument("--casefold", action="store_true")
    parser.add_argument("--collapse-whitespace", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    options = {
        "casefold": args.casefold,
        "collapse_whitespace": args.collapse_whitespace,
    }
    reference = prepare_text(args.reference.read_text(encoding="utf-8"), **options)
    hypothesis = prepare_text(args.hypothesis.read_text(encoding="utf-8"), **options)
    metrics = error_metrics(reference, hypothesis)
    if args.as_json:
        print(json.dumps(metrics, indent=2))
    else:
        print(f"CER: {metrics['cer']:.2%} ({metrics['character_edits']} edits)")
        print(f"WER: {metrics['wer']:.2%} ({metrics['word_edits']} edits)")


if __name__ == "__main__":
    main()

