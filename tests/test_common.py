from __future__ import annotations

import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

import zmo_common as zc


def fake_response(text="result", total_tokens=12):
    usage = SimpleNamespace(
        prompt_token_count=7,
        candidates_token_count=5,
        total_token_count=total_tokens,
    )
    candidate = SimpleNamespace(finish_reason="STOP", content=None)
    return SimpleNamespace(
        text=text,
        candidates=[candidate],
        prompt_feedback=None,
        usage_metadata=usage,
        model_version="gemini-3.6-flash-202607",
    )


def test_fixed_model_ids_have_no_latest_aliases():
    assert zc.MODEL_PRO == "gemini-3.1-pro-preview"
    assert zc.MODEL_FLASH == "gemini-3.6-flash"
    assert zc.MODEL_FLASH_LITE == "gemini-3.5-flash-lite"
    assert zc.MODEL_FALLBACK is None
    assert all(
        "latest" not in model
        for model in (zc.MODEL_PRO, zc.MODEL_FLASH, zc.MODEL_FLASH_LITE)
    )


def test_config_uses_model_defaults_and_standard_safety():
    config = zc.build_config(model_id=zc.MODEL_FLASH)
    assert config.thinking_config is None
    assert config.safety_settings is None

    explicit = zc.build_config(model_id=zc.MODEL_PRO, thinking_level="HIGH", safety=True)
    assert explicit.thinking_config.thinking_level.name == "HIGH"
    assert len(explicit.safety_settings) == 4


def test_send_text_contract_collects_usage_and_response_metadata():
    response = fake_response()
    client = SimpleNamespace(
        models=SimpleNamespace(generate_content=lambda **_kwargs: response)
    )
    tokens = []
    responses = []
    text, status = zc.send_text(
        client,
        zc.MODEL_FLASH,
        config=None,
        prompt="source",
        verbose=False,
        usage_sink=tokens,
        response_sink=responses,
    )
    assert (text, status) == ("result", "ok")
    assert tokens == [12]
    assert responses == [
        {
            "model_version": "gemini-3.6-flash-202607",
            "finish_reason": "STOP",
            "prompt_tokens": 7,
            "response_tokens": 5,
            "total_tokens": 12,
        }
    ]


def test_output_names_are_stable_and_collision_resistant(tmp_path):
    first = tmp_path / "one" / "same.pdf"
    second = tmp_path / "two" / "same.pdf"
    first.parent.mkdir()
    second.parent.mkdir()
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    assert zc.output_name_for(first, "_ocr.txt") == zc.output_name_for(first, "_ocr.txt")
    assert zc.output_name_for(first, "_ocr.txt") != zc.output_name_for(second, "_ocr.txt")


def test_atomic_output_and_provenance(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("input", encoding="utf-8")
    output = tmp_path / "output.txt"
    zc.atomic_write_text(output, "complete")
    assert output.read_text(encoding="utf-8") == "complete"

    sidecar = tmp_path / "output.provenance.json"
    zc.write_provenance(
        sidecar,
        source=source,
        model_id=zc.MODEL_FLASH,
        prompt_text="prompt",
        settings={"mode": "test"},
        responses=[zc.response_metadata(fake_response())],
    )
    record = json.loads(sidecar.read_text(encoding="utf-8"))
    assert record["source"]["sha256"] == zc.file_sha256(source)
    assert record["prompt"]["text"] == "prompt"
    assert record["model"]["response_versions"] == ["gemini-3.6-flash-202607"]


def test_drive_folder_cannot_escape_mount(tmp_path, monkeypatch):
    monkeypatch.setattr(zc.DriveHelper, "BASE_PATH", str(tmp_path))
    drive = zc.DriveHelper("Results")
    drive.mounted = True
    assert drive.folder() == tmp_path / "Results"
    with pytest.raises(ValueError):
        drive.folder_name = "../outside"
    with pytest.raises(ValueError):
        drive.folder_name = str(tmp_path.resolve())


def test_incremental_writer_retries_after_transient_mirror_error(tmp_path, monkeypatch):
    local = tmp_path / "local.txt"
    mirror = tmp_path / "drive" / "mirror.txt"
    real_copy = zc.atomic_copy
    calls = {"count": 0}

    def flaky_copy(source, destination, *args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise OSError("transient")
        return real_copy(source, destination, *args, **kwargs)

    monkeypatch.setattr(zc, "atomic_copy", flaky_copy)
    writer = zc.IncrementalWriter(local, mirror, sync_every=1)
    assert writer.last_sync_error
    writer.append("recovered")
    assert writer.last_sync_error is None
    assert mirror.read_text(encoding="utf-8") == "recovered"


def test_overlapping_audio_does_not_create_redundant_tail(tmp_path, monkeypatch):
    class FakeAudio:
        def __init__(self, length):
            self.length = length

        def __len__(self):
            return self.length

        def __getitem__(self, value):
            return FakeAudio(min(self.length, value.stop) - value.start)

        def export(self, path, **_kwargs):
            Path(path).write_bytes(b"mp3")

    class FakeAudioSegment:
        @staticmethod
        def from_file(_path):
            return FakeAudio(150_000)

    fake_pydub = ModuleType("pydub")
    fake_pydub.AudioSegment = FakeAudioSegment
    monkeypatch.setitem(sys.modules, "pydub", fake_pydub)
    segments = zc.split_mono_mp3("recording.mp3", tmp_path, 1, overlap_seconds=2)
    assert [offset for offset, _path in segments] == [0.0, 58.0, 116.0]


def test_chunk_text_preserves_every_character():
    text = ("paragraph one\n\n" * 100) + "the end"
    chunks = zc.chunk_text(text, max_chars=80)
    assert len(chunks) > 1
    assert "".join(chunks) == text


def test_timestamp_shift_only_changes_bracketed_times():
    text = "At 01:02, [00:01:02] Speaker 1 and [Kandahar?]"
    assert zc.shift_timestamps(text, 60) == "At 01:02, [00:02:02] Speaker 1 and [Kandahar?]"
