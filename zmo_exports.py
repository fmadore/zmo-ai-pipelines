"""Research exports, provenance and human review without altering raw output."""

import hashlib
import json
import math
import platform
import random
from importlib.metadata import version
from pathlib import Path

from zmo_state import file_sha256, utc_now


def export_records(store):
    rows = []
    for unit in store.units():
        review_ref = store.manifest["reviews"].get(unit["unit_id"])
        review = None
        if review_ref:
            review = json.loads((store.directory / review_ref["path"]).read_text())
            review["matches_current_output"] = (
                review.get("unit_sha256") == store.manifest["units"][unit["unit_id"]]["sha256"]
            )
        rows.append(
            {
                "source_id": store.manifest["source"]["id"],
                "source": store.manifest["source"],
                "run_id": store.manifest["run_id"],
                "model": store.manifest["config"]["model"],
                "unit": unit,
                "review": review,
                "provenance": "provenance.json",
            }
        )
    store.artifact("records.jsonl", "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    modules = {}
    for path in Path(__file__).parent.glob("zmo_*.py"):
        modules[path.name] = file_sha256(path)
    provenance = {
        key: store.manifest[key]
        for key in ("schema_version", "run_id", "source", "config", "signature", "state", "jobs")
    }
    provenance.update(
        created_utc=utc_now(),
        prompt_sha256=prompt_id(store.manifest["config"]["prompt"]),
        software={
            "python": platform.python_version(),
            "google_genai": version("google-genai"),
            "modules": modules,
        },
        units=[
            {
                "unit_id": u["unit_id"],
                "status": u["status"],
                "locator": u["locator"],
                "metadata": u["metadata"],
            }
            for u in store.units(include_chunks=True)
        ],
    )
    store.artifact("provenance.json", json.dumps(provenance, ensure_ascii=False, indent=2) + "\n")


def review_queue(store, sample_size=5, seed=0):
    records = store.units()
    flagged = [
        u
        for u in records
        if u["status"] not in {"complete", "empty"}
        or any(marker in u["text"] for marker in ("[UNCERTAIN", "[ILLEGIBLE"))
    ]
    ids = {u["unit_id"] for u in flagged}
    other = [u for u in records if u["unit_id"] not in ids and u["status"] == "complete"]
    return flagged + random.Random(seed).sample(other, min(max(0, sample_size), len(other)))


def save_review(store, unit_id, text, reviewer, note=""):
    if not store.unit(unit_id):
        raise ValueError("Unknown source unit")
    if not reviewer.strip():
        raise ValueError("Enter a reviewer name or identifier")
    prior = store.manifest["reviews"].get(unit_id)
    if prior:
        store.manifest.setdefault("review_history", []).append(prior)
    record = {
        "unit_id": unit_id,
        "unit_sha256": store.manifest["units"][unit_id]["sha256"],
        "corrected_text": text,
        "reviewer": reviewer.strip(),
        "note": note,
        "reviewed_utc": utc_now(),
        "previous": prior,
    }
    store.manifest["reviews"][unit_id] = store._store(
        json.dumps(record, ensure_ascii=False), "reviews"
    )
    store.save()
    export_records(store)


def _timestamp(seconds, separator):
    milliseconds = round(seconds * 1000)
    whole, ms = divmod(milliseconds, 1000)
    minutes, sec = divmod(whole, 60)
    hours, minute = divmod(minutes, 60)
    return f"{hours:02}:{minute:02}:{sec:02}{separator}{ms:03}"


def subtitle_text(words, *, webvtt=False, max_seconds=6.0, max_chars=84):
    cues, current = [], []
    previous_start = -1.0
    for word in words:
        start, end = word.get("start_seconds"), word.get("end_seconds")
        if start is None or end is None:
            continue
        if (
            not math.isfinite(start)
            or not math.isfinite(end)
            or not 0 <= start <= end
            or start < previous_start
        ):
            raise ValueError("Word times must be finite, ordered, and have end >= start")
        previous_start = start
        if current and (
            word.get("speaker") != current[-1].get("speaker")
            or end - current[0]["start_seconds"] > max_seconds
            or sum(len(w["text"]) + 1 for w in current) + len(word["text"]) > max_chars
        ):
            cues.append(current)
            current = []
        current.append(word)
    if current:
        cues.append(current)
    lines = ["WEBVTT", ""] if webvtt else []
    separator = "." if webvtt else ","
    for index, cue in enumerate(cues, 1):
        start, end = cue[0]["start_seconds"], max(w["end_seconds"] for w in cue)
        label = f"[{cue[0]['speaker']}] " if cue[0].get("speaker") else ""
        text = label + " ".join(w["text"].replace("\n", " ") for w in cue)
        text = text.replace("-->", "→")
        if webvtt:
            text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        lines.extend(
            [
                str(index),
                f"{_timestamp(start, separator)} --> {_timestamp(end, separator)}",
                text,
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def prompt_id(text):
    return hashlib.sha256(text.encode()).hexdigest()
