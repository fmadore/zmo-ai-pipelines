"""Resumable audio transcription and source-timed research exports."""

from __future__ import annotations

import tempfile
from pathlib import Path

import zmo_common as zc
import zmo_transcribe as adapter
from zmo_exports import export_records, subtitle_text
from zmo_media import VIDEO_EXTENSIONS, audio_segments, duration_seconds
from zmo_state import RunConfig, UnitResult


def configuration(**kwargs):
    config = adapter.configuration(**kwargs)
    return RunConfig(
        "audio",
        adapter.MODEL,
        options={
            "transcription": config,
            "segment_limit": adapter.segment_limit(config),
            "overlap_seconds": 0,
            "speaker_scope": "segment",
            "api": "interactions",
            "store": False,
            "encoding_margin_seconds": 0.1,
        },
    )


def preflight(source, options):
    import math
    import shutil

    duration = duration_seconds(source)
    limit = options["segment_limit"]
    if (duration > limit or Path(source).suffix.lower() in VIDEO_EXTENSIONS) and not shutil.which(
        "ffmpeg"
    ):
        raise RuntimeError("ffmpeg is required to extract the soundtrack or split this recording")
    return {
        "source": Path(source).name,
        "duration_seconds": duration,
        "estimated_requests": math.ceil(duration / (limit - 0.1)) if duration > limit else 1,
        "segment_limit_seconds": limit,
    }


def export_audio(store):
    parts, words = [], []
    for unit in store.units():
        if unit["status"] == "complete":
            parts.append(unit["text"])
        else:
            parts.append(f"[ERROR: {unit['unit_id']}, at {unit['locator']['offset_seconds']}s]")
        words.extend(unit["words"])
    store.artifact("transcription.txt", "\n\n".join(parts) + "\n")
    if words:
        store.artifact("transcription.annotated.txt", adapter.annotated_text(words))
        # Diarization-only runs may have no times; do not advertise empty subtitles.
        if any(word.get("start_seconds") is not None for word in words):
            store.artifact("transcription.srt", subtitle_text(words))
            store.artifact("transcription.vtt", subtitle_text(words, webvtt=True))
    export_records(store)


def run(client, source, store, *, on_progress=print):
    store.check_source(source)
    source = Path(source)
    options = store.manifest["config"]["options"]
    plan = preflight(source, options)
    store.manifest["state"] = "running"
    store.save()
    count = 0
    try:
        with tempfile.TemporaryDirectory(prefix="audio-", dir=store.directory) as temporary:
            segments = audio_segments(
                source,
                temporary,
                options["segment_limit"],
                duration=plan["duration_seconds"],
                skip_indices={
                    u["locator"]["segment"] for u in store.units() if u["status"] == "complete"
                },
            )
            for count, (offset, segment) in enumerate(segments, 1):
                key = f"segment-{count}"
                try:
                    if store.complete(key):
                        on_progress(f"{key}: already complete")
                        continue
                    locator = {"segment": count, "offset_seconds": offset}
                    try:
                        response = adapter.transcribe(
                            client,
                            segment,
                            zc.media_mime_type(segment),
                            options["transcription"],
                            offset=offset,
                            segment=count,
                        )
                        result = UnitResult(
                            key,
                            "complete",
                            text=response["text"],
                            raw=response["text"],
                            locator=locator,
                            words=response["words"],
                            metadata=response["metadata"],
                        )
                    except Exception as exc:
                        result = UnitResult(
                            key, "failed", locator=locator, error=adapter.error_message(exc)
                        )
                    store.record(result)
                    export_audio(store)
                    store.sync()
                    on_progress(f"{key}: {result.status}")
                finally:
                    if segment is not None and segment != source:
                        segment.unlink(missing_ok=True)
        store.manifest["state"] = (
            "complete"
            if all(store.complete(f"segment-{i}") for i in range(1, count + 1))
            else "partial"
        )
    except BaseException:
        store.manifest["state"] = "interrupted"
        raise
    finally:
        store.save()
        export_audio(store)
        store.sync()
    return store
