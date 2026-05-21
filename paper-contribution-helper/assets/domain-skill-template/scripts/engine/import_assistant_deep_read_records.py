#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def engine_dir() -> Path:
    return Path(__file__).resolve().parent


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate and import current-assistant local deep-read records into a project run.")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--records-jsonl", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, default=None)
    parser.add_argument("--llm-chunk-chars", type=int, default=55000)
    parser.add_argument("--llm-timeout", type=int, default=240)
    parser.add_argument("--require-all", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = args.run_dir.resolve()
    records = args.records_jsonl.resolve()
    state_dir = (args.state_dir or run_dir / "analysis" / "assistant_local_state").resolve()
    validation_out = run_dir / "analysis" / "assistant_deep_read_validation.json"
    validate_cmd = [
        sys.executable,
        str(engine_dir() / "validate_assistant_deep_read_records.py"),
        "--records-jsonl",
        str(records),
        "--run-dir",
        str(run_dir),
        "--out-json",
        str(validation_out),
    ]
    if args.require_all:
        validate_cmd.append("--require-all")
    run(validate_cmd)
    run(
        [
            sys.executable,
            str(engine_dir() / "analyze_extracted_papers.py"),
            "--out-dir",
            str(run_dir),
            "--state-dir",
            str(state_dir),
            "--llm-deep-read-mode",
            "required",
            "--llm-provider",
            "jsonl",
            "--llm-results-jsonl",
            str(records),
            "--llm-chunk-chars",
            str(args.llm_chunk_chars),
            "--llm-timeout",
            str(args.llm_timeout),
        ]
    )
    print(
        json.dumps(
            {
                "schema_version": "1.0",
                "run_dir": str(run_dir),
                "records_jsonl": str(records),
                "validation": str(validation_out),
                "state_dir": str(state_dir),
                "imported": True,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
