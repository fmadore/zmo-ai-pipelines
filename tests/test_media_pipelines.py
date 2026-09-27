import io
import json
import shutil
import subprocess
from types import SimpleNamespace as NS

import pytest
from pypdf import PdfReader, PdfWriter

import zmo_audio as audio
import zmo_common as common
import zmo_media as media
import zmo_ocr as ocr
from zmo_exports import subtitle_text
from zmo_state import RunStore


def test_failed_media_poll_deletes_known_remote_upload(tmp_path, monkeypatch):
    source = tmp_path / "file.pdf"
    source.write_bytes(b"pdf")
    deleted = []
    client = NS(
        files=NS(
            upload=lambda **kw: NS(name="known", state="PROCESSING"),
            get=lambda **kw: (_ for _ in ()).throw(RuntimeError("poll failed")),
            delete=lambda **kw: deleted.append(kw["name"]),
        )
    )
    monkeypatch.setattr(common.time, "sleep", lambda _: None)
    with pytest.raises(RuntimeError, match="poll failed"):
        common.upload_media(client, path=source, mime_type="application/pdf")
    assert deleted == ["known"]


@pytest.mark.parametrize("fail_second", [False, True])
def test_audio_segment_checkpoint_and_resume(tmp_path, monkeypatch, fail_second):
    source = tmp_path / "source.mp3"
    source.write_bytes(b"audio")
    store = RunStore.open(tmp_path / "runs", source, audio.configuration())
    monkeypatch.setattr(audio, "preflight", lambda *a: {"duration_seconds": 3601})
    monkeypatch.setattr(
        audio, "audio_segments", lambda *a, **k: iter([(0, source), (3599.9, source)])
    )
    calls = []

    def transcribe(*args, segment, **kwargs):
        calls.append(segment)
        if fail_second and segment == 2 and calls.count(2) == 1:
            raise RuntimeError("quota")
        return {"text": f"speech {segment}", "words": [], "metadata": {"usage": {}}}

    monkeypatch.setattr(audio.adapter, "transcribe", transcribe)
    audio.run(None, source, store)
    assert store.manifest["state"] == ("partial" if fail_second else "complete")
    assert "speech 1\n\n" in (store.directory / "transcription.txt").read_text()
    assert ("[ERROR:" in (store.directory / "transcription.txt").read_text()) is fail_second
    restored = RunStore.load(store.directory)
    audio.run(None, source, restored)
    assert restored.manifest["state"] == "complete"
    assert calls == ([1, 2, 2] if fail_second else [1, 2])
    assert len(json.loads((store.directory / "provenance.json").read_text())["units"]) == 2


def test_ocr_truncation_remains_retryable_with_page_provenance(tmp_path, monkeypatch):
    source = tmp_path / "source.pdf"
    writer = PdfWriter()
    for number in (1, 2, 3):
        writer.add_blank_page(width=100 + number, height=200)
    writer.write(source)
    config = ocr.configuration("model", "preserve all whitespace")
    store = RunStore.open(tmp_path / "runs", source, config)
    calls = []

    def send(client, model, config, data, response_sink, **kwargs):
        number = int(PdfReader(io.BytesIO(data)).pages[0].mediabox.width) - 100
        calls.append(number)
        response_sink.append({"model_version": "version", "finish_reason": "MAX_TOKENS"})
        return "  exact\n spacing  ", "truncated" if number == 2 and calls.count(2) == 1 else "ok"

    monkeypatch.setattr(ocr.zc, "send_media", send)
    ocr.run(None, source, store, workers=2)
    assert store.manifest["state"] == "partial"
    assert store.unit("page-2")["status"] == "truncated"
    assert store.unit("page-1")["text"] == "  exact\n spacing  "
    assert store.unit("page-2")["metadata"]["responses"][0]["model_version"] == "version"
    ocr.run(None, source, store, workers=2)
    assert sorted(calls) == [1, 2, 2, 3]
    assert store.manifest["state"] == "complete"


def test_ocr_text_layer_blank_pages_are_flagged_without_remote_calls(tmp_path):
    source = tmp_path / "source.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=200)
    writer.write(source)
    config = ocr.configuration("unused", "", method="text-layer")
    store = RunStore.open(tmp_path / "runs", source, config)
    assert ocr.preflight(source, config.options)["estimated_requests"] == 0
    ocr.run(None, source, store)
    assert store.unit("page-1")["status"] == "needs-ocr"


def test_subtitles_offset_zero_speaker_boundary_and_html_escaping():
    words = [
        {"text": "<Hello>", "start_seconds": 0.0, "end_seconds": 0.4, "speaker": "segment-1:<a>"},
        {"text": "there", "start_seconds": 0.5, "end_seconds": 1.0, "speaker": "segment-1:b"},
    ]
    srt = subtitle_text(words)
    assert "00:00:00,000 --> 00:00:00,400" in srt and "\n2\n" in srt
    vtt = subtitle_text(words, webvtt=True)
    assert vtt.startswith("WEBVTT\n") and "&lt;Hello&gt;" in vtt and "&lt;a&gt;" in vtt
    words[1]["start_seconds"] = -1
    with pytest.raises(ValueError):
        subtitle_text(words)


def test_no_ffmpeg_video_does_not_upload(tmp_path, monkeypatch):
    source = tmp_path / "video.mp4"
    source.write_bytes(b"video")
    monkeypatch.setattr(media.shutil, "which", lambda _: None)
    with pytest.raises(RuntimeError, match="soundtrack"):
        list(media.audio_segments(source, tmp_path, 10, duration=20))


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg unavailable")
def test_real_ffmpeg_segments_use_source_offsets_and_bounded_duration(tmp_path):
    source = tmp_path / "test.wav"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=2.5",
            str(source),
        ],
        check=True,
    )
    segments = list(media.audio_segments(source, tmp_path / "segments", 1.2))
    assert [offset for offset, _ in segments] == pytest.approx([0, 1.1, 2.2])
    assert all(media.duration_seconds(path) <= 1.2 for _, path in segments)
    overlapping = list(media.audio_segments(source, tmp_path / "overlap", 1.2, 0.1))
    assert [offset for offset, _ in overlapping] == pytest.approx([0, 1, 2])


def test_completed_segments_skip_conversion_before_yield(tmp_path, monkeypatch):
    monkeypatch.setattr(media.shutil, "which", lambda name: "/bin/" + name)
    monkeypatch.setattr(
        media.subprocess,
        "run",
        lambda *a, **kw: (_ for _ in ()).throw(AssertionError("must not transcode")),
    )
    assert list(
        media.audio_segments(
            tmp_path / "source.mp3", tmp_path / "out", 1.2, duration=2.5, skip_indices={1, 2, 3}
        )
    ) == [(0, None), (pytest.approx(1.1), None), (pytest.approx(2.2), None)]
