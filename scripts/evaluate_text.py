"""Calculate character and word error rates for checked research fixtures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from zmo_evaluate import edit_distance, error_metrics, prepare_text  # noqa: F401


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

