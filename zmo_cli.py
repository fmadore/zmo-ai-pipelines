"""Run, resume, inspect, collect and export the same pipelines outside Colab."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import zmo_audio
import zmo_common as zc
import zmo_ocr
import zmo_summary
from zmo_evaluate import evaluate_corpus
from zmo_exports import export_records, review_queue, save_review
from zmo_state import RunStore, import_recovery, write_json

PIPELINES = {"summary": zmo_summary, "ocr": zmo_ocr, "audio": zmo_audio}


def parser():
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("preflight", "run"):
        sub = commands.add_parser(name)
        sub.add_argument("pipeline", choices=PIPELINES)
        sub.add_argument("source", type=Path)
        sub.add_argument("--config", type=Path, required=True, help="JSON configuration arguments")
        if name == "run":
            sub.add_argument("--output", type=Path, default=Path("results"))
            sub.add_argument("--mirror", type=Path)
            sub.add_argument("--new-run", action="store_true")
            sub.add_argument("--batch", action="store_true")
            sub.add_argument("--workers", type=int, default=2)
    for name in (
        "resume",
        "collect",
        "status",
        "cancel",
        "reconcile",
        "cleanup",
        "export",
        "review",
        "resolve",
    ):
        sub = commands.add_parser(name)
        sub.add_argument("run", type=Path)
        sub.add_argument("--mirror", type=Path)
        if name in {"resume", "collect"}:
            sub.add_argument("--source", type=Path, required=True)
        if name == "cleanup":
            sub.add_argument("--confirm-exported", action="store_true")
        if name == "export":
            sub.add_argument("destination", type=Path)
        if name == "review":
            sub.add_argument("--unit")
            sub.add_argument("--text-file", type=Path)
            sub.add_argument("--reviewer", default="")
            sub.add_argument("--note", default="")
        if name == "resolve":
            sub.add_argument("submission_id")
            choice = sub.add_mutually_exclusive_group(required=True)
            choice.add_argument("--job-name")
            choice.add_argument(
                "--confirm-no-remote-job",
                action="store_true",
                help="Only after checking remote jobs; retrying may incur duplicate charges",
            )
    sub = commands.add_parser("import")
    sub.add_argument("archive", type=Path)
    sub.add_argument("--output", type=Path, default=Path("results"))
    sub = commands.add_parser("evaluate")
    sub.add_argument("manifest", type=Path)
    sub.add_argument("--output", type=Path)
    for flag in ("casefold", "collapse-whitespace", "unicode-nfc"):
        sub.add_argument("--" + flag, action="store_true")
    return root


def execute(args):
    command = args.command
    if command == "evaluate":
        result = evaluate_corpus(
            args.manifest,
            casefold=args.casefold,
            collapse_whitespace=args.collapse_whitespace,
            unicode_nfc=args.unicode_nfc,
        )
        if args.output:
            write_json(args.output, result)
        return result
    if command == "import":
        return {"run": str(import_recovery(args.archive, args.output).directory)}
    if command in {"preflight", "run"}:
        module = PIPELINES[args.pipeline]
        config = module.configuration(**json.loads(args.config.read_text(encoding="utf-8")))
        plan = module.preflight(args.source, config.options)
        if command == "preflight":
            return plan
        if args.batch and args.pipeline != "summary":
            raise ValueError("Batch mode is available for spreadsheet summaries only")
        store = RunStore.open(
            args.output, args.source, config, mirror_root=args.mirror, new_run=args.new_run
        )
    else:
        store = RunStore.load(args.run, mirror_root=args.mirror)
        module = PIPELINES[store.manifest["config"]["pipeline"]]
    if command == "status":
        return {
            "run": str(store.directory),
            "manifest": store.manifest,
            "units": [{"id": u["unit_id"], "status": u["status"]} for u in store.units()],
        }
    if command == "export":
        export_records(store)
        return {"archive": str(store.export_recovery(args.destination))}
    if command == "review":
        if args.unit:
            if not args.text_file:
                raise ValueError("Supply --text-file and --reviewer to save a correction")
            save_review(
                store,
                args.unit,
                args.text_file.read_text(encoding="utf-8"),
                args.reviewer,
                args.note,
            )
            store.sync()
        return {"queue": review_queue(store)}
    if (
        command in {"collect", "cancel", "reconcile", "cleanup", "resolve"}
        and module != zmo_summary
    ):
        raise ValueError("This operation applies only to summary Batch runs")
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    offline = module == zmo_ocr and store.manifest["config"]["options"]["method"] == "text-layer"
    if not key and not offline:
        raise ValueError("Set GEMINI_API_KEY before a network operation")
    client = zc.make_client(key) if key else None
    try:
        if command in {"run", "resume"}:
            if not offline and module != zmo_audio:
                model, message = zc.resolve_model(client, store.manifest["config"]["model"])
                if not model:
                    raise ValueError(message)
            if getattr(args, "batch", False):
                zmo_summary.submit_batch(client, args.source, store)
            elif module == zmo_ocr:
                module.run(client, args.source, store, workers=getattr(args, "workers", 2))
            else:
                module.run(client, args.source, store)
        elif command == "collect":
            zmo_summary.collect_batch(client, args.source, store)
        elif command == "cancel":
            zmo_summary.cancel_jobs(client, store)
        elif command == "reconcile":
            zmo_summary.reconcile_jobs(client, store)
            store.sync()
        elif command == "resolve":
            zmo_summary.resolve_submission(
                client,
                store,
                args.submission_id,
                name=args.job_name,
                abandon=args.confirm_no_remote_job,
            )
        elif command == "cleanup":
            if not zmo_summary.cleanup_remote(client, store, exported=args.confirm_exported):
                raise ValueError("Remote cleanup remains pending; preserve the recovery archive")
    finally:
        if client is not None:
            client.close()
    return {"run": str(store.directory), "state": store.manifest["state"]}


def main(argv=None):
    root = parser()
    args = root.parse_args(argv)
    try:
        print(json.dumps(execute(args), ensure_ascii=False, indent=2))
    except (ValueError, OSError) as exc:
        root.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
