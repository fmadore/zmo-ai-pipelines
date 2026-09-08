# Architecture decisions

## Fixed model releases

OCR and Summary use `gemini-3.1-pro-preview`, `gemini-3.7-flash`, or
`gemini-3.5-flash-lite`; audio uses `gemini-3.5-transcribe`.
Moving `-latest` aliases and silent model fallbacks are prohibited. OCR/Summary
check availability at preflight; audio reports access errors from the Transcribe
request and does not substitute a generative model.

Model-tuned thinking defaults are retained by omitting `thinking_config` unless
an expert explicitly supplies a value. Sampling parameters are likewise omitted.

## API choice by pipeline

The Interactions API became generally available in 2026 and is recommended by
Google for new projects. OCR and Summary retain `generateContent` because the
[Interactions API overview](https://ai.google.dev/gemini-api/docs/interactions-overview)
documents two current gaps that matter here:

- custom safety settings are unavailable;
- the Batch API is available only with `generateContent`.

Interactions also stores interactions by default unless `store=false` is used.
Audio now uses Interactions with `store=False` and no custom safety setting.
The prompt-free Transcribe adapter lives in `zmo_transcribe.py`. The bundling script
embeds that exact source into the audio setup cell, so unpublished changes work
without a mutable download or a fabricated helper commit. CI compares the embedded
source with the tested module. The existing immutable `zmo_common.py` pin is unchanged.

## Trust boundary

Each notebook installs exact dependencies, downloads `zmo_common.py` from a
recorded commit, verifies its SHA-256, then imports it. The default branch is not
executed. CI verifies that all three recorded hashes equal the repository helper.

Colab Secrets is the preferred key store. Manual key entry remains an explicitly
warned fallback because widget state may be saved into a notebook copy.

Drive folder paths are relative to `My Drive`, cannot contain `..`, and are
resolved beneath the mount. Dynamic filenames/messages are HTML-escaped.

## Output identity and provenance

Output filenames combine a safe source stem, source-content hash, and relevant
configuration identity. Each provenance sidecar includes:

- source name, size, and SHA-256;
- requested fixed model and concrete response model version(s), when reported;
- exact prompt, prompt SHA-256, and settings;
- helper version/hash and SDK/Python versions;
- completion status and available usage data.

API keys are never written into provenance. Prompts and vocabulary hints may
contain researcher-supplied source terms: protect sidecars accordingly.

## Checkpoint ordering

Local text appends are flushed and `fsync`ed. Atomic files are written in the
destination directory and promoted with `os.replace`.

For Summary, the workbook is saved first, then its local manifest. Drive receives
the workbook before the manifest. A manifest is therefore never considered
restorable unless its corresponding output exists and its signature matches the
selected source/configuration. Drive failures retry and do not disable future
sync attempts.

## Batch reconciliation

Summary Batch inputs use JSONL keys of the form `row-N`. The manifest stores the
remote job, input file, exact row mapping, and configuration signature. Collection
uses returned keys—not positional assumptions—to write results into the preserved
worksheet. Uploaded inputs and result files are deleted after successful collection
on a best-effort basis.

## Media handling

Video is never uploaded merely because soundtrack extraction failed. Audio and
video MIME types are explicit. Short audio is sent unchanged. Long audio is split
into mono MP3 segments without
overlap (60 minutes, or 30 with annotations). Speaker IDs are segment-scoped;
no cross-request identity matching is claimed. Both exact API text and structured
word annotations are saved, with absolute numeric offsets. Every audio run gets
a separate directory. Completed segments and provenance are saved after each request;
audio does not yet resume across runtime resets.

OCR uses high media resolution for standalone images and medium for PDFs, in line
with the current [media-resolution guidance](https://ai.google.dev/gemini-api/docs/generate-content/media-resolution).

