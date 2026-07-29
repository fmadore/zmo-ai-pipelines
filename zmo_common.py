"""Shared helpers for the ZMO AI Pipelines Colab notebooks.

This module is downloaded by each notebook at runtime:

    !wget -q -O zmo_common.py https://raw.githubusercontent.com/fmadore/zmo-ai-pipelines/main/zmo_common.py

Keeping the plumbing here means a fix lands in all three notebooks at once,
instead of being copy-pasted three times and drifting apart.

Notes for maintainers
---------------------
* We deliberately do NOT set ``temperature``, ``top_p`` or ``top_k``. Google
  deprecated those sampling parameters on 21 July 2026, and the Gemini 3
  guide warns that lowering temperature "may lead to unexpected behavior,
  such as looping or degraded performance". Looping is the worst possible
  failure mode for a long transcription.
* Model IDs are discovered at runtime rather than hardcoded, because the
  ``-latest`` aliases get hot-swapped without notice (``gemini-pro-latest``
  pointed at ``gemini-3-pro-preview``, which was shut down on 9 March 2026).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

__version__ = "2026.07.29"


# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

#: HTTP statuses the SDK should retry automatically. 408 is a request timeout,
#: which is as transient as a 503 and worth retrying too.
RETRY_STATUS_CODES = [408, 429, 500, 502, 503, 504]

#: The API caps a whole request at 20 MB. Anything above this threshold goes
#: through the Files API instead of being inlined, leaving room for the prompt.
INLINE_LIMIT_BYTES = 15 * 1024 * 1024

#: Gemini 3 models top out at 64k output tokens.
MAX_OUTPUT_TOKENS = 65536

#: The only two models the notebooks offer. The ``-latest`` aliases are
#: hot-swapped by Google as new releases land, so these keep pointing at the
#: current Pro and Flash models without anyone editing this file.
MODEL_PRO = "gemini-pro-latest"
MODEL_FLASH = "gemini-flash-latest"

MODEL_CHOICES = [
    ("Best quality — slower, costs more  (gemini-pro-latest)", MODEL_PRO),
    ("Faster and cheaper  (gemini-flash-latest)", MODEL_FLASH),
]

#: Archival material routinely contains violent, racist or sexual content that
#: the default filters would refuse to transcribe. Turning the filters off is
#: the whole point of a faithful archival transcription.
SAFETY_SETTINGS = [
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
]


# --------------------------------------------------------------------------
# Client
# --------------------------------------------------------------------------

def build_http_options() -> types.HttpOptions:
    """Retry policy: 5 attempts with exponential backoff on 429/5xx."""
    return types.HttpOptions(
        retry_options=types.HttpRetryOptions(
            attempts=5,
            initial_delay=2.0,
            exp_base=2.0,
            max_delay=60.0,
            jitter=0.2,
            http_status_codes=RETRY_STATUS_CODES,
        )
    )


def make_client(api_key: str) -> genai.Client:
    """Create a Gemini client with the shared retry policy applied."""
    return genai.Client(api_key=api_key, http_options=build_http_options())


# --------------------------------------------------------------------------
# API key
# --------------------------------------------------------------------------

SECRET_NAME = "GEMINI_API_KEY"


def read_secret(name: str = SECRET_NAME):
    """Read a key from Colab Secrets.

    Returns ``(value, status)`` where status is ``'ok'``, ``'missing'``,
    ``'no_access'`` or ``'not_colab'``. The distinction matters: "you haven't
    created the secret" and "you created it but didn't switch notebook access
    on" need different instructions.
    """
    try:
        from google.colab import userdata
    except Exception:
        return (None, "not_colab")

    try:
        value = userdata.get(name)
    except Exception as exc:
        kind = type(exc).__name__
        if "NotebookAccess" in kind:
            return (None, "no_access")
        return (None, "missing")

    return (value, "ok") if value else (None, "missing")


def mask_key(key: str) -> str:
    """Show just enough of a key to confirm which one is loaded."""
    if not key:
        return ""
    return f"{key[:6]}…{key[-4:]}" if len(key) > 12 else "…"


class ApiKeyPanel:
    """Step 2 UI. Colab Secrets is the primary path; typing is the fallback.

    Pasting a key into a widget is genuinely risky here: ipywidgets syncs a
    ``Password`` widget's plaintext value to the frontend, and Colab writes
    widget state into the saved ``.ipynb``. A user who types a key and then
    saves a copy to Drive or GitHub has published it. Colab Secrets never
    touches the notebook file.
    """

    def __init__(self, secret_name: str = SECRET_NAME):
        import ipywidgets as widgets

        self.secret_name = secret_name
        self._secret_value = None
        self.status = widgets.HTML()
        self.manual_input = widgets.Password(
            placeholder="Only if you cannot use Secrets",
            description="API key:",
            layout=widgets.Layout(width="480px"),
            style={"description_width": "80px"},
        )
        self.manual_note = widgets.HTML()
        self.manual_input.observe(self._on_manual, names="value")

        self.recheck_button = widgets.Button(
            description="🔄 Check Secrets again",
            layout=widgets.Layout(width="200px"),
        )
        self.recheck_button.on_click(lambda _b: self.refresh())

        self.fallback = widgets.Accordion(
            children=[widgets.VBox([
                widgets.HTML(
                    "<p>Colab can save widget contents into the notebook file. "
                    "If you paste your key here and then save a copy to Drive or "
                    "GitHub, <b>your key travels with the file</b>. Use Secrets "
                    "instead whenever you can, and delete the key from this box "
                    "before saving.</p>"
                ),
                self.manual_input,
                self.manual_note,
            ])],
        )
        self.fallback.set_title(0, "⚠️  I can't use Secrets — let me paste the key instead")
        self.fallback.selected_index = None

        self.refresh(announce=False)

    def _on_manual(self, change):
        value = change["new"]
        if len(value) > 20:
            self.manual_note.value = (
                "<span style='color:#b26a00;'>⚠️ Key entered manually — "
                "remember to clear this box before saving the notebook.</span>"
            )
        else:
            self.manual_note.value = (
                "<span style='color:#888;'>Paste the full key.</span>"
            )

    def refresh(self, announce: bool = True):
        """Re-read Colab Secrets and update the status line."""
        value, state = read_secret(self.secret_name)
        self._secret_value = value

        if state == "ok":
            self.status.value = (
                "<div style='background:#e8f5e9;padding:12px;border-radius:6px;'>"
                f"✅ <b>API key loaded from Colab Secrets</b> ({mask_key(value)})<br>"
                "Nothing is stored in this notebook. You're ready for the next step."
                "</div>"
            )
            self.fallback.selected_index = None
        elif state == "no_access":
            self.status.value = (
                "<div style='background:#fff3e0;padding:12px;border-radius:6px;'>"
                f"🔒 <b>Secret <code>{self.secret_name}</code> exists, but this notebook "
                "can't read it.</b><br>Open the 🔑 <b>Secrets</b> panel in the left sidebar "
                "and switch <b>Notebook access</b> ON, then click "
                "<i>Check Secrets again</i>.</div>"
            )
        else:
            self.status.value = (
                "<div style='background:#fff3e0;padding:12px;border-radius:6px;'>"
                f"🔑 <b>No <code>{self.secret_name}</code> secret found yet.</b>"
                "<ol style='margin:8px 0 0 18px;'>"
                "<li>Click the 🔑 <b>Secrets</b> icon in the left sidebar</li>"
                "<li>Click <b>+ Add new secret</b></li>"
                f"<li>Name it exactly <code>{self.secret_name}</code></li>"
                "<li>Paste your key from "
                "<a href='https://aistudio.google.com/apikey' target='_blank'>"
                "aistudio.google.com/apikey</a> into the Value box</li>"
                "<li>Switch <b>Notebook access</b> ON</li>"
                "<li>Click <i>Check Secrets again</i> below</li>"
                "</ol>You only ever do this once — the secret is remembered across "
                "all your notebooks.</div>"
            )

        if announce:
            self.fallback.selected_index = None

    def display(self):
        import ipywidgets as widgets
        from IPython.display import display as _display

        _display(self.status)
        _display(self.recheck_button)
        _display(widgets.HTML("<br>"))
        _display(self.fallback)

    def get(self):
        """Return the key to use, Secrets first."""
        if self._secret_value:
            return self._secret_value
        value, state = read_secret(self.secret_name)
        if state == "ok" and value:
            self._secret_value = value
            return value
        manual = (self.manual_input.value or "").strip()
        return manual or None


def key_help_message(secret_name: str = SECRET_NAME) -> str:
    """The message to print when a run is attempted with no key."""
    return (
        "❌ No API key found.\n"
        f"   Go back to Step 2 and add a Colab Secret named '{secret_name}'\n"
        "   (🔑 icon in the left sidebar), then click 'Check Secrets again'.\n"
        "   Get a key at https://aistudio.google.com/apikey"
    )


# --------------------------------------------------------------------------
# File selection
# --------------------------------------------------------------------------

class FileSelector:
    """Two-tab file picker: upload from the computer, or browse Google Drive.

    Shared because the audio and OCR notebooks need exactly the same thing.
    The Drive tab is deliberately rebuildable: users almost always mount Drive
    *after* first running this step, and would otherwise be stuck looking at a
    "not connected" message with no way forward except knowing to re-run the
    cell.
    """

    def __init__(self, dest_dir, extensions, drive=None, icon_for=None,
                 what="files", size_hint_mb=200):
        import ipywidgets as widgets

        self.dest_dir = Path(dest_dir)
        self.dest_dir.mkdir(parents=True, exist_ok=True)
        self.extensions = {e.lower() for e in extensions}
        self.drive = drive
        self.selected = []
        self._icon_for = icon_for or (lambda path: "📄")
        self._drive_picks = []

        self.upload_status = widgets.HTML()
        self.drive_status = widgets.HTML()
        self.drive_picks_html = widgets.HTML("<i>Nothing chosen yet</i>")

        upload_button = widgets.Button(
            description=f"📁 Upload {what} from my computer",
            button_style="primary",
            layout=widgets.Layout(width="320px", height="40px"),
        )
        upload_button.on_click(self._on_upload)

        self.local_tab = widgets.VBox([
            upload_button,
            self.upload_status,
            widgets.HTML(
                f"<br><i>Accepted: {', '.join(sorted(self.extensions))}</i><br>"
                f"<i>💡 Uploading through the browser gets slow and unreliable above "
                f"about {size_hint_mb} MB. For anything larger, put the file in "
                f"Google Drive and use the other tab.</i>"
            ),
        ])

        self.drive_tab = widgets.VBox([])
        self.tabs = widgets.Tab(children=[self.local_tab, self.drive_tab])
        self.tabs.set_title(0, "📤 From my computer")
        self.tabs.set_title(1, "☁️ From Google Drive")
        self.build_drive_tab()

    # -- local ------------------------------------------------------------
    def _on_upload(self, _button):
        from google.colab import files as colab_files

        self.upload_status.value = (
            "<span style='color:#1565c0;'>📤 Upload dialog opened — pick your files…</span>"
        )
        try:
            uploaded = colab_files.upload()
        except Exception as exc:
            self.upload_status.value = f"<span style='color:#c62828;'>❌ {exc}</span>"
            return

        if not uploaded:
            self.upload_status.value = "<span style='color:#ef6c00;'>⚠️ Nothing uploaded.</span>"
            return

        accepted, rejected = [], []
        self.selected = []
        for filename, content in uploaded.items():
            if Path(filename).suffix.lower() in self.extensions:
                target = self.dest_dir / filename
                target.write_bytes(content)
                self.selected.append(target)
                accepted.append(target)
            else:
                rejected.append(filename)

        self.upload_status.value = self._summary(accepted, rejected)

    # -- drive ------------------------------------------------------------
    def build_drive_tab(self, _button=None):
        import ipywidgets as widgets

        refresh = widgets.Button(
            description="🔄 Refresh", layout=widgets.Layout(width="130px")
        )
        refresh.on_click(self.build_drive_tab)

        if self.drive is None or not self.drive.mounted:
            self.drive_tab.children = (
                widgets.HTML(
                    "<div style='padding:16px;background:#fff3e0;border-radius:8px;'>"
                    "<b>☁️ Google Drive is not connected yet.</b>"
                    "<ol style='margin:8px 0 0 18px;'>"
                    "<li>Go up to <b>Step 2.5</b> and click <b>Connect Google Drive</b></li>"
                    "<li>Authorise access when Google asks</li>"
                    "<li>Come back here and click <b>Refresh</b></li>"
                    "</ol></div>"
                ),
                refresh,
            )
            return

        try:
            from ipyfilechooser import FileChooser
        except ImportError:
            self.drive_tab.children = (
                widgets.HTML(
                    "<div style='padding:16px;background:#fff3e0;border-radius:8px;'>"
                    "The Drive file browser needs the <code>ipyfilechooser</code> package. "
                    "Re-run <b>Step 1</b>, then click Refresh.</div>"
                ),
                refresh,
            )
            return

        chooser = FileChooser(
            path=DriveHelper.BASE_PATH,
            title="<b>📂 Browse your Google Drive</b>",
            show_hidden=False,
            select_default=False,
            filter_pattern=[f"*{ext}" for ext in sorted(self.extensions)],
        )
        chooser.register_callback(self._on_drive_pick)

        confirm = widgets.Button(
            description="✅ Use these files", button_style="success",
            layout=widgets.Layout(width="180px"),
        )
        confirm.on_click(self._on_drive_confirm)

        clear = widgets.Button(
            description="🗑️ Clear list", button_style="warning",
            layout=widgets.Layout(width="150px"),
        )
        clear.on_click(self._on_drive_clear)

        self.drive_tab.children = (
            widgets.HTML(
                "<p><i>Open folders and click a file to add it to the list. "
                "Repeat for as many files as you need, then press "
                "<b>Use these files</b>.</i></p>"
            ),
            chooser,
            widgets.HTML("<hr style='margin:10px 0;'>"),
            self.drive_picks_html,
            widgets.HBox([confirm, clear, refresh]),
            self.drive_status,
        )

    def _on_drive_pick(self, chooser):
        if not chooser.selected:
            return
        path = Path(chooser.selected)
        if path.suffix.lower() not in self.extensions:
            self.drive_status.value = (
                f"<span style='color:#c62828;'>❌ {path.suffix} is not a supported format.</span>"
            )
            return
        if path in self._drive_picks:
            self.drive_status.value = "<span style='color:#ef6c00;'>⚠️ Already in the list.</span>"
            return
        self._drive_picks.append(path)
        self._render_picks()
        self.drive_status.value = f"<span style='color:#2e7d32;'>✅ Added {path.name}</span>"

    def _on_drive_clear(self, _button):
        self._drive_picks = []
        self._render_picks()
        self.drive_status.value = "<span style='color:#1565c0;'>List cleared.</span>"

    def _on_drive_confirm(self, _button):
        if not self._drive_picks:
            self.drive_status.value = (
                "<span style='color:#c62828;'>❌ Choose at least one file first.</span>"
            )
            return
        copied, failed = [], []
        for source in self._drive_picks:
            try:
                target = self.dest_dir / source.name
                shutil.copy2(source, target)
                copied.append(target)
            except Exception:
                failed.append(source.name)
        self.selected = copied
        self.drive_status.value = self._summary(copied, failed)

    def _render_picks(self):
        if not self._drive_picks:
            self.drive_picks_html.value = "<i>Nothing chosen yet</i>"
            return
        rows = "".join(
            f"&nbsp;&nbsp;{self._icon_for(p)} {p.name}<br>" for p in self._drive_picks
        )
        self.drive_picks_html.value = f"<b>{len(self._drive_picks)} file(s) chosen:</b><br>{rows}"

    # -- shared -----------------------------------------------------------
    def _summary(self, accepted, rejected):
        html = ""
        if accepted:
            rows = "".join(
                f"&nbsp;&nbsp;&nbsp;{self._icon_for(Path(p))} {Path(p).name}<br>"
                for p in accepted
            )
            html += (
                f"<span style='color:#2e7d32;'>✅ Ready to process "
                f"{len(accepted)} file(s):</span><br>{rows}"
            )
        if rejected:
            rows = "".join(f"&nbsp;&nbsp;&nbsp;⚠️ {Path(p).name}<br>" for p in rejected)
            html += (
                f"<span style='color:#c62828;'>❌ Skipped {len(rejected)} "
                f"unsupported file(s):</span><br>{rows}"
            )
        return html or "<span style='color:#ef6c00;'>⚠️ Nothing selected.</span>"

    def display(self):
        from IPython.display import display as _display
        _display(self.tabs)


# --------------------------------------------------------------------------
# Notices
# --------------------------------------------------------------------------

def privacy_notice(material: str = "your files") -> str:
    """HTML warning about free-tier data handling.

    This matters more than usual for this audience: research interviews often
    carry ethics-board conditions that forbid third-party human review.
    """
    return (
        "<div style='background:#fdecea;border-left:5px solid #c62828;"
        "padding:12px 14px;border-radius:4px;margin:8px 0;'>"
        "<b>⚠️ Before you upload sensitive research material</b><br><br>"
        f"On the <b>free</b> Gemini tier, Google uses {material} "
        "to improve its products, and its terms state that "
        "<i>“human reviewers may read, annotate, and process your API input and "
        "output.”</i><br><br>"
        "On the <b>paid</b> tier (billing enabled on your Google Cloud project) "
        "Google does not use your prompts or responses to improve its products.<br><br>"
        "If your material is covered by a research-ethics approval, a consent form, "
        "or a data-protection agreement, <b>enable billing before processing it</b> — "
        "or check that free-tier handling is compatible with your approval. "
        "<a href='https://ai.google.dev/gemini-api/terms' target='_blank'>Gemini API "
        "terms</a>."
        "</div>"
    )


def api_key_migration_notice() -> str:
    """Standard keys stop working in September 2026."""
    return (
        "<div style='background:#e3f2fd;padding:10px 12px;border-radius:4px;"
        "margin:8px 0;'>"
        "ℹ️ <b>Keys created before 2026 may stop working.</b> Google is moving to "
        "“auth keys”: unrestricted standard keys are already rejected, and "
        "<b>all</b> standard keys will be rejected from <b>September 2026</b>. "
        "Every key you create today at "
        "<a href='https://aistudio.google.com/apikey' target='_blank'>"
        "aistudio.google.com/apikey</a> is an auth key. If your key suddenly stops "
        "working, create a fresh one there."
        "</div>"
    )


# --------------------------------------------------------------------------
# Responses
# --------------------------------------------------------------------------

def friendly_api_error(exc) -> str:
    """Map an APIError to a plain-language hint."""
    hints = {
        400: "Invalid request (check the file format or prompt length).",
        401: "Unauthorized — is your API key correct and still valid?",
        403: "Access denied or quota issue — check billing and API access.",
        404: "Model not found — it may have been retired. Re-run the settings step "
             "to refresh the model list.",
        429: "Rate limit hit even after retries — wait a few minutes, or reduce "
             "the number of parallel requests.",
        500: "Google server error — retry shortly.",
        503: "Model temporarily unavailable — retry shortly.",
    }
    code = getattr(exc, "code", None)
    message = getattr(exc, "message", str(exc))
    return f"❌ Gemini API [{code}] — {hints.get(code, 'See message below.')}\n   {message}"


def extract_text(response):
    """Pull text out of a response. Returns ``(text, status)``, never raises.

    Status is one of ``'ok'``, ``'truncated'``, ``'empty'``, or a string
    starting with ``'blocked'``. ``'truncated'`` still carries the partial
    text — losing half a transcription silently is worse than keeping it with
    a warning attached.
    """
    if response is None:
        return (None, "empty")

    feedback = getattr(response, "prompt_feedback", None)
    if feedback is not None and getattr(feedback, "block_reason", None):
        return (None, f"blocked (prompt: {feedback.block_reason})")

    candidates = getattr(response, "candidates", None) or []
    if not candidates:
        return (None, "empty")

    candidate = candidates[0]
    finish = getattr(candidate, "finish_reason", None)
    finish_name = str(finish).split(".")[-1] if finish else None

    try:
        text = response.text
    except Exception:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) if content else None
        text = "".join(getattr(p, "text", "") or "" for p in parts) if parts else None

    if finish_name == "MAX_TOKENS":
        return (text, "truncated") if text else (None, "empty")

    if finish_name and finish_name not in ("STOP", "FINISH_REASON_UNSPECIFIED"):
        return (None, f"blocked ({finish_name})")

    return (text, "ok") if text else (None, "empty")


def status_is_usable(status: str) -> bool:
    """True when the response carries text we can keep."""
    return status in ("ok", "truncated")


def warn_if_truncated(status: str, label: str = "", indent: str = "   ") -> None:
    if status == "truncated":
        print(
            f"{indent}⚠️ {label} hit the output limit and was CUT SHORT. "
            "The text below is incomplete."
        )


def log_tokens(response, label: str = "", indent: str = "   ") -> None:
    """Print token usage so cost stays visible."""
    usage = getattr(response, "usage_metadata", None)
    if usage is None:
        return
    total = getattr(usage, "total_token_count", None)
    if total is not None:
        print(f"{indent}🔢 {label} tokens: {total:,}")


def collect_tokens(response, sink) -> None:
    """Append a response's token total to ``sink`` (used by parallel callers)."""
    if sink is None:
        return
    usage = getattr(response, "usage_metadata", None)
    total = getattr(usage, "total_token_count", None) if usage else None
    if total is not None:
        sink.append(total)


