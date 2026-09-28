from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import nbformat
import pytest

ROOT = Path(__file__).parents[1]
NOTEBOOKS = sorted(ROOT.glob("*_Colab.ipynb"))


def code(path, cell):
    notebook = json.loads(path.read_text())
    return "".join(notebook["cells"][cell]["source"])


@pytest.mark.parametrize("path", NOTEBOOKS)
def test_valid_clean_notebook_and_all_executable_module_hashes(path):
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    assert len({c.id for c in notebook.cells}) == len(notebook.cells)
    for i, cell in enumerate(notebook.cells):
        if cell.cell_type == "code":
            assert not cell.outputs and cell.execution_count is None
            ast.parse(
                "\n".join(
                    line
                    for line in cell.source.splitlines()
                    if not line.lstrip().startswith(("%", "!"))
                ),
                filename=f"{path.name}:cell-{i}",
            )
    assignments = {}
    for node in ast.parse(
        "\n".join(line for line in code(path, 2).splitlines() if not line.startswith("%"))
    ).body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            try:
                assignments[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                pass
    assert re.fullmatch("[a-f0-9]{40}", assignments["HELPER_COMMIT"])
    assert assignments["MODULE_SHA256"] == {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob("zmo_*.py")
    }
    assert "hashlib.sha256(data).hexdigest() != expected" in code(path, 2)


def test_generated_notebooks_and_exact_dependency_pins():
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_notebooks.py"), "--check"], check=True
    )
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    direct = project["project"]["dependencies"] + project["project"]["optional-dependencies"]["dev"]
    locked = (ROOT / "requirements-dev.lock").read_text().casefold()
    for requirement in direct:
        assert requirement.casefold() in locked
    for path in NOTEBOOKS:
        setup = code(path, 2)
        for requirement in project["project"]["dependencies"]:
            assert requirement in setup
    assert "pexpect==4.9.0" in locked and "ptyprocess==0.7.0" in locked


@pytest.mark.parametrize("path", NOTEBOOKS)
def test_all_notebook_ui_cells_execute_offline(path, tmp_path):
    # Exercise real widgets and verified imports in an isolated interpreter.
    script = """
import io, json, urllib.request
from pathlib import Path
root, path = Path(__import__('sys').argv[1]), Path(__import__('sys').argv[2])
urllib.request.urlopen = lambda url, **kw: io.BytesIO((root / url.rsplit('/', 1)[1]).read_bytes())
namespace = {}
for cell in json.loads(path.read_text())['cells']:
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        source = '\\n'.join(line for line in source.splitlines() if not line.startswith(('%', '!')))
        exec(compile(source, str(path), 'exec'), namespace)
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(ROOT), str(path)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert result.returncode == 0, result.stderr


def test_diplomatic_and_normalized_prompts_remain_distinct():
    setup = code(ROOT / "OCR_HTR_Colab.ipynb", 2)
    assert "Preserve end-of-line hyphens exactly" in setup
    assert "Remove a line-break hyphen only" in setup
    assert "absolute precision" not in setup.lower()
