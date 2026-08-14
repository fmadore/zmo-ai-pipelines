# Architecture decisions

## Fixed model releases

Research runs use `gemini-3.1-pro-preview`, `gemini-3.7-flash`, or
`gemini-3.5-flash-lite`. Moving `-latest` aliases are prohibited. There is no
silent model fallback: an unavailable release stops at preflight so the user can
make and record a deliberate choice.

Model-tuned thinking defaults are retained by omitting `thinking_config` unless
an expert explicitly supplies a value. Sampling parameters are likewise omitted.

## GenerateContent remains the execution API

The Interactions API became generally available in 2026 and is recommended by
Google for new projects. This repository deliberately retains `generateContent`
for now because the [Interactions API overview](https://ai.google.dev/gemini-api/docs/interactions-overview)
documents two current gaps that matter here:

- custom safety settings are unavailable;
- the Batch API is available only with `generateContent`.

Interactions also stores interactions by default unless `store=false` is used.
A future migration must preserve no-storage behavior, archival safety consent,
Batch processing, provenance, and output compatibility. It must be benchmarked
per pipeline rather than applied as a mechanical SDK rename.

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
- requested fixed model and concrete response model version(s);
- exact prompt, prompt SHA-256, and settings;
- helper version/hash and SDK/Python versions;
- finish reasons and token usage.

Source content and API keys are never written into provenance.

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
video MIME types are explicit. Long audio is transcoded to mono 16 kHz MP3 and
split with overlap; the loop stops once the preceding segment reaches the end,
preventing a redundant tail.

OCR uses high media resolution for standalone images and medium for PDFs, in line
with the current [media-resolution guidance](https://ai.google.dev/gemini-api/docs/generate-content/media-resolution).

