import json

import zmo_cli
from zmo_state import RunStore, UnitResult
from zmo_summary import configuration


def test_cli_status_export_import_and_review_without_credentials(tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    source = tmp_path / "source.txt"
    source.write_text("source")
    store = RunStore.open(tmp_path / "runs", source, configuration("model"))
    store.record(UnitResult("text", "complete", text="raw"))
    parse = zmo_cli.parser().parse_args
    result = zmo_cli.execute(parse(["status", str(store.directory)]))
    assert result["units"] == [{"id": "text", "status": "complete"}]
    correction = tmp_path / "correction.txt"
    correction.write_text("corrected")
    zmo_cli.execute(
        parse(
            [
                "review",
                str(store.directory),
                "--unit",
                "text",
                "--text-file",
                str(correction),
                "--reviewer",
                "editor",
            ]
        )
    )
    archive = tmp_path / "recovery.zip"
    zmo_cli.execute(parse(["export", str(store.directory), str(archive)]))
    restored = zmo_cli.execute(
        parse(["import", str(archive), "--output", str(tmp_path / "restored")])
    )
    run = RunStore.load(restored["run"])
    assert run.manifest["reviews"]
    assert run.unit("text")["text"] == "raw"


def test_cli_preflight_and_module_entry_point(tmp_path, capsys):
    source = tmp_path / "source.txt"
    source.write_text("test source")
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"model": "model"}))
    zmo_cli.main(["preflight", "summary", str(source), "--config", str(config)])
    assert json.loads(capsys.readouterr().out)["estimated_requests"] == 1
