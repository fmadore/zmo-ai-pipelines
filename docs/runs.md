# Running and recovering work

## Configuration examples

Save one of these JSON objects as the CLI `--config` file. Notebook controls create the
same configuration. Prompts, model, and content-affecting options are frozen at run start.

Summary:

```json
{"model":"gemini-3.7-flash","worksheet":"Data","column":"Text","header_row":1,"column_policy":"new"}
```

Use `new` to preserve existing AI columns, `replace` for explicit replacement, or `error`
to stop on a collision. Formula source values must have a cached result. Recalculate/save
the original file before starting a new run when preflight lists missing caches.
For text files, omit worksheet/column. Optional `template` uses a `{text}` placeholder;
`system` contains researcher instructions. Long text is bounded by `max_chunk_chars`
(default 200,000) and `max_output_tokens` (default 4,096).

OCR/HTR:

```json
{"model":"gemini-3.7-flash","instructions":"Transcribe diplomatically; mark uncertainty.","first_page":1,"last_page":3,"method":"ocr"}
```

Use `0` for an unbounded page endpoint. `method: "text-layer"` extracts an existing PDF
layer locally; inspect preflight samples first. Empty extracted pages are `needs-ocr`.
Changing method creates a separate run. Explicit `reduced_safety` defaults to false.

Audio:

```json
{"mode":"verbatim","languages":["fr-FR"],"speakers":true,"timestamps":true}
```

Use an empty languages list for automatic detection. `vocabulary` is a list of terms;
it cannot accompany speakers/timestamps. Smart mode cannot use either annotation option.

## CLI workflow

```sh
export GEMINI_API_KEY='YOUR_KEY'
zmo-pipelines preflight ocr source.pdf --config ocr.json
zmo-pipelines run ocr source.pdf --config ocr.json --output results --mirror /path/to/mirror
zmo-pipelines status results/RUN_ID
zmo-pipelines resume results/RUN_ID --source source.pdf
zmo-pipelines export results/RUN_ID recovery.zip
zmo-pipelines import recovery.zip --output restored
```

The CLI prints the exact run directory. Use the same original source bytes for resume;
changed bytes are rejected. `run` with matching source/config resumes automatically.
`--new-run` preserves the existing run and intentionally creates separate processing.
Use one active notebook or CLI writer per run.

Without Drive, download a recovery ZIP before the runtime ends. Import it into an empty
output root after reset, then select the original source and matching settings. Drive
restores missing matching run directories automatically. A corrupted current manifest can
fall back to the previous verified generation. Import never overwrites an existing run.
The source itself is not in a recovery ZIP and must be retained separately.

## Batch controls

```sh
zmo-pipelines run summary source.xlsx --config summary.json --batch --mirror /path/to/mirror
zmo-pipelines collect results/RUN_ID --source source.xlsx --mirror /path/to/mirror
zmo-pipelines cancel results/RUN_ID
zmo-pipelines reconcile results/RUN_ID
zmo-pipelines resolve results/RUN_ID SUBMISSION_ID --job-name batches/EXACT_JOB
```

Cancellation is a request: collect/poll until the provider reports a terminal state before
retrying. Do not resubmit while a job is pending or its submission outcome is uncertain.
Only after checking remote jobs can an operator use `resolve ... --confirm-no-remote-job`.
A mistaken abandonment can incur duplicate charges. The notebook recovery panel exposes
the same explicit attach/abandon control.

Jobs split at 500 rows or 20 MiB of input by default. Very long rows are marked
`needs-synchronous-long-text`; after all Batch work is collected/cancelled, resume the run
synchronously to process them. Failed, missing, invalid, and truncated results remain
eligible for retry. New source AI Status cells are never trusted as resume state.

Remote files remain pending cleanup unless the mirror is verified. After saving and
checking a recovery ZIP, `zmo-pipelines cleanup results/RUN_ID --confirm-exported` permits
cleanup without a mirror. Provider retention still applies: collect promptly.

## Older releases

Schema-2 recovery ZIPs do not reinterpret older checkpoint files. Finish active legacy
Batch jobs with the original notebook release and preserve that release's outputs. A
matching active `*.checkpoint.json` in the local or mirror root blocks a new summary run
to prevent silently duplicating a paid legacy job. Keep the checkpoint beside its output.
New runs never overwrite legacy artifacts. Previously completed audio/OCR exports without
per-unit manifests cannot be safely resumed as schema-2 runs.

## Review and exports

`records.jsonl` stores the stable content-based source ID, run ID, unit locator/status,
raw text, timings/keywords, response metadata, and optional reviewed correction.
`provenance.json` records configuration and software fingerprints. The run manifest links
immutable unit and review histories. A correction identifies the unit revision it reviewed;
JSONL flags whether it still matches the latest retry output.

Notebook review shows flagged units plus a seeded sample of unflagged complete units,
with PDF/image previews, spreadsheet source text, or a 30-second recording sample.
Use the CLI to review any exact unit:

```sh
zmo-pipelines review results/RUN_ID
zmo-pipelines review results/RUN_ID --unit page-3 --text-file corrected.txt --reviewer researcher
```

Corrections do not overwrite the raw transcript or silently alter summary/Excel/subtitle
exports. Use the separate `review.corrected_text` field downstream. These are editorial
records, not model-confidence estimates. CER/WER evaluation is described in `evaluation.md`.
