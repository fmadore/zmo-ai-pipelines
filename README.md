# ZMO AI Pipelines

Reproducible Google Colab workflows for research transcription, OCR/HTR, and
source-grounded summaries with the Gemini API.

The notebooks are designed for researchers who need usable outputs without
writing Python, while retaining enough provenance to audit how each result was
produced. AI output is not ground truth: validate a representative sample before
using a pipeline at scale or citing its results.

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
| `Audio_Transcription_Colab.ipynb` | Audio/video transcription, translation, interviews, minutes | Extracts mono audio from video; overlaps segment boundaries; absolute timestamps; refuses to disguise video bytes as audio |
| `OCR_HTR_Colab.ipynb` | Printed OCR and handwritten-text recognition | Separate diplomatic and normalized modes; high image resolution and medium PDF resolution; bounded page concurrency |
| `Summary_Colab.ipynb` | Summaries and 5–10 validated keywords from text or `.xlsx` | Preserves worksheets/formulas/styles; atomic resumable checkpoints; synchronous and 50%-cost asynchronous Batch paths |

Every completed result is accompanied by a `.provenance.json` sidecar containing
the source SHA-256, fixed requested model, concrete model version reported by the
response, exact prompt and prompt hash, helper hash, SDK/Python versions, settings,
finish reasons, and token counts. Source content is not copied into provenance.

## Fixed model releases

The repository never uses a `-latest` alias. A reviewed repository update is
required to change a model:

| Choice | Model ID | Standard input/output price per 1M tokens* |
| --- | --- | --- |
| Pro | `gemini-3.1-pro-preview` | $2 / $12 up to 200k input tokens; $4 / $18 above 200k |
| Flash | `gemini-3.6-flash` | $1.50 / $7.50 |
| Flash Lite | `gemini-3.5-flash-lite` | $0.30 / $2.50 |

\*Prices recorded 31 July 2026; verify the current
[Gemini pricing page](https://ai.google.dev/gemini-api/docs/pricing) before a
large run. Batch generation is priced at 50% of standard rates and targets
completion within 24 hours ([Batch API](https://ai.google.dev/gemini-api/docs/batch-api)).
Pro 3.1 is a preview model, so its lifecycle risk is higher than a stable release.

Thinking configuration is deliberately omitted so each fixed model uses Google's
tuned default. Reduced safety filters are off by default and can be enabled only
through an explicit transcription/OCR checkbox; that decision is recorded in
provenance. See Google's current
[thinking guidance](https://ai.google.dev/gemini-api/docs/generate-content/thinking)
and [model documentation](https://ai.google.dev/gemini-api/docs/models).

## Quick start

1. Open the required notebook in Google Colab.
2. Run Step 1. It installs exact tested package versions and downloads
   `zmo_common.py` from the immutable commit recorded in the notebook.
3. Step 1 verifies the helper SHA-256 before importing any downloaded code.
4. Add `GEMINI_API_KEY` through Colab Secrets and enable notebook access.
5. Connect Drive for resumable work, choose source files, inspect settings, and
   test a small representative sample.
6. Download the current run's ZIP even when Drive is connected.

Mounting Drive lets notebook code access files exposed by that mount. Review the
notebook and its pinned helper before authorization; see the
[Colab FAQ](https://research.google.com/colaboratory/faq.html).

## Reproducibility and durability

- Direct notebook dependencies are exact versions verified from PyPI.
- The helper is loaded from an immutable Git commit and checked against a SHA-256.
- Model IDs are fixed and no silent fallback is permitted.
- Local files are written atomically or flushed after each incremental append.
- Drive copies use same-directory temporary files, retries, and final verification.
- A transient Drive failure does not permanently disable later synchronization.
- Output names include the source hash and configuration identity, avoiding
  collisions between different files with the same stem.
- Download buttons package only files registered by the current run.

Summary workbook checkpoints bind the source hash, model, prompt hash,
worksheet, column, and header row. A new runtime can restore a matching Drive
checkpoint. Invalid, truncated, and failed rows have explicit `AI Status` values
and are not treated as complete.

## Methodological choices

OCR/HTR offers two representations that must not be conflated:

- **Diplomatic:** preserves line breaks, punctuation, spelling, and end-of-line
  hyphenation.
- **Normalized reading text:** joins visually wrapped lines and removes only
  clear line-break hyphens while preserving wording and spelling.

Audio segmentation uses a configurable short overlap plus previous-transcript
context. The overlap reduces boundary omissions, but speakers and uncertain
readings still require human checking.

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

CI additionally constrains the complete tested dependency graph with
`requirements-dev.lock`; direct notebook packages remain explicitly pinned in
their setup cells.

CI repeats lint, helper tests, notebook JSON/Python validation, helper-call
contract validation, pin/hash checks, workbook round-trips, MIME regressions,
Drive retry behavior, and evaluation-metric tests. GitHub Actions are pinned to
immutable commit SHAs.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the release sequence and
[`docs/architecture.md`](docs/architecture.md) for API/design decisions.

## Limitations

- Gemini output can omit, normalize, or hallucinate content.
- A `.provenance.json` file documents a run; it does not prove output accuracy.
- `openpyxl` preserves ordinary `.xlsx` workbook structures but may not retain
  every vendor-specific Excel extension. Test irreplaceable workbooks on copies.
- Formula source values rely on cached results; recalculate and save the workbook
  in Excel or LibreOffice before upload if caches are empty.
- Batch results must be collected promptly; remote results are retained for a
  limited period.
- No live Gemini call runs in CI because credentials and research data must not
  enter the test environment.

## License

[MIT](LICENSE). Created by [Frédérick Madore](https://www.frederickmadore.com/)
for the [Leibniz-Zentrum Moderner Orient (ZMO)](https://www.zmo.de/).
