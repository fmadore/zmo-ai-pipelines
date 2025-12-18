# Copilot Instructions for ZMO AI Pipelines

## Project Context

Google Colab notebooks for **non-technical researchers** (social scientists, historians, archivists). Users should only need to click "Play" ▶️ to run workflows. All code remains visible for those who want to inspect or adapt it.

**Tools:** Audio transcription, OCR, HTR, text summarization – all powered by Gemini AI.

---

## Golden Rules

1. **Simplicity first** – Hide complexity, expose only essential options
2. **Use latest Gemini API** – Always verify patterns with Context7 MCP before writing API code
3. **Friendly feedback** – Emoji, colors, clear messages at every step
4. **Graceful errors** – Catch everything, explain in plain language with solutions
5. **Research-grade output** – Must meet academic/archival standards

---

## Gemini API (Critical)

```python
# ✅ CORRECT - Modern SDK
from google import genai
from google.genai import types

client = genai.Client(api_key=api_key)
response = client.models.generate_content(
    model="gemini-3-pro-preview",
    contents=[prompt, media_part],
    config=types.GenerateContentConfig(temperature=0.1)
)
```

```python
# ❌ WRONG - Deprecated
import google.generativeai as genai
model = genai.GenerativeModel('gemini-pro')
```

**Models (preference order):** `gemini-3-pro-preview` → `gemini-3-flash-preview`

**Thinking levels:**
- **Pro:** `low`, `high`
- **Flash:** `MINIMAL`, `low`, `medium`, `high`

---

## Colab Notebook Structure

Every notebook follows this pattern:
1. **Setup** – Install deps quietly (`-q`), create folders, print friendly confirmation
2. **API Key** – Password widget + auto-load from Colab Secrets
3. **Upload Files** – Button with clear status feedback
4. **Settings** – Simple dropdowns, hide advanced options
5. **Process** – Big green button, show progress per file
6. **Download** – Easy one-click download
7. **Help section** – Troubleshooting at the bottom

---

## UI Patterns

- Use `ipywidgets` for all interactions
- Emoji for status: ✅ success, ❌ error, ⏳ processing, 📁 files
- Color-coded HTML: green=success, red=error, orange=warning, blue=progress
- Always show progress: `"⏳ Processing file 2/5: interview.mp3"`

---

## Code Style

- `pathlib.Path` for files
- f-strings for formatting  
- Descriptive variable names (code = documentation)
- Store prompts as editable `.md` files in `prompts/` folder
- Constants in `SCREAMING_SNAKE_CASE`
