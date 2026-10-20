"""Small Colab front end for the same pipelines used by the CLI."""

from __future__ import annotations

import base64
import io
import json
import subprocess
import tempfile
from pathlib import Path

import zmo_audio
import zmo_common as zc
import zmo_ocr
import zmo_summary
from zmo_exports import review_queue, save_review
from zmo_state import RunStore, import_recovery

PIPELINES = {"summary": zmo_summary, "ocr": zmo_ocr, "audio": zmo_audio}


class NotebookSession:
    def __init__(
        self,
        pipeline,
        root,
        selector,
        key_panel,
        config_factory,
        mirror_factory,
        *,
        new_run=lambda: False,
        workers=lambda: 2,
        checkpoint_every=lambda: 50,
    ):
        self.pipeline = pipeline
        self.root = Path(root)
        self.selector = selector
        self.key_panel = key_panel
        self.config_factory = config_factory
        self.mirror_factory = mirror_factory
        self.new_run = new_run
        self.workers = workers
        self.checkpoint_every = checkpoint_every
        self.stores = {}
        self.sources = {}
        self._refresh = []

    def _notify(self):
        for callback in self._refresh:
            callback()

    def processing_panel(self, *, batch_mode=lambda: False):
        import ipywidgets as widgets
        from IPython.display import clear_output, display

        output = widgets.Output()
        limit = widgets.BoundedIntText(
            value=10000,
            min=1,
            max=1_000_000,
            description="Planned requests cap:",
            style={"description_width": "initial"},
        )
        input_rate = widgets.FloatText(value=0, description="$/1M input:")
        output_rate = widgets.FloatText(value=0, description="$/1M output:")
        audio_rate = widgets.FloatText(value=0, description="$/minute:")
        buttons = []

        def action(mode):
            def clicked(_button):
                with output:
                    clear_output()
                    for button in buttons:
                        button.disabled = True
                    client = None
                    try:
                        sources = [Path(path) for path in self.selector.selected]
                        if not sources:
                            raise ValueError("Choose source files in Step 3 first")
                        config = self.config_factory()
                        use_batch = batch_mode()
                        mirror_root, new_run = self.mirror_factory(), self.new_run()
                        module = PIPELINES[self.pipeline]
                        plans = [module.preflight(source, config.options) for source in sources]
                        total = sum(plan["estimated_requests"] for plan in plans)
                        if mode == "preflight":
                            print(json.dumps(plans, ensure_ascii=False, indent=2))
                            print(f"Planned requests: approximately {total}. Limit: {limit.value}.")
                            if self.pipeline == "audio" and audio_rate.value > 0:
                                estimate = (
                                    sum(p["duration_seconds"] for p in plans)
                                    / 60
                                    * audio_rate.value
                                )
                                print(
                                    f"Estimated audio cost at your supplied rate: ${estimate:.2f}"
                                )
                            elif input_rate.value > 0 or output_rate.value > 0:
                                chars = sum(p.get("characters", 0) for p in plans)
                                if chars:
                                    estimate = (
                                        chars / 3 * input_rate.value
                                        + total
                                        * config.options.get("max_output_tokens", 4096)
                                        * output_rate.value
                                    ) / 1_000_000
                                    print(
                                        f"Rough text cost allowance at your rates: ${estimate:.2f}"
                                    )
                                else:
                                    print(
                                        "Image/PDF cost depends on media; test a sample first."
                                    )
                            print(
                                "Estimates exclude retries and model thinking; "
                                "character/token ratios vary. This is not a billing cap."
                            )
                            return
                        if mode == "run" and total > limit.value:
                            raise ValueError(
                                "Planned work exceeds the cap; reduce scope or raise it"
                            )
                        key = self.key_panel.get()
                        if not key and not (
                            self.pipeline == "ocr" and config.options["method"] == "text-layer"
                        ):
                            raise ValueError(zc.key_help_message())
                        if key:
                            client = zc.make_client(key)
                        if (
                            mode == "run"
                            and self.pipeline != "audio"
                            and not (
                                self.pipeline == "ocr" and config.options["method"] == "text-layer"
                            )
                        ):
                            model, message = zc.resolve_model(client, config.model)
                            print(message)
                            if not model:
                                raise ValueError("The selected model is unavailable")
                        workers, cadence = self.workers(), self.checkpoint_every()
                        for source in sources:
                            store = RunStore.open(
                                self.root,
                                source,
                                config,
                                mirror_root=mirror_root,
                                new_run=new_run if mode == "run" else False,
                            )
                            self.stores[store.manifest["run_id"]] = store
                            self.sources[store.manifest["run_id"]] = source
                            self._notify()
                            if mode == "collect":
                                zmo_summary.collect_batch(client, source, store)
                            elif mode == "cancel":
                                zmo_summary.cancel_jobs(client, store)
                            elif (
                                self.pipeline == "summary"
                                and use_batch
                                and source.suffix.lower() == ".xlsx"
                            ):
                                zmo_summary.submit_batch(client, source, store)
                            elif self.pipeline == "summary":
                                module.run(client, source, store, checkpoint_every=cadence)
                            elif self.pipeline == "ocr":
                                module.run(client, source, store, workers=workers)
                            else:
                                module.run(client, source, store)
                            print(
                                f"{source.name}: {store.manifest['state']}. "
                                "Recovery ZIP is available below."
                            )
                    except KeyboardInterrupt:
                        print(
                            "Interrupted. Completed units are saved; "
                            "resume with the same source and settings."
                        )
                    except Exception as exc:
                        print(f"Could not finish: {exc}")
                    finally:
                        if client is not None:
                            client.close()
                        self._notify()
                        for button in buttons:
                            button.disabled = False

            return clicked

        for name, mode in (("Preview scope and cost", "preflight"), ("Run / resume", "run")):
            button = widgets.Button(description=name, layout=widgets.Layout(width="200px"))
            button.on_click(action(mode))
            buttons.append(button)
        if self.pipeline == "summary":
            for name, mode in (
                ("Collect Batch results", "collect"),
                ("Request Batch cancellation", "cancel"),
            ):
                button = widgets.Button(description=name, layout=widgets.Layout(width="230px"))
                button.on_click(action(mode))
                buttons.append(button)
        costs = widgets.Accordion(children=[widgets.VBox([input_rate, output_rate, audio_rate])])
        costs.set_title(0, "Optional: enter current provider prices for a cost estimate")
        costs.selected_index = None
        display(limit, costs, widgets.HBox(buttons), output)

    def recovery_panel(self):
        import ipywidgets as widgets
        from IPython.display import clear_output, display

        output = widgets.Output()
        runs = widgets.Dropdown(description="Run:", layout=widgets.Layout(width="95%"))

        def refresh():
            for path in self.root.glob("*/manifest.json"):
                try:
                    if path.parent.name not in self.stores:
                        self.stores[path.parent.name] = RunStore.load(
                            path.parent, mirror_root=self.mirror_factory()
                        )
                except ValueError:
                    continue
            previous = runs.value
            runs.options = [
                (f"{s.manifest['source']['name']} · {s.manifest['state']} · {key[-22:]}", key)
                for key, s in self.stores.items()
            ]
            if previous in self.stores:
                runs.value = previous

        self._refresh.append(refresh)
        refresh()

        def download(_button):
            from google.colab import files

            with output:
                clear_output()
                if not runs.value:
                    print("No run yet")
                    return
                store = self.stores[runs.value]
                path = store.export_recovery(self.root / f"{runs.value}.zip")
                files.download(str(path))
                print(
                    "ZIP contains outputs and verified recovery state, including partial results."
                )

        def restore(_button):
            from google.colab import files

            with output:
                clear_output()
                try:
                    for name, data in files.upload().items():
                        with tempfile.TemporaryDirectory() as tmp:
                            archive = Path(tmp) / Path(name).name
                            archive.write_bytes(data)
                            store = import_recovery(archive, self.root)
                            self.stores[store.manifest["run_id"]] = store
                            print(
                                "Restored. Select the original source and "
                                "matching settings to resume."
                            )
                    self._notify()
                except Exception as exc:
                    print(f"Recovery import failed: {exc}")

        def cleanup(_button):
            with output:
                clear_output()
                if not runs.value or not confirmation.value:
                    print("Select a run and confirm that its recovery ZIP has been saved.")
                    return
                key = self.key_panel.get()
                if not key:
                    print(zc.key_help_message())
                    return
                client = zc.make_client(key)
                try:
                    done = zmo_summary.cleanup_remote(
                        client, self.stores[runs.value], exported=True
                    )
                    print(
                        "Remote cleanup complete" if done else "Some remote cleanup remains pending"
                    )
                finally:
                    client.close()

        download_button = widgets.Button(
            description="Download recovery ZIP", button_style="success"
        )
        download_button.on_click(download)
        import_button = widgets.Button(description="Import recovery ZIP")
        import_button.on_click(restore)
        display(runs, widgets.HBox([download_button, import_button]), output)
        if self.pipeline == "summary":
            confirmation = widgets.Checkbox(description="I have saved and checked the recovery ZIP")
            runs.observe(lambda _change: setattr(confirmation, "value", False), names="value")
            self._refresh.append(lambda: setattr(confirmation, "value", False))
            cleanup_button = widgets.Button(description="Clean collected remote files")
            cleanup_button.on_click(cleanup)
            display(confirmation, cleanup_button)
            submission = widgets.Text(description="Submission ID:")
            job_name = widgets.Text(description="Remote job:")
            abandon = widgets.Checkbox(
                description="I checked remote jobs; this submission created no job"
            )
            resolve_button = widgets.Button(description="Resolve uncertain submission")

            def resolve(_button):
                with output:
                    clear_output()
                    if not runs.value:
                        return
                    key = self.key_panel.get()
                    if not key:
                        print(zc.key_help_message())
                        return
                    client = zc.make_client(key)
                    try:
                        zmo_summary.resolve_submission(
                            client,
                            self.stores[runs.value],
                            submission.value.strip(),
                            name=job_name.value.strip() or None,
                            abandon=abandon.value,
                        )
                        print("Submission resolved. Resume or collect with matching settings.")
                    except Exception as exc:
                        print(str(exc))
                    finally:
                        client.close()

            resolve_button.on_click(resolve)
            display(
                widgets.HTML(
                    "<p>For an uncertain submission, copy its ID from manifest.json. "
                    "Attach the matching remote job, or confirm none exists before retrying. "
                    "Incorrect abandonment can incur duplicate charges.</p>"
                ),
                submission,
                job_name,
                abandon,
                resolve_button,
            )
        self.review_panel(runs)

    def review_panel(self, runs):
        import ipywidgets as widgets
        from IPython.display import clear_output, display

        units = widgets.Dropdown(description="Unit:")
        raw = widgets.Textarea(disabled=True, layout=widgets.Layout(width="95%", height="180px"))
        corrected = widgets.Textarea(layout=widgets.Layout(width="95%", height="180px"))
        reviewer = widgets.Text(description="Reviewer:")
        note = widgets.Text(description="Note:")
        output = widgets.Output()

        def select_unit(_change=None):
            if not runs.value or not units.value:
                return
            record = self.stores[runs.value].unit(units.value)
            raw.value = record["text"]
            corrected.value = record["text"]
            review = self.stores[runs.value].manifest["reviews"].get(units.value)
            if review:
                saved = json.loads((self.stores[runs.value].directory / review["path"]).read_text())
                current = self.stores[runs.value].manifest["units"][units.value]["sha256"]
                if saved.get("unit_sha256") == current:
                    corrected.value = saved["corrected_text"]

        def select_run(_change=None):
            if not runs.value:
                units.options = []
                return
            store = self.stores[runs.value]
            queue = review_queue(store)
            units.options = [(f"{u['unit_id']} · {u['status']}", u["unit_id"]) for u in queue]
            select_unit()

        def save(_button):
            with output:
                clear_output()
                try:
                    store = self.stores[runs.value]
                    save_review(store, units.value, corrected.value, reviewer.value, note.value)
                    store.sync()
                    print(
                        "Correction saved separately; "
                        "original output is preserved in records.jsonl."
                    )
                except Exception as exc:
                    print(str(exc))

        def show(_button):
            from IPython.display import HTML, Audio, Image
            from pypdf import PdfReader, PdfWriter

            with output:
                clear_output()
                source = self.sources.get(runs.value)
                if not source:
                    print("Select the original source and resume/collect to reconnect its preview.")
                    return
                locator = self.stores[runs.value].unit(units.value)["locator"]
                if source.suffix.lower() == ".pdf":
                    writer = PdfWriter()
                    buffer = io.BytesIO()
                    with source.open("rb") as handle:
                        writer.add_page(PdfReader(handle).pages[locator["page"] - 1])
                        writer.write(buffer)
                    encoded = base64.b64encode(buffer.getvalue()).decode()
                    display(
                        HTML(
                            f'<iframe width="95%" height="600" '
                            f'src="data:application/pdf;base64,{encoded}"></iframe>'
                        )
                    )
                elif self.pipeline == "audio":
                    with tempfile.TemporaryDirectory() as tmp:
                        clip = Path(tmp) / "clip.mp3"
                        subprocess.run(
                            [
                                "ffmpeg",
                                "-y",
                                "-loglevel",
                                "error",
                                "-ss",
                                str(locator.get("offset_seconds", 0)),
                                "-i",
                                str(source),
                                "-t",
                                "30",
                                "-vn",
                                str(clip),
                            ],
                            check=True,
                            capture_output=True,
                            timeout=60,
                        )
                        display(Audio(filename=str(clip)))
                    print(f"30-second sample from {locator.get('offset_seconds', 0)} seconds")
                elif source.suffix.lower() in zmo_ocr.IMAGE_MIME:
                    display(Image(filename=str(source)))
                elif source.suffix.lower() == ".xlsx":
                    options = self.stores[runs.value].manifest["config"]["options"]
                    rows = zmo_summary.source_rows(source, options)
                    try:
                        for row, text, _ in rows:
                            if row == locator["row"]:
                                print(text)
                                break
                    finally:
                        rows.close()
                else:
                    print(source.read_text(encoding="utf-8"))

        runs.observe(select_run, names="value")
        units.observe(select_unit, names="value")
        self._refresh.append(select_run)
        select_run()
        show_button = widgets.Button(description="Show source page / sample")
        show_button.on_click(show)
        save_button = widgets.Button(description="Save reviewed correction")
        save_button.on_click(save)
        panel = widgets.Accordion(
            children=[
                widgets.VBox(
                    [
                        units,
                        show_button,
                        widgets.Label("Original model output"),
                        raw,
                        widgets.Label("Reviewed text"),
                        corrected,
                        reviewer,
                        note,
                        save_button,
                        output,
                    ]
                )
            ]
        )
        panel.set_title(0, "Review flagged units and a reproducible sample of unflagged output")
        panel.selected_index = None
        display(panel)
