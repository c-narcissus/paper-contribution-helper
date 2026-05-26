#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import write_json


REQUIRED_KEYS = [
    "schema_version",
    "workflow_alignment",
    "reading_status",
    "paper_key",
    "source_grounding_summary",
    "authoritative_report_markdown",
    "paper_identity",
    "scientific_problem_and_positioning",
    "method_deep_read",
    "formulas_algorithms_and_assumptions",
    "figure_table_and_experiment_analysis",
    "claim_support_matrix",
    "delta_reframing",
    "story_option_board",
    "reviewer_attack_preplay",
    "review_reply_coverage",
    "reproducibility_gaps",
    "limitations_and_scope_boundaries",
    "no_new_experiment_reuse_priorities",
    "reusable_anonymous_patterns",
    "uncertainty_notes",
]

REQUIRED_ALIGNMENT = "llm-full-paper-deep-read"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        for physical_line, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise SystemExit(f"Line {physical_line} is not a JSON object in {path}")
            records.append(payload)
    return records


def expected_keys_from_run(run_dir: Path | None) -> set[str]:
    if not run_dir:
        return set()
    manifest = run_dir / "analysis" / "per_paper_analysis_manifest.jsonl"
    if not manifest.exists():
        return set()
    keys: set[str] = set()
    for record in load_jsonl(manifest):
        key = str(record.get("paper_key") or "")
        if key:
            keys.add(key)
    return keys


def validate(records: list[dict[str, Any]], expected_keys: set[str], require_all: bool) -> dict[str, Any]:
    problems: list[str] = []
    seen: set[str] = set()
    for index, record in enumerate(records, 1):
        key = str(record.get("paper_key") or f"record-{index}")
        if key in seen:
            problems.append(f"{key}: duplicate paper_key")
        seen.add(key)
        missing = [name for name in REQUIRED_KEYS if name not in record]
        if missing:
            problems.append(f"{key}: missing keys: {', '.join(missing)}")
        if record.get("workflow_alignment") != REQUIRED_ALIGNMENT:
            problems.append(f"{key}: workflow_alignment must be {REQUIRED_ALIGNMENT}")
        if record.get("reading_status") != "complete":
            problems.append(f"{key}: reading_status must be complete")
        report = str(record.get("authoritative_report_markdown") or "").strip()
        if len(report) < 400:
            problems.append(f"{key}: authoritative_report_markdown is too short")
        if not isinstance(record.get("source_grounding_summary"), dict):
            problems.append(f"{key}: source_grounding_summary must be an object")
        if not isinstance(record.get("claim_support_matrix"), list) or not record.get("claim_support_matrix"):
            problems.append(f"{key}: claim_support_matrix must be a non-empty list")
        if not isinstance(record.get("story_option_board"), list) or not record.get("story_option_board"):
            problems.append(f"{key}: story_option_board must be a non-empty list")
        if not isinstance(record.get("reusable_anonymous_patterns"), list) or not record.get("reusable_anonymous_patterns"):
            problems.append(f"{key}: reusable_anonymous_patterns must be a non-empty list")
        if expected_keys and key not in expected_keys:
            problems.append(f"{key}: not present in run manifest")
    missing_expected = sorted(expected_keys - seen) if require_all else []
    if missing_expected:
        preview = ", ".join(missing_expected[:20])
        extra = f" ... {len(missing_expected) - 20} more" if len(missing_expected) > 20 else ""
        problems.append(f"missing records for manifest papers: {preview}{extra}")
    return {
        "schema_version": "1.0",
        "valid": not problems,
        "record_count": len(records),
        "expected_count": len(expected_keys) if expected_keys else None,
        "problem_count": len(problems),
        "problems": problems,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate current-assistant local deep-read JSONL records.")
    parser.add_argument("--records-jsonl", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--require-all", action="store_true")
    parser.add_argument("--out-json", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records_path = args.records_jsonl.resolve()
    records = load_jsonl(records_path)
    expected = expected_keys_from_run(args.run_dir.resolve() if args.run_dir else None)
    report = validate(records, expected, args.require_all)
    if args.out_json:
        write_json(args.out_json.resolve(), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["valid"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
