# Contributing and releases

## Local checks

Install the exact development environment and run both checks before every commit:

```powershell
.venv/Scripts/python.exe -m pip install --constraint requirements-dev.lock --editable ".[dev]"
.venv/Scripts/ruff.exe check .
.venv/Scripts/python.exe -m pytest
```

Do not add API keys, research fixtures, generated transcripts, workbook outputs,
or `.provenance.json` files containing information about real sources.

## Dependency updates

Training data and cached examples are not version sources. Verify every proposed
pin against the upstream registry, update `pyproject.toml` and the relevant `%pip`
cell together, resolve `requirements-dev.lock` from a clean Python 3.12 environment,
rebuild using that constraint, and run the full suite. Record behavioral changes
in `CHANGELOG.md`.

## Helper/notebook release sequence

Notebook helper integrity is intentionally a two-commit release operation:

1. Modify and test `zmo_common.py`.
2. Commit the helper so it has an immutable Git object.
3. Calculate that committed file's SHA-256.
4. Update `HELPER_COMMIT` and `HELPER_SHA256` in all three notebooks.
5. Run the full suite. `test_notebook_verifies_current_helper_bytes` must pass.
6. Commit the notebook pins.

Never point a notebook at `main`, a branch, or a mutable release asset. Never
change the helper after calculating the digest without repeating the sequence.

## Model updates

Check the official model documentation and lifecycle notices. Add only a concrete
model ID, never a `-latest` alias. Re-run the local gold-set evaluation described
in `docs/evaluation.md`, update pricing/lifecycle documentation, and retain the
prior model in release history.

## Notebook hygiene

- Clear every output before committing.
- Keep cell IDs unique.
- Ensure all `zc.*` keyword calls match the helper signature.
- Test a temporary workbook round-trip when touching Summary.
- Test video-without-ffmpeg and audio-boundary behavior when touching Audio.
- Keep diplomatic and normalized OCR prompts methodologically distinct.
