# Audio transcription

Open the Audio Colab, run each step in order, and try one short recording before
processing a collection. Read the `.txt` result while listening to the recording.

The notebook uses **Gemini 3.5 Transcribe**, with no prompt editor. Choose
Verbatim for research transcription or Smart for an edited reading copy. Optional
voice labels and word times require Verbatim. Vocabulary hints cannot accompany
either annotation option. Language defaults to automatic detection; a selected
language is a hint, not translation. Google documents these combinations in the
[Transcribe guide](https://ai.google.dev/gemini-api/docs/transcribe).

## Outputs

Each run has its own folder. Download its ZIP in Step 6, including incomplete
results if any segment failed:

- `transcription.txt`: original response text joined in recording order.
- `transcription.annotated.txt`: readable voice/time annotations when returned.
- `transcription.srt` and `transcription.vtt`: subtitles when word times are returned.
- `records.jsonl`: raw text, segment status, word annotations, and optional reviewed
  corrections. Numeric times refer to the source; speaker IDs include the segment.
- `provenance.json`: source hash, options, software hashes, available response metadata,
  and completion status. Vocabulary hints may contain names; protect this as research data.
- `manifest.json` and immutable object folders: verified resume state and review history.

Original audio is preserved for a single request. Longer recordings are split
without overlap and re-encoded; video is reduced to its soundtrack. Check joins
manually. Voice identity is not inferred across requests. The notebook enforces
Google's documented duration limits and clearly scopes voice labels to segments.

## Recovery

A completed segment is saved before the next request. Drive receives verified copies
if connected. Download the recovery ZIP even if Drive reports success. After a runtime
reset, reconnect Drive or import the ZIP, select the same original source/settings, and
resume. Completed segments are reused without uploading or converting them again.
A changed source, model, or configuration creates a separate run. The explicit separate-run
option also starts fresh and may incur new charges. Only mirrored/exported progress
survives loss of the local runtime. See [run recovery](runs.md).

The Interactions request uses `store=False`; file deletion is attempted after each
request, including failed ones. Google describes this storage control in the
[Interactions overview](https://ai.google.dev/gemini-api/docs/interactions-overview).
The institutional privacy notice still applies.

## Validation before publication

Use consented representative recordings: clear speech, mixed languages, several
voices, silence, noisy audio, and speech crossing a segment boundary. Compare
Verbatim with and without annotations; evaluate Smart against an edited reference.
Run the same file twice and check that the first output remains intact. Interrupt
a multi-segment run and verify the locally saved and Drive copies. Automated tests
validate contracts and failure handling, not real recognition quality.
