#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from common import read_json, write_json


MATERIAL_ROOT = Path("materials") / "_by_paper"
REQUIRED_OPTIONAL_STATUS = "source_status.json"
RECOGNIZED_REVIEW_FILES = [
    "official_reviews.json",
    "official_reviews.md",
    "meta_review.json",
    "meta_review.md",
    "decision.json",
    "decision.md",
]
RECOGNIZED_REPLY_FILES = [
    "author_replies.json",
    "author_replies.md",
    "reviewer_followups.json",
    "reviewer_followups.md",
    "public_comments.json",
]


def has_any(folder: Path, names: list[str]) -> bool:
    return any((folder / name).exists() for name in names)


def inspect_material(folder: Path, run_dir: Path) -> dict[str, Any]:
    status = read_json(folder / REQUIRED_OPTIONAL_STATUS)
    pdf_present = (folder / "paper.pdf").exists()
    submission_present = (folder / "submission.json").exists()
    review_present = has_any(folder, RECOGNIZED_REVIEW_FILES)
    reply_present = has_any(folder, RECOGNIZED_REPLY_FILES)
    issues: list[str] = []
    if not pdf_present:
        issues.append("missing paper.pdf")
    if not submission_present:
        issues.append("missing submission.json")
    if not (folder / REQUIRED_OPTIONAL_STATUS).exists():
        issues.append("missing source_status.json")
    if not review_present and not status.get("reviews_missing"):
        issues.append("reviews absent but source_status.reviews_missing is not true")
    if not reply_present and not status.get("replies_missing"):
        issues.append("replies absent but source_status.replies_missing is not true")
    return {
        "paper_key": folder.name,
        "material_dir": folder.relative_to(run_dir).as_posix(),
        "pdf_present": pdf_present,
        "submission_present": submission_present,
        "source_status_present": (folder / REQUIRED_OPTIONAL_STATUS).exists(),
        "review_present": review_present,
        "reply_present": reply_present,
        "issues": issues,
    }


def validate(run_dir: Path) -> dict[str, Any]:
    materials_root = run_dir / MATERIAL_ROOT
    records: list[dict[str, Any]] = []
    if materials_root.exists():
        for folder in sorted(path for path in materials_root.iterdir() if path.is_dir()):
            records.append(inspect_material(folder, run_dir))
    issue_count = sum(len(record["issues"]) for record in records)
    counters = {
        "pdf_present": sum(1 for record in records if record["pdf_present"]),
        "reviews_present": sum(1 for record in records if record["review_present"]),
        "replies_present": sum(1 for record in records if record["reply_present"]),
        "source_status_present": sum(1 for record in records if record["source_status_present"]),
    }
    source_kinds = Counter()
    for folder in sorted(path for path in materials_root.iterdir() if path.is_dir()) if materials_root.exists() else []:
        status = read_json(folder / REQUIRED_OPTIONAL_STATUS)
        source_kinds[str(status.get("source_kind") or "unknown")] += 1
    return {
        "schema_version": "1.0",
        "valid": bool(records) and issue_count == 0,
        "run_dir": run_dir.as_posix(),
        "paper_count": len(records),
        "issue_count": issue_count,
        "counts": counters,
        "source_kinds": dict(source_kinds),
        "records": records,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Project Corpus Validation",
        "",
        f"- Run dir: `{report['run_dir']}`",
        f"- Valid: `{report['valid']}`",
        f"- Paper count: {report['paper_count']}",
        f"- Issue count: {report['issue_count']}",
        f"- Source kinds: {report['source_kinds']}",
        "",
        "| Paper key | PDF | Reviews | Replies | Source status | Issues |",
        "|---|---|---|---|---|---|",
    ]
    for record in report["records"]:
        issues = "; ".join(record["issues"]) if record["issues"] else ""
        lines.append(
            f"| `{record['paper_key']}` | {record['pdf_present']} | {record['review_present']} | {record['reply_present']} | {record['source_status_present']} | {issues} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a project-level corpus run before skill initialization/evolution.")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, default=None)
    parser.add_argument("--out-md", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = args.run_dir.resolve()
    if not run_dir.exists():
        raise SystemExit(f"Run directory does not exist: {run_dir}")
    report = validate(run_dir)
    out_json = args.out_json or (run_dir / "validation" / "project_corpus_validation.json")
    out_md = args.out_md or (run_dir / "validation" / "project_corpus_validation.md")
    write_json(out_json, report)
    write_markdown(report, out_md)
    print(json.dumps({"valid": report["valid"], "paper_count": report["paper_count"], "issue_count": report["issue_count"], "out_json": str(out_json), "out_md": str(out_md)}, ensure_ascii=False, indent=2))
    if not report["valid"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
