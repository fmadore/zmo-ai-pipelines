from __future__ import annotations

import ast
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import zmo_transcribe as zt


def response(status="completed"):
    return SimpleNamespace(status=status, output_text="Hello", steps=[{
        "content": [{"annotations": [{"type": "word_info", "text": "Hello",
                                      "start_offset": "0s", "end_offset": "0.4s",
                                      "speaker": "spk_1"}]}]}])


@pytest.mark.parametrize("kwargs", [
    {"mode": "smart", "speakers": True},
    {"mode": "smart", "timestamps": True},
    {"vocabulary": ["ZMO"], "timestamps": True},
    {"vocabulary": ["ZMO"], "speakers": True},
    {"vocabulary": [str(i) for i in range(1001)]},
])
def test_invalid_options_fail_before_upload(kwargs):
    with pytest.raises(ValueError):
        zt.configuration(**kwargs)


def test_configuration_and_duration_limits():
    assert zt.configuration()["language_codes"] == []
    config = zt.configuration(languages=["fr-FR"], speakers=True, timestamps=True)
    assert config == {"language_codes": ["fr-FR"], "mode": {
        "type": "verbatim", "diarization_mode": "speaker", "timestamp_granularities": ["word"]}}
    assert zt.segment_limit(config) == 1800
    assert zt.segment_limit(zt.configuration(mode="smart")) == 3600
    assert zt.configuration(vocabulary=["ZMO", "ZMO", " "])["custom_vocabulary"] == ["ZMO"]


def test_zero_timestamps_shift_and_speakers_are_scoped():
    parsed = zt.parse_interaction(response(), offset=1800, segment=2)
    assert parsed["words"][0]["start_seconds"] == 1800
    assert parsed["words"][0]["end_seconds"] == 1800.4
    assert parsed["words"][0]["speaker"] == "segment-2:spk_1"
    assert "[1800.000s]" in zt.annotated_text(parsed["words"])
    with pytest.raises(RuntimeError):
        zt.parse_interaction(response("failed"))


@pytest.mark.parametrize("failure", [False, True])
def test_request_is_prompt_free_and_upload_deleted_on_success_or_failure(failure):
    sent, deleted = [], []

    def create(**kwargs):
        sent.append(kwargs)
        if failure:
            raise RuntimeError("quota")
        return response()

    client = SimpleNamespace(files=SimpleNamespace(
        upload=lambda **kwargs: SimpleNamespace(name="file", uri="uri", state="ACTIVE"),
        delete=lambda **kwargs: deleted.append(kwargs)),
        interactions=SimpleNamespace(create=create))
    if failure:
        with pytest.raises(RuntimeError, match="quota"):
            zt.transcribe(client, "audio.mp3", "audio/mpeg", zt.configuration())
    else:
        assert zt.transcribe(client, "audio.mp3", "audio/mpeg", zt.configuration())["text"]
    assert sent[0]["store"] is False
    assert sent[0]["model"] == zt.MODEL
    assert sent[0]["input"] == [{"type": "audio", "uri": "uri", "mime_type": "audio/mpeg"}]
    assert deleted == [{"name": "file"}]


def test_notebook_adapter_matches_tested_module():
    root = Path(__file__).resolve().parents[1]
    notebook = json.loads((root / "Audio_Transcription_Colab.ipynb").read_text(encoding="utf-8"))
    setup = "".join(notebook["cells"][2]["source"])
    assignment = next(
        line for line in setup.splitlines() if line.startswith("TRANSCRIBE_SOURCE = ")
    )
    source = ast.literal_eval(assignment.split(" = ", 1)[1])
    assert source == (root / "zmo_transcribe.py").read_text(encoding="utf-8")


def test_real_sdk_response_types():
    from google.genai._gaos.types.interactions import Interaction

    item = Interaction.model_validate({
        "status": "completed", "output_text": "Hello", "steps": [{
            "type": "model_output", "content": [{"type": "text", "text": "Hello",
                "annotations": [{"type": "word_info", "text": "Hello", "speaker": "spk_1",
                                 "start_offset": "0s", "end_offset": "0.4s"}]}]}],
    })
    result = zt.parse_interaction(item)
    assert result["text"] == "Hello"
    assert result["words"][0]["start_seconds"] == 0