# --------------------------------------------------------------------------
# Generation config
# --------------------------------------------------------------------------

def default_thinking_level(model_id: str) -> str:
    """Pick a safe thinking level for a model.

    Pro models reject ``MINIMAL`` — they only accept LOW and above — so the
    floor has to depend on the model, not on a hardcoded guess.
    """
    return "LOW" if "pro" in (model_id or "").lower() else "MINIMAL"


def build_config(
    system_instruction=None,
    model_id: str = "",
    thinking_level: str = None,
    media_resolution=None,
    max_output_tokens: int = MAX_OUTPUT_TOKENS,
    response_mime_type: str = "text/plain",
    response_schema=None,
    safety: bool = True,
) -> types.GenerateContentConfig:
    """Build a GenerateContentConfig.

    Note the absence of ``temperature``, ``top_p`` and ``top_k``: they are
    deprecated, and Google explicitly recommends leaving temperature at its
    default on Gemini 3 models.

    Passing ``response_schema`` switches the reply to JSON matching that
    schema, which is far more dependable than asking for a particular text
    layout and then parsing it back out.
    """
    params = {
        "max_output_tokens": max_output_tokens,
        "response_mime_type": "application/json" if response_schema else response_mime_type,
        "thinking_config": types.ThinkingConfig(
            thinking_level=thinking_level or default_thinking_level(model_id)
        ),
    }
    if response_schema is not None:
        params["response_schema"] = response_schema
    if system_instruction:
        params["system_instruction"] = system_instruction
    if media_resolution is not None:
        params["media_resolution"] = media_resolution
    if safety:
        params["safety_settings"] = SAFETY_SETTINGS
    return types.GenerateContentConfig(**params)


