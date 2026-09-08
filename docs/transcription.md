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

- `…transcription.txt`: original response text, joined in recording order.
- `…transcription.annotated.txt`: readable voice/time annotations when returned.
- `…transcription.words.json`: segment status and word annotations; numeric times
  refer to the original recording, and speaker IDs include the segment number.
- `…transcription.provenance.json`: source hash, options, adapter hash, available
  response metadata, and completion status. Vocabulary hints can contain names;
  protect this file as research data.

Original audio is preserved for a single request. Longer recordings are split
without overlap and re-encoded; video is reduced to its soundtrack. Check joins
manually. Voice identity is not inferred across requests. The notebook enforces
Google's documented duration limits and clearly scopes voice labels to segments.

## Recovery

A completed segment is saved before the next request. Drive receives copies if
connected. Download the ZIP even if Drive reports success. After a runtime reset,
existing Drive copies remain available, but this version does not resume audio
segments automatically. A new run transcribes again and may incur new charges.

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
