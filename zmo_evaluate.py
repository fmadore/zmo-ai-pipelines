"""Offline character/word accuracy evaluation with reproducible corpus strata."""

from __future__ import annotations

import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

from rapidfuzz.distance import Levenshtein

from zmo_state import file_sha256, utc_now


def edit_distance(reference, hypothesis):
    return Levenshtein.distance(reference, hypothesis)


def prepare_text(text, *, casefold=False, collapse_whitespace=False, unicode_nfc=False):
    if unicode_nfc:
        text = unicodedata.normalize("NFC", text)
    if casefold:
        text = text.casefold()
    if collapse_whitespace:
        text = re.sub(r"\s+", " ", text).strip()
    return text


def error_metrics(reference, hypothesis):
    rw, hw = reference.split(), hypothesis.split()
    ce, we = edit_distance(reference, hypothesis), edit_distance(rw, hw)
    return {
        "reference_characters": len(reference),
        "character_edits": ce,
        "cer": ce / max(1, len(reference)),
        "reference_words": len(rw),
        "word_edits": we,
        "wer": we / max(1, len(rw)),
    }


def evaluate_corpus(manifest_path, **normalization):
    """Each fixture has one reference and named A/B hypotheses; paths are relative."""
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows, totals, seen = [], defaultdict(lambda: defaultdict(int)), set()
    if not isinstance(manifest.get("fixtures"), list) or not manifest["fixtures"]:
        raise ValueError("Corpus manifest needs a nonempty fixtures list")
    for fixture in manifest["fixtures"]:
        if fixture["id"] in seen:
            raise ValueError("Fixture IDs must be unique")
        seen.add(fixture["id"])
        reference = manifest_path.parent / fixture["reference"]
        ref = prepare_text(reference.read_text(encoding="utf-8"), **normalization)
        if not fixture.get("hypotheses"):
            raise ValueError("Each fixture needs named hypotheses")
        for variant, name in fixture["hypotheses"].items():
            hypothesis = manifest_path.parent / name
            hyp = prepare_text(hypothesis.read_text(encoding="utf-8"), **normalization)
            metrics = error_metrics(ref, hyp)
            strata = {
                k: fixture.get(k, "unspecified")
                for k in ("language", "script", "condition", "kind")
            }
            rows.append(
                {
                    "id": fixture["id"],
                    "variant": variant,
                    **strata,
                    **metrics,
                    "reference_sha256": file_sha256(reference),
                    "hypothesis_sha256": file_sha256(hypothesis),
                }
            )
            for dimension, label in [("overall", "all"), *strata.items()]:
                total = totals[(variant, dimension, label)]
                total["fixtures"] += 1
                for key in (
                    "reference_characters",
                    "character_edits",
                    "reference_words",
                    "word_edits",
                ):
                    total[key] += metrics[key]
    aggregates = []
    for (variant, dimension, label), total in sorted(totals.items()):
        aggregates.append(
            {
                "variant": variant,
                "dimension": dimension,
                "label": label,
                **total,
                "cer": total["character_edits"] / max(1, total["reference_characters"]),
                "wer": total["word_edits"] / max(1, total["reference_words"]),
            }
        )
    return {
        "created_utc": utc_now(),
        "manifest_sha256": file_sha256(manifest_path),
        "normalization": normalization,
        "fixtures": rows,
        "aggregates": aggregates,
        "method": "Levenshtein; reference-denominator CER/WER; micro-weighted aggregates",
    }
