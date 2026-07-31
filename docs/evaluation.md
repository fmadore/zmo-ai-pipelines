# Evaluation protocol

Do not describe a pipeline as “research-grade,” “precise,” or “accurate” without
measuring it on representative material from the intended corpus.

## Build a local gold set

Select material across the difficult dimensions that occur in the collection:

- print versus handwriting;
- scripts and languages;
- faded, skewed, marginal, or multi-column pages;
- speaker counts, accents, noise, crosstalk, and code-switching;
- short, typical, and unusually long source text.

Create manually checked UTF-8 reference transcriptions. Keep sensitive fixtures
in an approved local or institutional store; do not commit them merely to make CI
convenient. Record selection criteria and fixture hashes.

## OCR/HTR and audio metrics

Run the pipeline with fixed model, prompt, and settings, then compare each output:

```powershell
.venv/Scripts/python.exe scripts/evaluate_text.py reference.txt hypothesis.txt
```

The default comparison is exact and therefore appropriate for diplomatic output.
For a separately defined normalized evaluation:

```powershell
.venv/Scripts/python.exe scripts/evaluate_text.py reference.txt hypothesis.txt `
  --casefold --collapse-whitespace --json
```

Report character error rate (CER) and word error rate (WER) by document category,
not only as a pooled average. Review substitutions and omissions qualitatively.
For audio, separately inspect segment boundaries and speaker-label continuity.

Benchmark at least:

- Flash against Pro on difficult fixtures;
- PDF medium resolution against high on a sample before paying the token cost;
- audio overlap values (for example 0, 2, and 5 seconds);
- diplomatic and normalized OCR against their own matching references.

## Summary evaluation

CER/WER are not meaningful for summaries. Use a blinded rubric with at least:

- source faithfulness and unsupported claims;
- coverage of central claims/evidence;
- omission of material instructions embedded in the source;
- language and terminology preservation;
- keyword specificity, distinctness, and count;
- consistency across repeated runs of the same fixed release.

Sample both synchronous and Batch outputs because the execution path must not
change semantics. Include adversarial source passages that contain commands or
prompt-like text.

## Record the decision

Store aggregate results, fixture hashes, date, model ID/concrete response version,
prompt hash, helper hash, settings, and acceptance thresholds. Re-run the benchmark
before changing a model, prompt, media resolution, segmentation, dependency, or API.

