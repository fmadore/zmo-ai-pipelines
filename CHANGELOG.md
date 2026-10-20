# Changelog

## 2026-10-20

- Moved the fixed Flash release from `gemini-3.7-flash` to `gemini-3.8-flash`.
  Google now routes `gemini-3.7-flash` requests to 3.8 Flash, so the old ID no
  longer selects a fixed model. Pricing is unchanged. Runs before this release
  remain identified by their recorded response model in `.provenance.json`.
  Pro 3.1, Flash Lite 3.5 and Transcribe 3.5 are unchanged.
- Update google-genai to 2.31.0, pypdf to 6.21.1 and ruff to 0.17.1, verified
  against PyPI on 2026-10-20; re-resolved `requirements-dev.lock` on Python 3.12.
- Repinned the notebook helper commit/SHA-256 for the new helper version.

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

