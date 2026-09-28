import json
import zipfile
from pathlib import Path

import pytest

import zmo_state as state
from zmo_exports import export_records, save_review
from zmo_state import RunConfig, RunStore, UnitResult, import_recovery, stage_file


def make_store(tmp_path, **kwargs):
    source = tmp_path / "source.txt"
    source.write_text("source")
    return RunStore.open(tmp_path / "runs", source, RunConfig("summary", "model"), **kwargs), source


def test_colliding_basenames_and_identical_bytes_preserve_source_paths(tmp_path):
    paths = []
    for directory, text in [("one", "first"), ("two", "second"), ("three", "first")]:
        source = tmp_path / directory / "same.txt"
        source.parent.mkdir()
        source.write_text(text)
        paths.append(stage_file(source, tmp_path / "staged"))
    assert len(set(paths)) == 3
    assert [p.read_text() for p in paths] == ["first", "second", "first"]
    assert all(p.name == "same.txt" for p in paths)


def test_copy_retries_silent_corruption_before_publish(tmp_path, monkeypatch):
    source, output = tmp_path / "source", tmp_path / "out"
    source.write_bytes(b"correct")
    real = state.shutil.copyfile
    calls = []

    def copy(src, dst):
        calls.append(dst)
        if len(calls) == 1:
            Path(dst).write_bytes(b"corrupt")
        else:
            real(src, dst)

    monkeypatch.setattr(state.shutil, "copyfile", copy)
    state.verified_copy(source, output, delay=0)
    assert len(calls) == 2 and output.read_bytes() == b"correct"


def test_resume_signature_includes_settings_and_new_run_guards_jobs(tmp_path):
    store, source = make_store(tmp_path)
    store.record(UnitResult("row-1", "complete", text="result"))
    assert RunStore.open(tmp_path / "runs", source, RunConfig("summary", "model")).complete("row-1")
    other = RunStore.open(tmp_path / "runs", source, RunConfig("summary", "different"))
    assert other.directory != store.directory and not other.complete("row-1")
    store.manifest["jobs"].append({"state": "submitted"})
    store.save()
    with pytest.raises(ValueError, match="active Batch"):
        RunStore.open(tmp_path / "runs", source, RunConfig("summary", "model"), new_run=True)
    source.write_text("changed")
    with pytest.raises(ValueError, match="Source differs"):
        store.check_source(source)


def test_mirror_failure_preserves_previous_generation_and_recovery(tmp_path, monkeypatch):
    store, _ = make_store(tmp_path, mirror_root=tmp_path / "drive")
    store.record(UnitResult("row-1", "complete", text="first"))
    export_records(store)
    assert store.sync()
    remote = tmp_path / "drive" / store.directory.name
    store.record(UnitResult("row-2", "complete", text="second"))
    original = state.verified_copy
    monkeypatch.setattr(
        state, "verified_copy", lambda *a, **k: (_ for _ in ()).throw(OSError("offline"))
    )
    assert store.sync() is False
    monkeypatch.setattr(state, "verified_copy", original)
    recovered = RunStore.restore(remote, tmp_path / "restored")
    assert recovered.complete("row-1") and recovered.unit("row-2") is None
    assert (recovered.directory / "provenance.json").exists()


def test_recovery_zip_keeps_full_review_history_raw_data_and_provenance(tmp_path):
    store, _ = make_store(tmp_path)
    store.record(UnitResult("row-1", "complete", text="raw"))
    save_review(store, "row-1", "first correction", "reviewer")
    save_review(store, "row-1", "second correction", "reviewer")
    archive = store.export_recovery(tmp_path / "recovery.zip")
    recovered = import_recovery(archive, tmp_path / "restored")
    latest = json.loads(
        (recovered.directory / recovered.manifest["reviews"]["row-1"]["path"]).read_text()
    )
    previous = json.loads((recovered.directory / latest["previous"]["path"]).read_text())
    assert previous["corrected_text"] == "first correction"
    assert recovered.unit("row-1")["text"] == "raw"
    assert (recovered.directory / "provenance.json").is_file()
    with zipfile.ZipFile(archive) as bundle:
        assert "source.txt" not in bundle.namelist()
    with pytest.raises(FileExistsError):
        import_recovery(archive, tmp_path / "restored")


@pytest.mark.parametrize("name", ["../escape", "/absolute", "a\\b"])
def test_recovery_rejects_path_traversal(tmp_path, name):
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr(name, "bad")
    with pytest.raises(ValueError, match="Unsafe"):
        import_recovery(archive, tmp_path / "out")


def test_recovery_rejects_tampered_registered_bytes(tmp_path):
    store, _ = make_store(tmp_path)
    store.record(UnitResult("row-1", "complete", text="value"))
    archive = store.export_recovery(tmp_path / "good.zip")
    with zipfile.ZipFile(archive) as source, zipfile.ZipFile(tmp_path / "bad.zip", "w") as dest:
        for name in source.namelist():
            dest.writestr(name, b"bad" if name.startswith("units/") else source.read(name))
    with pytest.raises(ValueError, match="corrupted"):
        import_recovery(tmp_path / "bad.zip", tmp_path / "out")


def test_legacy_active_batch_prevents_accidental_paid_restart(tmp_path):
    store, source = make_store(tmp_path)
    legacy = tmp_path / "runs" / "old.checkpoint.json"
    legacy.write_text(
        json.dumps(
            {
                "kind": "batch",
                "state": "submitted",
                "signature": {"source_sha256": state.file_sha256(source)},
            }
        )
    )
    with pytest.raises(ValueError, match="older-release Batch"):
        RunStore.open(tmp_path / "runs", source, RunConfig("summary", "model"))


def test_retry_preserves_attempt_history_and_review_revision_identity(tmp_path):
    store, _ = make_store(tmp_path)
    store.record(UnitResult("page-1", "truncated", text="old raw"))
    save_review(store, "page-1", "correction", "editor")
    store.record(UnitResult("page-1", "complete", text="new raw"))
    export_records(store)
    record = json.loads((store.directory / "records.jsonl").read_text())
    assert record["review"]["matches_current_output"] is False
    previous = store.unit("page-1")["previous"]
    assert json.loads((store.directory / previous["path"]).read_text())["text"] == "old raw"
    archive = store.export_recovery(tmp_path / "history.zip")
    restored = import_recovery(archive, tmp_path / "restored")
    assert (restored.directory / previous["path"]).is_file()
