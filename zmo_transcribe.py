"""Prompt-free Gemini Transcribe adapter, bundled into the audio notebook.

Regenerate the notebook copy with scripts/bundle_transcribe.py after editing.
"""

from __future__ import annotations

import math
import time

MODEL = "gemini-3.5-transcribe"
VERSION = "2026.09.08"


def error_message(exc):
    code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    hints = {
        400: "Check the language code, audio format and options in Step 4.",
        401: "Check your API key in Step 2.",
        403: "Check this project's billing and access to Gemini Transcribe in AI Studio.",
        404: "Gemini Transcribe is unavailable on this project; check access in AI Studio.",
        429: "Quota reached. Wait and check your project quota before retrying.",
    }
    return f"{hints.get(code, 'Check the recording or retry later.')} {exc}"


def configuration(mode="verbatim", languages=(), speakers=False, timestamps=False,
                  vocabulary=()):
    """Validate incompatible options before uploading or spending API quota."""
    if mode not in {"verbatim", "smart"}:
        raise ValueError("Choose Verbatim or Smart in Step 4.")
    if mode == "smart" and (speakers or timestamps):
        raise ValueError("Smart cannot identify speakers or add word times. Choose Verbatim.")
    terms = list(dict.fromkeys(term.strip() for term in vocabulary if term.strip()))
    if len(terms) > 1000:
        raise ValueError("Use at most 1,000 vocabulary terms (about 100 is recommended).")
    if terms and (speakers or timestamps):
        raise ValueError("Vocabulary hints cannot be used with speakers or word times.")
    selected_mode = "smart" if mode == "smart" else {"type": "verbatim"}
    if speakers:
        selected_mode["diarization_mode"] = "speaker"
    if timestamps:
        selected_mode["timestamp_granularities"] = ["word"]
    config = {"mode": selected_mode, "language_codes": list(languages)}
    if terms:
        config["custom_vocabulary"] = terms
    return config


def segment_limit(config):
    mode = config["mode"]
    annotated = isinstance(mode, dict) and (
        mode.get("diarization_mode") or mode.get("timestamp_granularities")
    )
    return 30 * 60 if annotated else 60 * 60


def field(value, name, default=None):
    return value.get(name, default) if isinstance(value, dict) else getattr(value, name, default)


def seconds(value):
    if value is None:
        return None
    result = float(str(value).removesuffix("s"))
    if not math.isfinite(result) or result < 0:
        raise ValueError("The API returned an invalid word timestamp.")
    return result


def parse_interaction(interaction, offset=0.0, segment=1):
    """Keep exact transcript text; scope speaker IDs to their API request."""
    status = field(interaction, "status")
    if status != "completed":
        raise RuntimeError(f"Transcription did not complete (status: {status}). Retry this file.")
    text = field(interaction, "output_text", "") or ""
    words = []
    for step in field(interaction, "steps", []) or []:
        for content in field(step, "content", []) or []:
            for annotation in field(content, "annotations", []) or []:
                if field(annotation, "type") != "word_info":
                    continue
                start = seconds(field(annotation, "start_offset"))
                end = seconds(field(annotation, "end_offset"))
                speaker = field(annotation, "speaker")
                words.append({
                    "text": field(annotation, "text", ""),
                    "speaker": f"segment-{segment}:{speaker}" if speaker else None,
                    "start_seconds": round(start + offset, 6) if start is not None else None,
                    "end_seconds": round(end + offset, 6) if end is not None else None,
                    "segment": segment,
                })
    if not text.strip():
        raise RuntimeError("No speech text returned. Check the recording before retrying.")
    usage = field(interaction, "usage")
    if hasattr(usage, "model_dump"):
        usage = usage.model_dump(mode="json")
    return {
        "text": text, "words": words,
        "metadata": {
            "interaction_id": field(interaction, "id"),
            "model_version": field(interaction, "model_version"),
            "finish_reason": status,
            "usage": usage if isinstance(usage, dict) else None,
        },
    }


def transcribe(client, path, mime_type, config, *, offset=0.0, segment=1):
    """Upload, wait, transcribe without interaction storage, then delete upload."""
    uploaded = None
    try:
        uploaded = client.files.upload(file=str(path), config={"mime_type": mime_type})
        deadline = time.monotonic() + 900
        while str(field(uploaded, "state", "")).split(".")[-1] == "PROCESSING":
            if time.monotonic() > deadline:
                raise TimeoutError("Upload processing timed out. Retry this file later.")
            time.sleep(2)
            uploaded = client.files.get(name=uploaded.name)
        if str(field(uploaded, "state", "")).split(".")[-1] == "FAILED":
            raise RuntimeError("Google could not process the audio upload.")
        response = client.interactions.create(
            model=MODEL,
            input=[{"type": "audio", "uri": uploaded.uri, "mime_type": mime_type}],
            generation_config={"transcription_config": config},
            store=False,
        )
        return parse_interaction(response, offset, segment)
    finally:
        if uploaded is not None:
            try:
                client.files.delete(name=uploaded.name)
            except Exception:
                print("⚠️ Remote audio cleanup failed; check uploaded files in Google AI Studio.")


def annotated_text(words):
    """Readable word annotations without altering the plain transcript."""
    lines = []
    for word in words:
        prefix = f"[{word['speaker']}] " if word["speaker"] else ""
        if word["start_seconds"] is not None:
            prefix += f"[{word['start_seconds']:.3f}s] "
        lines.append(prefix + word["text"])
    return "\n".join(lines) + ("\n" if lines else "")