# --------------------------------------------------------------------------
# Model discovery
# --------------------------------------------------------------------------

def resolve_model(client, model_id: str):
    """Check that an alias still resolves, and report what it points at.

    Returns ``(ok, message)``. Aliases are hot-swapped by Google, which is
    exactly why the notebooks use them — but it also means a run can fail with
    a bare 404 that a non-specialist has no way to interpret. One cheap lookup
    before a long job turns that into a sentence they can act on.
    """
    try:
        model = client.models.get(model=model_id)
    except genai_errors.APIError as exc:
        return (False, friendly_api_error(exc))
    except Exception as exc:
        # Never block a run just because the pre-flight check itself broke.
        return (True, f"(could not verify {model_id}: {exc})")

    version = getattr(model, "version", None) or ""
    display = getattr(model, "display_name", None) or ""
    detail = " → ".join(part for part in [display, version] if part)
    return (True, f"{model_id}{f' ({detail})' if detail else ''}")


# --------------------------------------------------------------------------
# Sending media
# --------------------------------------------------------------------------

def _wait_until_active(client, uploaded, poll_seconds: float = 2.0, timeout: float = 900.0):
    deadline = time.time() + timeout
    while str(getattr(uploaded, "state", "")).split(".")[-1] == "PROCESSING":
        if time.time() > deadline:
            raise RuntimeError("Timed out waiting for the upload to be processed.")
        time.sleep(poll_seconds)
        uploaded = client.files.get(name=uploaded.name)
    if str(getattr(uploaded, "state", "")).split(".")[-1] == "FAILED":
        raise RuntimeError(f"Gemini could not process the upload: {getattr(uploaded, 'error', '')}")
    return uploaded


