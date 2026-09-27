# Changelog

## 2026.9.27

- Extracted all processing into shared, tested modules with a CLI and generated Colab UIs.
- Added content-verified run manifests, per-unit resume, recovery ZIP import/export,
  historical attempts/reviews, verified Drive copies, and source/configuration guards.
- Fixed staging collisions, Excel formula injection, missing formula caches, stale AI
  statuses, strict JSON validation, incomplete OCR handling, and upload-poll cleanup.
- Made Batch submission intent durable; block duplicate/mode-switch submissions,
  split JSONL jobs, reconcile ambiguous creates, and defer cleanup until outputs are safe.
- Replaced whole-recording decoding with streaming ffmpeg segmentation; summaries
  read worksheets linearly and checkpoint bounded map/reduce work.
- Added scope/price preflight, explicit PDF text-layer extraction, source review with
  separate corrections, SRT/WebVTT, JSONL, and stratified offline A/B CER/WER evaluation.
- Aligned version metadata and Python 3.12 support, refreshed exact dependency pins,
  removed pydub/audioop, and unified notebook/CI dependency constraints.


## Unreleased — 2026-09-08

- Migrate audio to Gemini 3.5 Transcribe with Verbatim/Smart, language hints,
  vocabulary hints, optional voice labels and word timestamps; remove generative prompts.
- Preserve short original audio, apply documented duration limits, scope speakers to
  segments, and save exact text, annotations and provenance in separate run folders.
- Bundle a testable audio adapter directly into Colab; retain the immutable common helper.
- Update google-genai to 2.22.0, verified against PyPI on 2026-09-08.
- Clarify setup, Secrets access, billing, outputs and recovery guidance across notebooks.
- Harden Summary Batch row reconciliation and system instructions; remove unused
  per-document token-count requests. Preserve edited OCR prompts on setup reruns.
- Add repository review and audio migration/evaluation guidance.


## 2026-08-14

- Moved the fixed Flash release from `gemini-3.6-flash` to `gemini-3.7-flash`.
  Runs before this release remain identified by the prior model ID in their
  `.provenance.json` sidecars. Pro 3.1 and Flash Lite 3.5 are unchanged.
- Repinned the notebook helper commit/SHA-256 for the new helper version.

## 2026-07-31

- Fixed the Summary `send_text(..., usage_sink=...)` runtime failure.
- Replaced moving model aliases with fixed Pro 3.1, Flash 3.6, and Flash Lite 3.5 IDs.
- Pinned exact Colab dependencies and verified the helper commit/SHA-256 before import.
- Added response-model provenance, source/prompt hashes, collision-safe outputs, and client cleanup.
- Made reduced archival safety filters an explicit, recorded opt-in.
- Added MIME-safe video handling and overlapping, non-redundant audio segmentation.
- Split OCR/HTR into diplomatic and normalized modes; use medium PDF/high image resolution.
- Preserved `.xlsx` workbooks, added atomic/restorable checkpoints and explicit row statuses.
- Added keyed Batch submission/collection and long-text map/reduce summaries.
- Added tests, pinned CI actions/dependencies, CER/WER tooling, architecture/evaluation docs, and MIT license.

