"""Embed the tested audio adapter in Colab without a mutable remote download."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = "# BUNDLED TRANSCRIBE ADAPTER (generated; do not edit below)\n"


def main():
    path = ROOT / "Audio_Transcription_Colab.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    setup = "".join(notebook["cells"][2]["source"]).split(MARKER)[0].rstrip() + "\n\n"
    source = (ROOT / "zmo_transcribe.py").read_text(encoding="utf-8")
    setup += (MARKER + "import types as module_types\n"
              + "zt = module_types.ModuleType('zmo_transcribe')\n"
              + f"TRANSCRIBE_SOURCE = {source!r}\n"
              + "exec(compile(TRANSCRIBE_SOURCE, 'zmo_transcribe.py', 'exec'), zt.__dict__)\n")
    notebook["cells"][2]["source"] = setup.splitlines(keepends=True)
    path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