def upload_media(client, path=None, data=None, mime_type=None, display_name="file"):
    """Upload via the Files API, waiting until the file is ACTIVE."""
    temp_path = None
    try:
        if path is None:
            suffix = ".pdf" if mime_type == "application/pdf" else ".bin"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
                handle.write(data)
                temp_path = handle.name
            path = temp_path

        uploaded = client.files.upload(
            file=str(path),
            config=types.UploadFileConfig(display_name=display_name, mime_type=mime_type),
        )
        return _wait_until_active(client, uploaded)
    finally:
        if temp_path:
            try:
                os.unlink(temp_path)
            except Exception:
                pass


def send_media(
    client,
    model: str,
    config,
    *,
    path=None,
    data=None,
    mime_type=None,
    prompt: str = "Please transcribe this in full.",
    label: str = "",
    context_text: str = None,
    inline_limit: int = INLINE_LIMIT_BYTES,
    verbose: bool = True,
    indent: str = "   ",
    usage_sink: list = None,
):
    """Send one media item plus a prompt, and return ``(text, status)``.

    Chooses inline bytes or the Files API based on size — a request is capped
    at 20 MB in total, so anything close to that has to be uploaded first.
    Uploaded files are always deleted afterwards so they don't eat quota.

    ``usage_sink`` collects token counts instead of printing them, which is
    what parallel callers want: printing from several threads interleaves into
    nonsense, but the totals still need to reach the user.
    """
    uploaded = None
    try:
        size = len(data) if data is not None else os.path.getsize(path)
        use_files_api = size > inline_limit
        if verbose:
            mode = "Files API" if use_files_api else "inline"
            print(f"{indent}└─ 📤 {label} ({size / (1024 * 1024):.1f} MB, {mode})…")

        if use_files_api:
            uploaded = upload_media(
                client, path=path, data=data, mime_type=mime_type,
                display_name=label or "media",
            )
            media_part = uploaded
        else:
            if data is None:
                data = Path(path).read_bytes()
            media_part = types.Part.from_bytes(data=data, mime_type=mime_type)

        contents = [media_part]
        if context_text:
            contents.append(context_text)
        contents.append(prompt)

        response = client.models.generate_content(
            model=model, contents=contents, config=config
        )
        collect_tokens(response, usage_sink)
        if verbose:
            log_tokens(response, label, indent=indent)
        return extract_text(response)

    except genai_errors.APIError as exc:
        return (None, friendly_api_error(exc))
    except Exception as exc:
        return (None, f"❌ {label} failed: {exc}")
    finally:
        if uploaded is not None:
            try:
                client.files.delete(name=uploaded.name)
            except Exception:
                pass


