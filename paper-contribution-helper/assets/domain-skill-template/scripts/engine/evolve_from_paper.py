#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from common import default_state_dir, read_json, write_json


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATE_DIR = default_state_dir()
DEFAULT_EVOLUTION_DIR = Path("outputs/delta_contribution_evolution_intake")


def slugify(text: str, max_len: int = 80) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    return (text or "paper")[:max_len].strip("_")


def copy_optional(src: Path | None, dst: Path) -> bool:
    if src is None:
        return False
    if not src.exists():
        raise SystemExit(f"Input file does not exist: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def write_default_submission(material_dir: Path, pdf_path: Path, metadata_path: Path | None, source_kind: str, domain_scope: str) -> dict[str, object]:
    metadata = read_json(metadata_path) if metadata_path else {}
    if not metadata:
        metadata = {
            "title": pdf_path.stem,
            "year": None,
            "venue": source_kind,
            "primary_area": domain_scope,
            "keywords": [],
        }
    metadata.setdefault("source_kind", source_kind)
    metadata.setdefault("domain_scope", domain_scope)
    write_json(material_dir / "submission.json", metadata)
    return metadata


def run_analyzer(evolution_dir: Path, state_dir: Path) -> None:
    script = Path(__file__).resolve().with_name("analyze_extracted_papers.py")
    subprocess.run(
        [
            sys.executable,
            str(script),
            "--out-dir",
            str(evolution_dir),
            "--state-dir",
            str(state_dir),
        ],
        check=True,
    )


def decide_from_manifest(evolution_dir: Path) -> dict[str, object]:
    manifest = evolution_dir / "analysis" / "per_paper_analysis_manifest.jsonl"
    records: list[dict[str, object]] = []
    if manifest.exists():
        for line in manifest.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.strip():
                records.append(json.loads(line))
    if not records:
        return {"decision": "manual-review", "reason": "No per-paper analysis record was generated."}

    record = records[0]
    modes = record.get("incremental_mode_analysis") or {}
    mode_hits = [
        name
        for name, payload in modes.items()
        if isinstance(payload, dict) and payload.get("present")
    ]
    review_status = record.get("review_status")
    pdf_status = record.get("pdf_status")
    if mode_hits and pdf_status == "ok":
        decision = "include"
        reason = "The paper has readable PDF text and reusable incremental/delta contribution signals."
    elif mode_hits:
        decision = "manual-review"
        reason = "Reusable incremental signals exist, but PDF extraction is partial or missing."
    else:
        decision = "manual-review" if review_status == "missing" else "exclude"
        reason = "No strong incremental-pattern signal was detected in the available material."
    return {
        "decision": decision,
        "reason": reason,
        "mode_hits": mode_hits,
        "review_status": review_status,
        "pdf_status": pdf_status,
        "analysis_report": record.get("analysis_report"),
    }


def update_evolution_state(state_dir: Path, decision: dict[str, object], evolution_dir: Path) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    state = {
        "schema_version": "1.0",
        "status": "pending-casebook-review",
        "evolving": False,
        "last_decision": decision,
        "last_evolution_dir": evolution_dir.as_posix(),
        "updated_at": dt.datetime.now().isoformat(timespec="seconds"),
    }
    write_json(state_dir / "evolution_state.json", state)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare one new paper for skill evolution with mandatory per-paper analysis.")
    parser.add_argument("--paper-pdf", type=Path, required=True)
    parser.add_argument("--reviews", type=Path, default=None, help="Optional review JSON/MD file.")
    parser.add_argument("--replies", type=Path, default=None, help="Optional author-reply JSON/MD file.")
    parser.add_argument("--metadata", type=Path, default=None, help="Optional submission metadata JSON.")
    parser.add_argument("--evolution-dir", type=Path, default=DEFAULT_EVOLUTION_DIR)
    parser.add_argument("--state-dir", type=Path, default=DEFAULT_STATE_DIR)
    parser.add_argument("--source-kind", default="iclr-openreview")
    parser.add_argument("--domain-scope", default="computer-science")
    parser.add_argument("--case-id", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pdf_path = args.paper_pdf.resolve()
    if not pdf_path.exists():
        raise SystemExit(f"PDF does not exist: {pdf_path}")

    case_id = args.case_id or f"{dt.datetime.now().strftime('%Y%m%d%H%M%S')}_{slugify(pdf_path.stem)}"
    evolution_dir = args.evolution_dir.resolve()
    material_dir = evolution_dir / "materials" / "_by_paper" / case_id
    material_dir.mkdir(parents=True, exist_ok=True)

    copy_optional(pdf_path, material_dir / "paper.pdf")
    if args.reviews:
        suffix = ".json" if args.reviews.suffix.lower() == ".json" else ".md"
        copy_optional(args.reviews.resolve(), material_dir / f"official_reviews{suffix}")
    if args.replies:
        suffix = ".json" if args.replies.suffix.lower() == ".json" else ".md"
        copy_optional(args.replies.resolve(), material_dir / f"author_replies{suffix}")
    write_default_submission(material_dir, pdf_path, args.metadata.resolve() if args.metadata else None, args.source_kind, args.domain_scope)

    run_analyzer(evolution_dir, args.state_dir.resolve())
    decision = decide_from_manifest(evolution_dir)
    write_json(evolution_dir / "evolution_decision.json", decision)
    update_evolution_state(args.state_dir.resolve(), decision, evolution_dir)
    print(json.dumps({"case_id": case_id, "decision": decision, "evolution_dir": str(evolution_dir)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
