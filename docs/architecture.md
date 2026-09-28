# Architecture

## Modules and interfaces

The notebooks are presentation and configuration layers. Both `NotebookSession` and
`zmo-pipelines` invoke the same `zmo_summary`, `zmo_ocr`, and `zmo_audio` functions.
`zmo_state` owns source identity, configuration, immutable records, manifests, mirror
verification, and recovery. `zmo_exports` owns JSONL/provenance, review, and subtitles.
`zmo_media` prepares bounded audio segments. `zmo_transcribe` is the prompt-free
Interactions adapter. `zmo_evaluate` provides offline accuracy metrics.

`zmo_common` retains the shared Colab widgets, Gemini request helpers, and compatibility
utilities. Its old incremental writer and media wrappers remain for external callers;
the three pipelines use the new run store and segment generator.

## Run identity and persistence

A run signature binds source name, byte count, SHA-256/stable ID, complete configuration,
prompts, model, engine version, and manifest schema. Source hashes are computed at run
opening/validation, not once per row. Same-name uploads are staged in distinct directories.
Every row/page/segment has a stable unit key. Complete units are reused only within the
same verified run; AI Status cells in a newly supplied workbook never establish completion.

Unit records, exports, and review revisions are content-addressed immutable files. A
manifest references their hashes and byte counts. Each local save uses fsync plus atomic
replacement, retaining the prior manifest. Retry histories link previous unit revisions;
review corrections record the exact unit revision they reviewed. Original output is kept.

Mirroring copies and hashes objects first, then publishes and validates the manifest.
It retains the prior remote generation. Failed copies remain retryable. A recovery ZIP
contains the manifest, every referenced object and history record, and readable exports.
Import rejects traversal, symlinks, duplicate/extra files, oversized archives, and corrupt
bytes before publishing a run folder. Original sources and credentials are excluded.

Use one writer per run. Atomic storage does not provide distributed locking. A hard kill
between a provider response and local persistence cannot guarantee exactly-once billing.
The Drive export cadence bounds which locally completed units survive loss of a runtime.

## Batch lifecycle

Persist a submission UUID before uploading; persist the upload handle before creating
its job; persist the returned job name immediately. Each phase is mirrored. An ambiguous
create exception leaves an unresolved intent and blocks automatic resubmission. Reconcile
using the provider display name, attach the exact verified job, or explicitly abandon only
after checking that no remote job exists. Row keys are validated before applying results.

Synchronous mode and a separate restart cannot reuse a run with unresolved Batch work.
Terminal failures/cancellations make incomplete rows eligible for explicit retry. Job
inputs are streamed and split at configured row/byte limits. Long rows are marked for the
bounded synchronous map/reduce path. Export workbook, JSONL, and provenance before marking
a job collected. Delete remote files only after a verified mirror or explicit confirmation
that a recovery ZIP was saved; preserve failed cleanup identifiers for retry.

## Processing boundaries

Summary traverses formula and cached-value worksheets with linear `iter_rows` passes.
Missing formula caches are explicit incomplete units. Output workbooks retain other sheets,
formulas, and normal formatting; generated values are literal strings and validated against
Excel limits. Large summaries persist bounded map results and cap output token requests.

OCR keeps at most one pending request per worker and persists completions as they arrive.
Truncation, failed requests, blank text layers, and incomplete pages remain distinguishable.
PDF text-layer extraction requires an explicit choice after preflight samples. Provider text
is preserved without whitespace normalization. Standalone images use high media resolution;
PDFs use medium. All settings are included in the run identity.

Audio probes with ffprobe and seeks into the original with ffmpeg, yielding one segment at
a time. Short audio stays unchanged. Video uploads contain only extracted soundtracks.
Segment offsets follow source time with an encoder margin; speaker IDs are segment-scoped.
Exact transcript text, word annotations, and SRT/WebVTT exports retain those offsets.

## API and trust boundaries

OCR/Summary retain generateContent and Summary Batch. Audio uses Interactions with
`store=False`; uploaded files are deleted after requests, including polling failures.
Fixed model IDs have no automatic fallback. Thinking/sampling defaults remain model defaults.

Every notebook fetches modules from one immutable Git commit, verifies every digest before
importing, and installs exact direct dependencies with the CI constraints. Colab Secrets is
the preferred key source. Provenance includes source identity, prompts/options, model and
response metadata, module hashes, and SDK/Python versions. API keys are never recorded.
Prompts, vocabulary, transcripts, and review notes may themselves contain research data.