def send_text(client, model: str, config, prompt: str, label: str = "", verbose: bool = True,
              indent: str = "   "):
    """Text-only generation. Returns ``(text, status)``."""
    try:
        response = client.models.generate_content(
            model=model, contents=prompt, config=config
        )
        if verbose:
            log_tokens(response, label, indent=indent)
        return extract_text(response)
    except genai_errors.APIError as exc:
        return (None, friendly_api_error(exc))
    except Exception as exc:
        return (None, f"❌ {label} failed: {exc}")


# --------------------------------------------------------------------------
# Google Drive
# --------------------------------------------------------------------------

class DriveHelper:
    """Mount Drive and hand back a folder to mirror results into."""

    BASE_PATH = "/content/drive/My Drive"

    def __init__(self, default_folder: str):
        self.folder_name = default_folder
        self.mounted = False

    def mount(self) -> bool:
        if self.mounted:
            return True
        try:
            from google.colab import drive
            drive.mount("/content/drive")
            self.mounted = True
            return True
        except Exception as exc:
            print(f"❌ Could not connect Google Drive: {exc}")
            return False

    def folder(self):
        """Return the output folder as a Path, creating it if needed."""
        if not self.mounted:
            return None
        path = Path(self.BASE_PATH) / self.folder_name
        try:
            path.mkdir(parents=True, exist_ok=True)
            return path
        except Exception as exc:
            print(f"⚠️ Could not create the Drive folder: {exc}")
            return None

    def path_for(self, filename: str):
        folder = self.folder()
        return folder / filename if folder else None


