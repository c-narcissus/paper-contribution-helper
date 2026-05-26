#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path


def default_overlay_dir(skill_name: str) -> Path:
    return Path.cwd() / f".{skill_name}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Append a project-local anonymous evolution card from a new-paper analysis record.")
    parser.add_argument("--analysis-record", type=Path, required=True)
    parser.add_argument("--skill-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--overlay-dir", type=Path, default=None)
    parser.add_argument("--case-label", default=None)
    args = parser.parse_args()
    skill_dir = args.skill_dir.resolve()
    manifest = json.loads((skill_dir / "references" / "knowledge_manifest.json").read_text(encoding="utf-8"))
    skill_name = manifest.get("skill_name") or skill_dir.name
    overlay_dir = args.overlay_dir or default_overlay_dir(skill_name)
    record = json.loads(args.analysis_record.read_text(encoding="utf-8", errors="replace"))
    overlay_path = overlay_dir / "evolution" / "evolving_casebook.jsonl"
    overlay_path.parent.mkdir(parents=True, exist_ok=True)
    card = {
        "schema_version": "1.0",
        "case_id": f"local-evolution-{dt.datetime.now().strftime('%Y%m%d%H%M%S')}",
        "case_label": args.case_label or "new-paper-local-evolution",
        "source": "project-local new paper analysis",
        "evidence_label": "new-paper-derived",
        "review_attack_mode": record.get("review_attack_mode"),
        "base_case_analogies": record.get("recommended_base_case_labels", []),
        "pattern_summary": {k: bool(v) for k, v in (record.get("pattern_hits") or {}).items()},
        "anonymization": "No title, authors, URLs, forum ids, or unique benchmark bundles are stored by this script.",
    }
    with overlay_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(card, ensure_ascii=False) + "\n")
    print(json.dumps({"overlay": str(overlay_path), "case_id": card["case_id"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
