# ZMO AI Pipelines

[![Tests](https://github.com/fmadore/zmo-ai-pipelines/actions/workflows/tests.yml/badge.svg)](https://github.com/fmadore/zmo-ai-pipelines/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](pyproject.toml)

Reproducible Google Colab workflows for research transcription, OCR/HTR, and
source-grounded summaries with the Gemini API.

The notebooks are designed for researchers who need usable outputs without
writing Python, while retaining enough provenance to audit how each result was
produced. AI output is not ground truth: validate a representative sample before
using a pipeline at scale or citing its results.

## Open a tool in Google Colab

Choose what you want to do and click its **Open in Colab** button. No installation
on your computer is needed. In Colab, start at Step 1 and follow the instructions
in order. Read the privacy requirements below before uploading research material.

| What do you want to do? | Open the notebook |
| --- | --- |
| **Transcribe audio or video** into text | [![Open Audio Transcription in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fmadore/zmo-ai-pipelines/blob/main/Audio_Transcription_Colab.ipynb) |
| **Read scanned or handwritten documents** (OCR/HTR) | [![Open OCR and HTR in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fmadore/zmo-ai-pipelines/blob/main/OCR_HTR_Colab.ipynb) |
| **Summarise texts and extract keywords** | [![Open Summaries and Keywords in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fmadore/zmo-ai-pipelines/blob/main/Summary_Colab.ipynb) |

## Important privacy requirement

These notebooks target institutional use in Germany/EEA. Use a billing-enabled
Google Cloud project and obtain any ethics, consent, confidentiality, copyright,
and DPO approval required for the material. The current
[Gemini API Additional Terms](https://ai.google.dev/gemini-api/terms) distinguish
EEA/Switzerland/UK use and restrict how API clients may be made available there.

Outside those regions, Google states that unpaid-service inputs and outputs may
be used to improve products and reviewed by humans. Do not submit sensitive,
confidential, or personal data through an unpaid service. Billing is not a
substitute for institutional authorization.

## Notebooks

| Notebook | Purpose | Important behavior |
| --- | --- | --- |
| `Audio_Transcription_Colab.ipynb` | Audio/video transcription with Gemini 3.5 Transcribe | Verbatim or Smart; language hints; optional voices and word times; separate run folders |
| `OCR_HTR_Colab.ipynb` | Printed OCR and handwritten-text recognition | Separate diplomatic and normalized modes; high image resolution and medium PDF resolution; bounded page concurrency |
| `Summary_Colab.ipynb` | Summaries and 5–10 validated keywords from text or `.xlsx` | Preserves worksheets/formulas/styles; atomic resumable checkpoints; synchronous and 50%-cost asynchronous Batch paths |

Every completed result is accompanied by a `provenance.json` record containing
the source SHA-256, fixed requested model, concrete model version when reported by
the response, exact prompt and prompt hash (empty for prompt-free audio), helper
hash, SDK/Python versions, settings, completion status, and available usage data.
Source content is not copied into provenance, except any terms explicitly supplied
as vocabulary hints or included by the researcher in instructions. Treat sidecars
as research data too.

## Fixed model releases

Audio uses `gemini-3.5-transcribe`; the table below applies to OCR and Summary.
The repository never uses a `-latest` alias. A reviewed repository update is
required to change a model:

| Choice | Model ID | Input/output price per 1M tokens* |
| --- | --- | --- |
| Pro | `gemini-3.1-pro-preview` | $2 / $12 up to 200k input tokens; $4 / $18 above 200k |
| Flash | `gemini-3.7-flash` | $0.75 / $3.75 through 31 December 2026; $1.50 / $7.50 from 1 January 2027 |
| Flash Lite | `gemini-3.5-flash-lite` | $0.30 / $2.50 |

\*Prices in effect 14 August 2026; verify the current
[Gemini pricing page](https://ai.google.dev/gemini-api/docs/pricing) before a
large run. The Flash 3.7 rate is introductory and doubles on 1 January 2027, so
a budget estimated this year does not carry over. Batch generation is priced at
50% of standard rates and targets completion within 24
hours ([Batch API](https://ai.google.dev/gemini-api/docs/batch-api)).
Pro 3.1 is a preview model, so its lifecycle risk is higher than a stable release.

Thinking configuration is deliberately omitted so each fixed model uses Google's
tuned default. Reduced safety filters are available only in OCR, off by default, through
an explicit checkbox; that decision is recorded in
provenance. See Google's current
[thinking guidance](https://ai.google.dev/gemini-api/docs/generate-content/thinking)
and [model documentation](https://ai.google.dev/gemini-api/docs/models).

## Quick start

1. Open the required notebook in Google Colab.
2. Run Step 1. It installs exact tested package versions and downloads
   all pipeline modules from the immutable commit recorded in the notebook.
3. Step 1 verifies every module SHA-256 before importing any downloaded code.
4. Add `GEMINI_API_KEY` through Colab Secrets and enable notebook access.
5. Connect Drive to save recoverable checkpoints for all three pipelines, choose source
   files, inspect settings, and test a small representative sample.
6. Download the current run's ZIP even when Drive is connected.

Mounting Drive lets notebook code access files exposed by that mount. Review the
notebook and its pinned helper before authorization; see the
[Colab FAQ](https://research.google.com/colaboratory/faq.html).

## Reproducibility and durability

- Direct notebook dependencies are exact versions verified from PyPI.
- All executable modules are loaded from an immutable Git commit and verified by SHA-256.
- Notebooks are generated from UI templates with `python scripts/build_notebooks.py`.
  Their install constraints come from the same tested dependency lock as CI.
- Model IDs are fixed and no silent fallback is permitted.
- Local files are written atomically or flushed after each incremental append.
- Drive copies use same-directory temporary files, retries, and final verification.
- A transient Drive failure does not permanently disable later synchronization.
- Output names include the source hash and configuration identity, avoiding
  collisions between different files with the same stem.
- Recovery ZIPs package registered exports, immutable unit records, review history,
  and the run manifest. Original source files and API keys are not included.

All pipelines identify runs by source bytes, model, complete prompts, settings, and
software version. A new runtime can restore a matching Drive run or imported ZIP.
Completed rows, pages, and audio segments are reused; incomplete units remain retryable.
Summary marks missing formula caches and writes generated Excel cells as literal text.
Existing AI columns require an explicit new/replace/error policy.

Step 5 previews request counts, PDF text-layer samples, and optional price estimates.
Step 6 offers a review queue with source previews, a reproducible random sample,
and separate corrections with reviewer history. Audio word times produce SRT/WebVTT.
`records.jsonl` provides stable source IDs and per-unit metadata for downstream research.
See [run and recovery instructions](docs/runs.md), including older-release checkpoints.

## Methodological choices

OCR/HTR offers two representations that must not be conflated:

- **Diplomatic:** preserves line breaks, punctuation, spelling, and end-of-line
  hyphenation.
- **Normalized reading text:** joins visually wrapped lines and removes only
  clear line-break hyphens while preserving wording and spelling.

Audio uses `gemini-3.5-transcribe` through the Interactions API, without a prompt.
Choose Verbatim for a research transcript or Smart for an edited reading copy.
Voice labels and word times require Verbatim; vocabulary hints cannot accompany
either feature. Automatic language detection is the default. Long recordings are
split without overlap, and speaker identities are explicitly scoped to each segment.
Check segment joins manually. See the [audio guide](docs/transcription.md).

Summary source text is JSON-quoted inside a data delimiter and covered by a
system instruction that treats embedded commands as source data. Structured
output enforces shape and 5–10 keywords; semantic validation remains necessary.
Very long text uses a conservative map/reduce path. Google's
[prompt-design](https://ai.google.dev/gemini-api/docs/prompting-strategies) and
[structured-output](https://ai.google.dev/gemini-api/docs/generate-content/structured-output)
guidance informed these choices.

Use [`scripts/evaluate_text.py`](scripts/evaluate_text.py) and the protocol in
[`docs/evaluation.md`](docs/evaluation.md) to calculate CER/WER against locally
held, manually checked fixtures. Sensitive fixtures should not be committed.

## Command-line use

Install with Python 3.12, then use the same tested pipeline modules outside Colab:

```sh
python -m pip install -c requirements-dev.lock -e .
zmo-pipelines preflight summary source.xlsx --config summary.json
zmo-pipelines run summary source.xlsx --config summary.json --output results --mirror drive/runs
zmo-pipelines status results/RUN_ID
zmo-pipelines resume results/RUN_ID --source source.xlsx
zmo-pipelines export results/RUN_ID recovery.zip
```

Set `GEMINI_API_KEY` in the environment for network operations. No key is needed
for preflight, status, review, exports, corpus evaluation, or PDF text-layer extraction.
Example configurations and Batch controls are in [docs/runs.md](docs/runs.md).

## Development

The project targets the current Colab Python 3.12 generation. Google documents
available images on the
[Colab runtime versions page](https://research.google.com/colaboratory/runtime-version-faq.html).

```powershell
C:/Users/frede/AppData/Local/Programs/Python/Python312/python.exe -m venv .venv
.venv/Scripts/python.exe -m pip install --constraint requirements-dev.lock --editable ".[dev]"
.venv/Scripts/ruff.exe check .
.venv/Scripts/python.exe -m pytest
```

Python 3.12 is the supported and CI-tested runtime. Both CI and notebook setup
constrain dependencies with `requirements-dev.lock`. ffmpeg and ffprobe are required
for audio duration checks, long recordings, and video soundtrack extraction.

CI checks lint, generated notebook freshness, module hashes, every UI cell offline,
workbook round-trips, recovery/Batch failure paths, media handling, and evaluation metrics. GitHub Actions are pinned to
immutable commit SHAs.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the release sequence and
[`docs/architecture.md`](docs/architecture.md) for API/design decisions.

## Limitations

- Gemini output can omit, normalize, or hallucinate content.
- Recovery requires a surviving Drive checkpoint or downloaded recovery ZIP plus
  the unchanged original source. Work completed since the last mirror/export can
  be lost in a runtime reset. Use one active writer per run.
- Request estimates are planning tools, not billing caps. A process killed during
  a remote request can leave an uncertain outcome; inspect before retrying.
- A `provenance.json` file documents a run; it does not prove output accuracy.
- `openpyxl` preserves ordinary `.xlsx` workbook structures but may not retain
  every vendor-specific Excel extension. Test irreplaceable workbooks on copies.
- Formula source values rely on cached results; recalculate and save the workbook
  in Excel or LibreOffice before upload if caches are empty.
- Batch results must be collected promptly; remote results are retained for a
  limited period.
- No live Gemini call runs in CI because credentials and research data must not
  enter the test environment.

## Citation

If a pipeline contributed to published work, cite the software as well as the
sources. Machine-readable metadata is in [`CITATION.cff`](CITATION.cff), which
GitHub renders under **Cite this repository** in the sidebar.

> Madore, F. (2026). *ZMO AI Pipelines* (version 2026.9.27) [Computer software].
> https://github.com/fmadore/zmo-ai-pipelines

State the pipeline, the fixed model ID, and the run date in your methods
section; the `provenance.json` sidecar records the exact values.

## License

[MIT](LICENSE). Created by [Frédérick Madore](https://www.frederickmadore.com/)
for the [Leibniz-Zentrum Moderner Orient (ZMO)](https://www.zmo.de/).

## Repository review

See [the September 2026 review](docs/review-2026-09-08.md) for findings,
implemented changes, remaining priorities and validation limits.
