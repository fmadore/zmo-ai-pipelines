"""Durable, content-verified run state shared by notebooks and command-line jobs."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import time
import uuid
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

VERSION = "2026.9.27"
SCHEMA_VERSION = 2
TERMINAL_JOBS = {"collected", "JOB_STATE_FAILED", "JOB_STATE_CANCELLED", "JOB_STATE_EXPIRED"}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def file_sha256(path, chunk_size=1024 * 1024):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_hash(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()
    ).hexdigest()


def atomic_write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = content.encode("utf-8") if isinstance(content, str) else content
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".write-", delete=False) as out:
            temporary = Path(out.name)
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temporary, path)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)
    return path


def write_json(path, value):
    return atomic_write(
        path, json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    )


def verified_copy(source, destination, attempts=3, delay=1.0):
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve():
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    expected = file_sha256(source)
    error = None
    for attempt in range(attempts):
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                dir=destination.parent, prefix=".copy-", delete=False
            ) as handle:
                temporary = Path(handle.name)
            shutil.copyfile(source, temporary)
            if file_sha256(temporary) != expected:
                raise OSError("Copy checksum differs from the source")
            with temporary.open("rb") as handle:
                os.fsync(handle.fileno())
            os.replace(temporary, destination)
            if file_sha256(destination) != expected:
                raise OSError("Saved copy checksum differs from the source")
            return destination
        except OSError as exc:
            error = exc
            if attempt + 1 < attempts:
                time.sleep(delay * 2**attempt)
        finally:
            if temporary:
                temporary.unlink(missing_ok=True)
    raise OSError(f"Could not verify copy of {source.name}: {error}") from error


def safe_name(value):
    name = re.sub(r"[^\w. -]", "_", str(value)).strip(" .")[:100]
    return name or "source"


def stage_file(source, directory):
    """Distinct source paths never collide, including identical basenames."""
    source = Path(source)
    identity = json_hash({"path": str(source.resolve()), "sha256": file_sha256(source)})[:20]
    destination = Path(directory) / identity / source.name
    return verified_copy(source, destination)


def stage_bytes(name, data, directory):
    name = Path(name).name
    identity = json_hash({"name": name, "sha256": hashlib.sha256(data).hexdigest()})[:20]
    return atomic_write(Path(directory) / identity / name, data)


@dataclass(frozen=True)
class RunConfig:
    pipeline: str
    model: str
    prompt: str = ""
    options: dict = field(default_factory=dict)
    engine_version: str = VERSION


@dataclass
class UnitResult:
    unit_id: str
    status: str
    text: str = ""
    raw: str = ""
    locator: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    error: str = ""
    words: list = field(default_factory=list)
    keywords: list = field(default_factory=list)
    kind: str = "result"


def _relative(value):
    value = str(value)
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or "\\" in value or str(path) != value:
        raise ValueError(f"Unsafe artifact path: {value!r}")
    return Path(*path.parts)


class RunStore:
    """A manifest references immutable unit records and artifact objects.

    Objects are copied before their manifest. An interrupted mirror therefore
    leaves the previous manifest and all of its referenced bytes recoverable.
    Source documents and credentials are never included in recovery archives.
    """

    def __init__(self, directory, manifest, mirror_root=None):
        self.directory = Path(directory)
        self.manifest = manifest
        self.mirror_root = Path(mirror_root) if mirror_root else None
        self.last_sync_error = None

    @classmethod
    def open(cls, root, source, config, *, mirror_root=None, new_run=False, source_id=None):
        root, source = Path(root), Path(source)
        source_info = {
            "name": source.name,
            "size_bytes": source.stat().st_size,
            "sha256": file_sha256(source),
        }
        source_info["id"] = source_id or "sha256:" + source_info["sha256"]
        if config.pipeline == "summary":
            for folder in (root, Path(mirror_root) if mirror_root else root):
                for legacy in folder.glob("*.checkpoint.json"):
                    try:
                        record = json.loads(legacy.read_text(encoding="utf-8"))
                    except (OSError, ValueError):
                        continue
                    if (
                        record.get("kind") == "batch"
                        and record.get("signature", {}).get("source_sha256")
                        == source_info["sha256"]
                        and record.get("state") not in TERMINAL_JOBS
                    ):
                        raise ValueError(
                            "An older-release Batch checkpoint exists. Collect or cancel it "
                            "with its original notebook before starting this source again: "
                            + str(legacy)
                        )
        settings = asdict(config)
        signature = json_hash(
            {"source": source_info, "config": settings, "schema_version": SCHEMA_VERSION}
        )
        prefix = f"{safe_name(source.stem)}_{signature[:20]}"
        root.mkdir(parents=True, exist_ok=True)
        candidates = sorted(root.glob(prefix + "*"), reverse=True)
        if mirror_root:
            for remote in sorted(Path(mirror_root).glob(prefix + "*"), reverse=True):
                if remote.is_dir() and not (root / remote.name).exists():
                    cls.restore(remote, root)
            candidates = sorted(root.glob(prefix + "*"), reverse=True)
        matching = []
        for candidate in candidates:
            if candidate.is_dir():
                existing = cls.load(candidate, mirror_root=mirror_root)
                if existing.manifest["signature"] == signature:
                    matching.append(existing)
        if new_run:
            if any(run.active_jobs for run in matching):
                raise ValueError(
                    "An active Batch job exists. Collect or cancel it before restarting."
                )
        elif matching:
            return max(matching, key=lambda run: run.manifest["created_utc"])
        run_id = prefix + "_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        run_id += "_" + uuid.uuid4().hex[:6]
        directory = root / run_id
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "run_id": run_id,
            "signature": signature,
            "source": source_info,
            "config": settings,
            "created_utc": utc_now(),
            "updated_utc": utc_now(),
            "state": "ready",
            "units": {},
            "artifacts": {},
            "jobs": [],
            "reviews": {},
            "generation": 0,
        }
        store = cls(directory, manifest, mirror_root)
        store.save()
        return store

    @staticmethod
    def references(manifest):
        yield from manifest.get("units", {}).values()
        yield from manifest.get("artifacts", {}).values()
        yield from manifest.get("reviews", {}).values()
        yield from manifest.get("review_history", [])
        yield from manifest.get("unit_history", [])

    def check_source(self, source):
        source = Path(source)
        expected = self.manifest["source"]
        if (
            source.stat().st_size != expected["size_bytes"]
            or file_sha256(source) != expected["sha256"]
        ):
            raise ValueError("Source differs from this run; select the original unchanged file")

    @classmethod
    def validate(cls, directory, manifest):
        if manifest.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("Unsupported recovery schema; use its original software release.")
        if _relative(manifest["run_id"]).name != manifest["run_id"]:
            raise ValueError("Invalid run identifier")
        signature = json_hash(
            {
                "source": manifest["source"],
                "config": manifest["config"],
                "schema_version": SCHEMA_VERSION,
            }
        )
        if signature != manifest["signature"]:
            raise ValueError("Run configuration fingerprint does not match")
        for ref in cls.references(manifest):
            path = Path(directory) / _relative(ref["path"])
            if (
                not path.is_file()
                or path.is_symlink()
                or path.stat().st_size != ref["size_bytes"]
                or file_sha256(path) != ref["sha256"]
            ):
                raise ValueError(f"Missing or corrupted recovery artifact: {ref['path']}")

    @classmethod
    def load(cls, directory, *, mirror_root=None):
        directory = Path(directory)
        failures = []
        for filename in ("manifest.json", "manifest.previous.json"):
            try:
                manifest = json.loads((directory / filename).read_text(encoding="utf-8"))
                cls.validate(directory, manifest)
                store = cls(directory, manifest, mirror_root)
                store.materialize()
                if filename != "manifest.json":
                    print("Recovered the previous verified checkpoint.")
                    write_json(directory / "manifest.json", manifest)
                return store
            except (OSError, ValueError, KeyError, TypeError) as exc:
                failures.append(str(exc))
        raise ValueError("No valid checkpoint: " + "; ".join(failures))

    @classmethod
    def restore(cls, remote_directory, root):
        remote = cls.load(remote_directory)
        destination = Path(root) / remote.manifest["run_id"]
        if destination.exists():
            raise FileExistsError(
                "Recovery target already exists; choose a different output folder."
            )
        Path(root).mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".restore-", dir=root))
        try:
            for ref in cls.references(remote.manifest):
                rel = _relative(ref["path"])
                verified_copy(remote.directory / rel, staging / rel)
            write_json(staging / "manifest.json", remote.manifest)
            cls.validate(staging, remote.manifest)
            os.replace(staging, destination)
        finally:
            if staging.exists():
                shutil.rmtree(staging)
        return cls.load(destination)

    @property
    def active_jobs(self):
        return [job for job in self.manifest["jobs"] if job["state"] not in TERMINAL_JOBS]

    def save(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / "manifest.json"
        if path.exists():
            atomic_write(self.directory / "manifest.previous.json", path.read_bytes())
        self.manifest["generation"] += 1
        self.manifest["updated_utc"] = utc_now()
        write_json(path, self.manifest)

    def _store(self, content, directory):
        data = content.encode("utf-8") if isinstance(content, str) else content
        digest = hashlib.sha256(data).hexdigest()
        relative = f"{directory}/{digest}"
        path = self.directory / relative
        if not path.exists():
            atomic_write(path, data)
        return {"path": relative, "sha256": digest, "size_bytes": len(data)}

    def record(self, unit):
        if not re.fullmatch(r"[A-Za-z0-9_.:-]+", unit.unit_id):
            raise ValueError("Unit identifiers must be simple stable keys")
        payload = asdict(unit) | {"signature": self.manifest["signature"], "saved_utc": utc_now()}
        previous = self.manifest["units"].get(unit.unit_id)
        if previous:
            self.manifest.setdefault("unit_history", []).append(previous)
            payload["previous"] = previous
        self.manifest["units"][unit.unit_id] = self._store(
            json.dumps(payload, ensure_ascii=False, allow_nan=False), "units"
        )
        self.save()

    def unit(self, unit_id):
        ref = self.manifest["units"].get(unit_id)
        if not ref:
            return None
        return json.loads((self.directory / _relative(ref["path"])).read_text(encoding="utf-8"))

    def units(self, *, include_chunks=False):
        records = [self.unit(key) for key in self.manifest["units"]]
        return sorted(
            (r for r in records if include_chunks or r.get("kind") != "chunk"),
            key=lambda r: tuple(
                int(p) if p.isdigit() else p for p in re.split(r"(\d+)", r["unit_id"])
            ),
        )

    def complete(self, unit_id):
        record = self.unit(unit_id)
        return bool(record and record["status"] in {"complete", "empty", "skipped-source-error"})

    def artifact(self, name, content):
        if _relative(name).name != name:
            raise ValueError("Export names cannot contain directories")
        ref = self._store(content, "objects")
        self.manifest["artifacts"][name] = ref
        atomic_write(self.directory / name, content)
        self.save()
        return self.directory / name

    def register_artifact(self, path):
        path = Path(path)
        digest = file_sha256(path)
        relative = f"objects/{digest}"
        target = self.directory / relative
        if not target.exists():
            verified_copy(path, target)
        if file_sha256(target) != digest:
            raise ValueError("Artifact changed while it was being registered")
        self.manifest["artifacts"][path.name] = {
            "path": relative,
            "sha256": digest,
            "size_bytes": path.stat().st_size,
        }
        destination = self.directory / path.name
        verified_copy(path, destination)
        self.save()
        return destination

    def materialize(self):
        for name, ref in self.manifest["artifacts"].items():
            if _relative(name).name != name:
                raise ValueError("Invalid export filename")
            target = self.directory / name
            source = self.directory / _relative(ref["path"])
            if not target.exists() or file_sha256(target) != ref["sha256"]:
                verified_copy(source, target)

    def sync(self):
        if self.mirror_root is None:
            return False
        target = self.mirror_root / self.manifest["run_id"]
        try:
            for ref in self.references(self.manifest):
                relative = _relative(ref["path"])
                destination = target / relative
                if not destination.exists() or file_sha256(destination) != ref["sha256"]:
                    verified_copy(self.directory / relative, destination)
            # Keep the prior *remote* generation, not a possibly unsynced local one.
            previous = target / "manifest.json"
            if previous.exists():
                verified_copy(previous, target / "manifest.previous.json")
            verified_copy(self.directory / "manifest.json", target / "manifest.json")
            self.validate(target, self.manifest)
            for name, ref in self.manifest["artifacts"].items():
                verified_copy(target / ref["path"], target / name)
            self.last_sync_error = None
            return True
        except (OSError, ValueError) as exc:
            self.last_sync_error = str(exc)
            print(f"Mirror incomplete; download the recovery ZIP: {exc}")
            return False

    def export_recovery(self, destination):
        self.validate(self.directory, self.manifest)
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        files = {"manifest.json"} | {r["path"] for r in self.references(self.manifest)}
        files |= set(self.manifest["artifacts"])
        with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as tmp:
            temporary = Path(tmp.name)
        try:
            with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for name in sorted(files):
                    reference = self.manifest["artifacts"].get(name)
                    source = reference["path"] if reference else name
                    archive.write(self.directory / source, arcname=name)
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)
        return destination


def import_recovery(archive, root, max_bytes=2 * 1024**3):
    """Validate paths, sizes and hashes before publishing a recovery directory."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".import-", dir=root))
    try:
        with zipfile.ZipFile(archive) as bundle:
            entries = bundle.infolist()
            names = [item.filename for item in entries]
            if (
                len(names) != len(set(names))
                or len(names) > 100_000
                or sum(item.file_size for item in entries) > max_bytes
            ):
                raise ValueError("Recovery ZIP is duplicated or exceeds the size limit")
            for item in entries:
                relative = _relative(item.filename)
                if item.is_dir() or (item.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError("Recovery ZIP must contain ordinary files only")
                with bundle.open(item) as source:
                    destination = staging / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with destination.open("wb") as out:
                        shutil.copyfileobj(source, out)
        manifest = json.loads((staging / "manifest.json").read_text(encoding="utf-8"))
        RunStore.validate(staging, manifest)
        allowed = {"manifest.json"} | {r["path"] for r in RunStore.references(manifest)}
        allowed |= set(manifest["artifacts"])
        if set(names) != allowed:
            raise ValueError("Recovery ZIP contains unregistered or missing files")
        destination = root / manifest["run_id"]
        if destination.exists():
            raise FileExistsError("This run already exists; import into a different output folder.")
        os.replace(staging, destination)
        return RunStore.load(destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
