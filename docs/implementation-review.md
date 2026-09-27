# Repository improvement implementation, 27 September 2026

This change implements the review against baseline commit
`f2ed4c8b1f4373c733776b5b88d745fe5e95f227`.

| Review area | Implementation | Verification |
| --- | --- | --- |
| Same-name input collisions | Identity directories and verified staged copies | Distinct paths, different bytes, identical bytes |
| Generated Excel formulas | Strict string schema, literal cell type, Excel length/control validation | Formula-leading summaries/keywords round-trip as text |
| Stale source AI statuses | Run-owned unit records; explicit new/replace/error column policy | Fresh workbook statuses never skip source rows |
| Missing formula caches | Preflight row list and needs-recalculation status | Missing cache produces no generation request |
| Batch restart and mode switching | Durable intent/job handles, active-job guards, reconciliation and explicit resolution | Duplicate submit blocked, ambiguous create reconciled, terminal failure retry |
| Download and runtime recovery | Content-verified portable ZIPs, explicit import, manifest discovery | Corruption/traversal rejected, histories/provenance round-trip |
| Premature remote cleanup | Publish exports/provenance first; verified mirror or explicit saved-export confirmation | Failed sync/export never deletes remote results |
| OCR truncation and provenance | Separate per-page complete/truncated/failed state and response metadata | Retry only incomplete pages; preserve exact whitespace |
| Polling-time upload leaks | Cleanup holds the known upload handle through polling | Failure deletes the known remote file |
| Workbook efficiency | Linear read-only row traversal; periodic workbook exports | Workbook preservation and multi-row resume integration |
| Audio efficiency | ffmpeg generator reads source intervals; completed segments bypass conversion | Real synthetic-audio duration/offset check and skip regression |
| Checkpoint efficiency | Immutable unit records, cached source identity, streamed workbook artifact registration | Verified copies and previous-generation restore |
| Long summaries | Bounded recursive map/reduce, conservative token checks, retained chunk results | Interrupted aggregation reuses completed map requests |
| Batch capacity | Stream JSONL and split row/byte-limited jobs | Multiple jobs with stable keys and separate instructions |
| Maintainability | Shared pipeline/state/export modules, typed config/results, CLI, generated notebook UI | Same modules tested directly and all UI cells executed offline |
| Release consistency | One dependency lock for CI/notebooks; exact pins; Python 3.12 declaration; matching citation/version | Dependency consistency, generated freshness, all module hashes |
| Prompt preservation | Existing researcher-edited prompt files retained during setup | Explicit create-only template initialization |
| Research exports | Stable-ID JSONL, per-unit metadata, SRT/WebVTT | Subtitle times, segment speakers, escaping and provenance |
| Human review | Flagged units plus seeded sample; source previews; separate correction history | Reviewed/raw revisions preserved across retries and ZIP recovery |
| Scope and cost planning | Request estimates, optional supplied price rates, formula and PDF-layer preflight | Offline preflight and explicit method selection |
| Evaluation | Fast offline CER/WER with explicit normalization and A/B corpus strata | Reference denominators, Unicode normalization, weighted aggregation |

Validation: 76 automated tests passed on Python 3.12; Ruff, notebook-generation checks,
dependency consistency, and package/CLI checks passed. Tests include real ffmpeg on
synthetic audio and mock SDK/provider operations. No paid API calls or research uploads
were made. Live Colab Secrets, mounted Drive behavior, provider account availability,
and actual recognition quality require an approved small representative trial.

Operational limits are explicit: one writer per run; provider requests cannot promise
exactly-once billing across a hard process kill; only mirrored/exported progress survives
loss of a Colab runtime; cost estimates are not billing caps. Legacy checkpoints remain
with their original release and are never silently reinterpreted. Active matching legacy
Batch checkpoints block accidental resubmission. See `runs.md` for recovery procedures.