# --------------------------------------------------------------------------
# Incremental output
# --------------------------------------------------------------------------

class IncrementalWriter:
    """Append results to disk as they arrive, mirroring to Drive each time.

    Writing only at the end means a browser disconnect at page 280 of 300
    loses everything. Every ``append`` here is immediately durable.
    """

    def __init__(self, path, mirror_path=None, header: str = ""):
        self.path = Path(path)
        self.mirror_path = Path(mirror_path) if mirror_path else None
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._mirror_failed = False
        self.path.write_text(header, encoding="utf-8")
        self._sync()

    def append(self, text: str) -> None:
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(text)
        self._sync()

    def _sync(self) -> None:
        if not self.mirror_path or self._mirror_failed:
            return
        try:
            self.mirror_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.path, self.mirror_path)
        except Exception as exc:
            self._mirror_failed = True
            print(f"   ⚠️ Could not mirror to Drive (continuing locally): {exc}")

    def read(self) -> str:
        return self.path.read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# Audio / video
# --------------------------------------------------------------------------

def have_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def media_duration_seconds(path):
    """Duration in seconds via ffprobe, or None if it can't be determined."""
    if shutil.which("ffprobe") is None:
        return None
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True,
        )
        return float(result.stdout)
    except Exception:
        return None


def to_mono_mp3(source, dest_dir, bitrate: str = "64k"):
    """Convert any audio or video file to a small mono MP3.

    For video this is the important one: sending an MP4 to be transcribed bills
    you for every frame *and* the audio, and a 1 GB upload from Colab is slow
    and failure-prone. Stripping to audio typically turns 1 GB into ~30 MB.

    For audio it normalises everything to one predictable format, which removes
    a whole class of bugs where a file was re-encoded but kept its original
    extension and was then sent with the wrong MIME type. Gemini downmixes to
    mono and downsamples anyway, so nothing that matters to a transcript is lost.
    """
    if not have_ffmpeg():
        raise RuntimeError("ffmpeg is not available, so the audio cannot be converted.")

    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    destination = dest_dir / f"{Path(source).stem}_audio.mp3"

    result = subprocess.run(
        ["ffmpeg", "-y", "-i", str(source), "-vn", "-ac", "1", "-ar", "16000",
         "-c:a", "libmp3lame", "-b:a", bitrate, "-loglevel", "error", str(destination)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if result.returncode != 0 or not destination.exists():
        message = result.stderr.decode("utf-8", "replace").strip()[:400]
        raise RuntimeError(f"ffmpeg could not extract audio: {message or 'no audio track?'}")
    return destination


def split_mono_mp3(source, dest_dir, segment_minutes: int):
    """Cut an MP3 into segments, returning ``[(offset_seconds, path), ...]``.

    Output is always MP3 regardless of the input extension, so the MIME type
    sent to the API can never disagree with the actual bytes.
    """
    from pydub import AudioSegment

    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    segment_ms = int(segment_minutes) * 60 * 1000

    audio = AudioSegment.from_file(str(source))
    if len(audio) <= segment_ms:
        return [(0.0, Path(source))]

    stem = Path(source).stem
    segments = []
    for index, start in enumerate(range(0, len(audio), segment_ms), start=1):
        chunk = audio[start:start + segment_ms]
        path = dest_dir / f"{stem}_segment_{index:02d}.mp3"
        chunk.export(str(path), format="mp3", bitrate="64k",
                     parameters=["-ac", "1", "-ar", "16000"])
        segments.append((start / 1000.0, path))
    return segments


def format_hms(seconds) -> str:
    seconds = max(0, int(seconds))
    return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"


_BRACKET_SPAN = re.compile(r"\[[^\]\n]{0,120}\]")
_HMS = re.compile(r"\b(\d{1,3}):([0-5]\d):([0-5]\d)\b")
_MS = re.compile(r"\b(\d{1,3}):([0-5]\d)\b")


def shift_timestamps(text: str, offset_seconds: float) -> str:
    """Rewrite bracketed timestamps so they refer to the whole recording.

    Each segment is transcribed independently, so the model restarts its clock
    at 00:00:00 every time. Left alone, a quotation cited at 00:04:12 of
    segment 4 is really at 00:34:12 — wrong by half an hour, with nothing on
    screen to suggest it. Shifting is done here rather than by asking the model
    to add the offset itself, because arithmetic is exactly what it is worst at.

    Only text inside square brackets is touched, so "[Kandahar?]" and prose
    containing colons are left alone.
    """
    if not text or not offset_seconds:
        return text

    offset = int(offset_seconds)

    def fix_span(match):
        span = match.group(0)
        if _HMS.search(span):
            return _HMS.sub(
                lambda t: format_hms(
                    int(t.group(1)) * 3600 + int(t.group(2)) * 60 + int(t.group(3)) + offset
                ),
                span,
            )
        if _MS.search(span):
            return _MS.sub(
                lambda t: format_hms(int(t.group(1)) * 60 + int(t.group(2)) + offset),
                span,
            )
        return span

    return _BRACKET_SPAN.sub(fix_span, text)


def continuity_hint(previous_tail: str, max_chars: int = 800) -> str:
    """Context so speaker labels stay stable across segments.

    Without this, "Speaker 1" in segment 4 may be a different person from
    "Speaker 1" in segment 1, which quietly corrupts any speaker-level analysis.
    """
    if not previous_tail:
        return None
    tail = previous_tail.strip()[-max_chars:]
    return (
        "For continuity, here is the end of the previous segment's transcript. "
        "Keep using the same speaker numbering, and do not repeat this text in "
        "your output:\n\n"
        f"{tail}"
    )


# --------------------------------------------------------------------------
# Small file helpers
# --------------------------------------------------------------------------

def clear_folder(folder) -> int:
    """Delete the files in a folder, leaving subfolders alone."""
    path = Path(folder)
    if not path.exists():
        return 0
    removed = 0
    for item in path.glob("*"):
        if item.is_file():
            try:
                item.unlink()
                removed += 1
            except Exception:
                pass
    return removed


def folder_report(folders: dict) -> None:
    print("📊 Current folder status:\n")
    for name in folders.values():
        path = Path(name)
        if path.exists():
            items = [f for f in path.glob("*") if f.is_file()]
            size_kb = sum(f.stat().st_size for f in items) / 1024
            print(f"   📂 {name}/ : {len(items)} file(s), {size_kb:,.1f} KB")
        else:
            print(f"   📂 {name}/ : (not created)")


def environment_report() -> None:
    """One-line sanity check printed by Step 1."""
    print(f"   • zmo_common {__version__}")
    print(f"   • google-genai {genai.__version__}")
    print(f"   • Python {sys.version_info.major}.{sys.version_info.minor}")
    print(f"   • ffmpeg {'available' if have_ffmpeg() else 'NOT FOUND'}")
