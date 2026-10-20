"""Page-oriented OCR with bounded concurrency and independent durable results."""

from __future__ import annotations

import io
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path

from google.genai import types
from pypdf import PdfReader, PdfWriter

import zmo_common as zc
from zmo_exports import export_records
from zmo_state import RunConfig, UnitResult

USER_PROMPT = "Transcribe this page completely, following the instructions given."
IMAGE_MIME = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".heic": "image/heic",
    ".heif": "image/heif",
}


def configuration(
    model, instructions, *, first_page=0, last_page=0, reduced_safety=False, method="ocr"
):
    if first_page < 0 or last_page < 0 or method not in {"ocr", "text-layer"}:
        raise ValueError("Invalid page range or extraction method")
    return RunConfig(
        "ocr",
        model,
        instructions + "\n\n--- USER PROMPT ---\n" + USER_PROMPT,
        {
            "instructions": instructions,
            "user_prompt": USER_PROMPT,
            "first_page": first_page,
            "last_page": last_page,
            "reduced_safety": reduced_safety,
            "method": method,
            "max_output_tokens": zc.MAX_OUTPUT_TOKENS,
            "pdf_resolution": "medium",
            "image_resolution": "high",
        },
    )


def page_range(total, options):
    first, last = options["first_page"] or 1, options["last_page"] or total
    if total < 1 or not 1 <= first <= last <= total:
        raise ValueError(f"Choose a valid page range within 1–{total}")
    return range(first, last + 1)


def preflight(source, options):
    source = Path(source)
    if source.suffix.lower() != ".pdf":
        if source.suffix.lower() not in IMAGE_MIME:
            raise ValueError("Unsupported image format")
        if options["method"] == "text-layer":
            raise ValueError("Text-layer extraction is available only for PDFs")
        return {"source": source.name, "pages": 1, "estimated_requests": 1, "text_samples": []}
    with source.open("rb") as handle:
        reader = PdfReader(handle)
        selected = page_range(len(reader.pages), options)
        samples = [
            {"page": number, "text": (reader.pages[number - 1].extract_text() or "")[:1000]}
            for number in list(selected)[:3]
        ]
        return {
            "source": source.name,
            "pages": len(selected),
            "range": [selected.start, selected.stop - 1],
            "text_samples": samples,
            "estimated_requests": len(selected) if options["method"] == "ocr" else 0,
        }


def export_ocr(store):
    parts = []
    for unit in store.units():
        number = unit["locator"]["page"]
        parts.append(f"--- Page {number} ---\n")
        if unit["status"] != "complete":
            parts.append(f"[{unit['status'].upper()}: {unit['error'] or 'review required'}]\n")
        # Keep the provider's text unchanged, including diplomatic whitespace.
        parts.append(unit["text"] + "\n\n")
    store.artifact("transcription.txt", "".join(parts))
    export_records(store)


def run(client, source, store, *, workers=2, checkpoint_every=5, on_progress=print):
    store.check_source(source)
    if not 1 <= workers <= 4:
        raise ValueError("Use between one and four OCR workers")
    source = Path(source)
    options = store.manifest["config"]["options"]
    preflight(source, options)
    is_pdf = source.suffix.lower() == ".pdf"
    config = zc.build_config(
        system_instruction=options["instructions"],
        media_resolution=types.MediaResolution.MEDIA_RESOLUTION_MEDIUM
        if is_pdf
        else types.MediaResolution.MEDIA_RESOLUTION_HIGH,
        safety=options["reduced_safety"],
        max_output_tokens=options["max_output_tokens"],
    )
    store.manifest["state"] = "running"
    store.save()
    handle = source.open("rb") if is_pdf else None
    pool = ThreadPoolExecutor(max_workers=workers)
    pending = {}
    completed = 0
    interrupted = False

    def request(number, data):
        metadata = []
        args = (
            {"data": data, "mime_type": "application/pdf"}
            if is_pdf
            else {"path": source, "mime_type": IMAGE_MIME[source.suffix.lower()]}
        )
        text, status = zc.send_media(
            client,
            store.manifest["config"]["model"],
            config,
            **args,
            prompt=USER_PROMPT,
            verbose=False,
            response_sink=metadata,
        )
        mapped = (
            "complete" if status == "ok" else "truncated" if status == "truncated" else "failed"
        )
        return UnitResult(
            f"page-{number}",
            mapped,
            text=text or "",
            raw=text or "",
            locator={"page": number},
            metadata={"method": "ocr", "responses": metadata},
            error="" if status == "ok" else status,
        )

    try:
        reader = PdfReader(handle) if is_pdf else None
        selected = list(page_range(len(reader.pages), options)) if is_pdf else [1]
        remaining = iter(number for number in selected if not store.complete(f"page-{number}"))

        def fill():
            nonlocal completed
            while len(pending) < workers:
                try:
                    number = next(remaining)
                except StopIteration:
                    break
                try:
                    if options["method"] == "text-layer":
                        text = reader.pages[number - 1].extract_text() or ""
                        store.record(
                            UnitResult(
                                f"page-{number}",
                                "complete" if text.strip() else "needs-ocr",
                                text=text,
                                raw=text,
                                locator={"page": number},
                                metadata={"method": "text-layer"},
                            )
                        )
                        completed += 1
                        if completed % max(1, checkpoint_every) == 0:
                            export_ocr(store)
                            store.sync()
                        continue
                    data = None
                    if is_pdf:
                        writer = PdfWriter()
                        writer.add_page(reader.pages[number - 1])
                        buffer = io.BytesIO()
                        writer.write(buffer)
                        data = buffer.getvalue()
                    pending[pool.submit(request, number, data)] = number
                except Exception as exc:
                    store.record(
                        UnitResult(
                            f"page-{number}", "failed", locator={"page": number}, error=str(exc)
                        )
                    )

        fill()
        while pending:
            ready, _ = wait(pending, return_when=FIRST_COMPLETED)
            for future in ready:
                number = pending.pop(future)
                try:
                    result = future.result()
                except Exception as exc:
                    result = UnitResult(
                        f"page-{number}", "failed", locator={"page": number}, error=str(exc)
                    )
                store.record(result)
                completed += 1
                on_progress(f"Page {number}: {result.status}")
                if completed % max(1, checkpoint_every) == 0:
                    export_ocr(store)
                    store.sync()
            fill()
        store.manifest["state"] = (
            "complete" if all(store.complete(f"page-{p}") for p in selected) else "partial"
        )
    except BaseException:
        interrupted = True
        store.manifest["state"] = "interrupted"
        raise
    finally:
        for future in pending:
            future.cancel()
        # Running calls may already be billed: preserve their results before exit.
        pool.shutdown(wait=True, cancel_futures=True)
        if interrupted:
            for future, number in pending.items():
                if future.done() and not future.cancelled():
                    try:
                        store.record(future.result())
                    except Exception as exc:
                        store.record(
                            UnitResult(
                                f"page-{number}", "failed", locator={"page": number}, error=str(exc)
                            )
                        )
        if handle:
            handle.close()
        store.save()
        export_ocr(store)
        store.sync()
    return store
