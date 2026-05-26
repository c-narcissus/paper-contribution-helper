#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

from common import default_state_dir, read_json, write_json


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATE_DIR = default_state_dir()


def run_script(script_name: str, args: list[str]) -> None:
    script = Path(__file__).resolve().with_name(script_name)
    subprocess.run([sys.executable, str(script), *args], check=True)


def update_skill_state(run_dir: Path, state_dir: Path, focus_domains: list[str], years: list[str], source_kind: str, domain_scope: str) -> None:
    validation = read_json(run_dir / "validation" / "project_corpus_validation.json")
    per_paper_state = read_json(state_dir / "per_paper_analysis_state.json")
    now = dt.datetime.now().isoformat(timespec="seconds")
    resources = [
        {"path": (run_dir / "validation" / "project_corpus_validation.md").as_posix(), "kind": "project_corpus_validation", "status": "available"},
        {"path": (run_dir / "analysis" / "per_paper_analysis_manifest.jsonl").as_posix(), "kind": "per_paper_analysis_manifest", "status": "available"},
        {"path": (run_dir / "reports" / "per_paper_analysis_index.md").as_posix(), "kind": "per_paper_analysis_index", "status": "available"},
    ]
    for rel in [
        "index/screened_incremental_candidates.csv",
        "index/high_risk_candidates.csv",
        "index/all_candidates.csv",
        "index/incremental_all_index.csv",
    ]:
        path = run_dir / rel
        if path.exists():
            resources.append({"path": path.as_posix(), "kind": Path(rel).stem, "status": "available"})

    knowledge_state = {
        "schema_version": "1.0",
        "knowledge_available": bool(validation.get("paper_count")),
        "source_kind": source_kind,
        "domain_scope": domain_scope,
        "focus_domains": focus_domains,
        "years": years,
        "project_run_dir": run_dir.as_posix(),
        "paper_count": validation.get("paper_count", 0),
        "per_paper_analysis": per_paper_state,
        "resources": resources,
        "updated_at": now,
    }
    init_state = {
        "schema_version": "1.0",
        "initialized": bool(validation.get("paper_count")),
        "status": "ready" if validation.get("paper_count") else "empty_result",
        "reason": "Knowledge initialized from a validated project corpus run.",
        "source_kind": source_kind,
        "domain_scope": domain_scope,
        "focus_domains": focus_domains,
        "years": years,
        "corpus_source": "project-run-dir",
        "project_run_dir": run_dir.as_posix(),
        "per_paper_analysis_required": True,
        "per_paper_analysis_complete": bool(per_paper_state.get("report_coverage_complete")),
        "per_paper_analysis_state": per_paper_state,
        "updated_at": now,
    }
    write_json(state_dir / "knowledge_state.json", knowledge_state)
    write_json(state_dir / "initialization_state.json", init_state)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize skill knowledge from a validated project-level corpus run.")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, default=DEFAULT_STATE_DIR)
    parser.add_argument("--focus-domains", nargs="*", default=[])
    parser.add_argument("--years", nargs="*", default=[])
    parser.add_argument("--source-kind", default="project-corpus")
    parser.add_argument("--domain-scope", default="computer-science")
    parser.add_argument("--allow-validation-warnings", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = args.run_dir.resolve()
    state_dir = args.state_dir.resolve()
    if not run_dir.exists():
        raise SystemExit(f"Run directory does not exist: {run_dir}")

    validation_args = ["--run-dir", str(run_dir)]
    if args.allow_validation_warnings:
        try:
            run_script("validate_project_corpus.py", validation_args)
        except subprocess.CalledProcessError:
            pass
    else:
        run_script("validate_project_corpus.py", validation_args)

    run_script("analyze_extracted_papers.py", ["--out-dir", str(run_dir), "--state-dir", str(state_dir)])
    update_skill_state(run_dir, state_dir, args.focus_domains, args.years, args.source_kind, args.domain_scope)
    run_script(
        "synthesize_initialized_resources.py",
        [
            "--run-dir",
            str(run_dir),
            "--focus-domains",
            *args.focus_domains,
            "--years",
            *args.years,
            "--source-kind",
            args.source_kind,
            "--domain-scope",
            args.domain_scope,
            "--state-dir",
            str(state_dir),
        ],
    )
    print(json.dumps({"initialized_from": str(run_dir), "state_dir": str(state_dir)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
