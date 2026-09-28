# Contributing and releases

## Local checks

Use Python 3.12 and install ffmpeg/ffprobe for media integration tests.

```sh
python -m pip install -c requirements-dev.lock -e '.[dev]'
python scripts/build_notebooks.py
ruff check .
pytest
python -m pip check
```

Never commit API keys, actual research fixtures, generated transcripts, or provenance
from real source material. Automated tests use synthetic input and mocked provider APIs.
A passing test suite does not establish transcription accuracy or provider availability.

## Source layout

Edit pipeline behavior in `zmo_summary.py`, `zmo_ocr.py`, or `zmo_audio.py`.
Shared state, media, exports, CLI, evaluation, and notebook widgets have separate modules.
Edit notebook narrative/settings in `notebooks/*.template.json`, setup in `*_setup.py.in`,
and configuration wiring in `*_run.py.in`. Processing and download cells are generated;
changes to generated root notebooks will be overwritten. `scripts/bundle_transcribe.py`
is a compatibility alias for the complete builder.

## Dependency updates

Verify new versions against the upstream registry. Update `pyproject.toml`, then:

```sh
uv pip compile pyproject.toml --extra dev --python-version 3.12 -o requirements-dev.lock
python -m pip install -c requirements-dev.lock -e '.[dev]'
python scripts/build_notebooks.py
ruff check .
pytest
python -m pip check
```

The generator embeds the same constraints and direct requirements in each notebook.
Review transitive changes and update `CHANGELOG.md`. The lock targets Linux/Python 3.12;
other runtimes are not claimed as tested. Setuptools is separately pinned by build-system.

## Immutable module releases

All downloaded Python modules require a two-commit release:

1. Edit modules, templates, docs, and tests. Regenerate notebooks and run all checks.
2. Commit the implementation modules so their exact bytes have a real Git commit.
3. Run `python scripts/build_notebooks.py --commit FULL_IMPLEMENTATION_COMMIT`.
4. Run lint, tests, `python scripts/build_notebooks.py --check`, and verify the
   pinned commit contains every module with the digest recorded in notebook setup.
5. Commit the generated notebook pins and `notebooks/release.json`.
6. Push both commits together. The branch head must contain the complete release.

Never use a mutable branch or fabricate a commit. Any subsequent module edit requires
another implementation commit and regenerated pins. The downloaded modules are all
verified before import, including the audio adapter; no executable source is bundled.

## Validation and model updates

Use concrete model IDs and official lifecycle/API documentation. No silent fallback.
Keep tests for workbook formulas/styles, partial statuses, source/config guards, upload
cleanup, interrupted runs, Batch reconciliation, verified mirrors, and recovery archives.
Every notebook UI cell executes offline in CI. Preserve diplomatic and normalized prompts
as separate methodological choices. Before changing a model, prompt, or media policy,
evaluate an approved representative corpus as described in `docs/evaluation.md`.
