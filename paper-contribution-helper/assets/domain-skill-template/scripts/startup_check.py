#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def nonempty(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 2


def default_skill_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def project_overlay_dir(skill_name: str) -> Path:
    return Path.cwd() / f".{skill_name}"


def fallback_engine_status(skill_dir: Path) -> dict[str, object]:
    required_scripts = [
        "common.py",
        "startup_check.py",
        "scan_corpus_catalog.py",
        "configure_initialization.py",
        "build_incremental_knowledge_base.py",
        "standardize_local_pdf_intake.py",
        "validate_project_corpus.py",
        "initialize_from_project_corpus.py",
        "analyze_extracted_papers.py",
        "prepare_assistant_deep_read_packets.py",
        "validate_assistant_deep_read_records.py",
        "import_assistant_deep_read_records.py",
        "synthesize_initialized_resources.py",
        "evolve_from_paper.py",
    ]
    top_level_scripts = [
        "acp_command_file_bridge.py",
    ]
    top_level_refs = [
        "project_corpus_direct_workflow.md",
        "assistant_local_deep_read_workflow.md",
        "acp_command_file_workflow.md",
        "llm_deep_reading_workflow.md",
        "usage_workflows.md",
    ]
    required_refs = [
        "contract_state.md",
        "contract_evidence.md",
        "contract_output_language.md",
        "contract_project_corpus.md",
        "contract_story_options.md",
        "contract_target_report_quality.md",
        "workflow_startup_initialization.md",
        "workflow_knowledge_base_build.md",
        "workflow_project_discovery.md",
        "workflow_local_pdf_intake.md",
        "workflow_target_domain_inference.md",
        "workflow_target_paper_reframing.md",
    ]
    scripts = [{"path": f"scripts/engine/{name}", "exists": (skill_dir / "scripts" / "engine" / name).exists()} for name in required_scripts]
    scripts.extend({"path": f"scripts/{name}", "exists": (skill_dir / "scripts" / name).exists()} for name in top_level_scripts)
    refs = [{"path": f"references/base_delta/{name}", "exists": (skill_dir / "references" / "base_delta" / name).exists()} for name in required_refs]
    refs.extend({"path": f"references/{name}", "exists": (skill_dir / "references" / name).exists()} for name in top_level_refs)
    return {
        "available": all(item["exists"] for item in scripts + refs),
        "scripts": scripts,
        "references": refs,
    }


def report_playbook_status(skill_dir: Path) -> dict[str, object]:
    required = [
        "reader_friendly_reporting.md",
        "positive_reframing_patterns.md",
        "latent_contribution_mining.md",
        "reviewer_attack_taxonomy.md",
        "rebuttal_pattern_library.md",
        "github_review_skill_digest.md",
    ]
    refs = [{"path": f"references/report_playbook/{name}", "exists": (skill_dir / "references" / "report_playbook" / name).exists()} for name in required]
    return {"available": all(item["exists"] for item in refs), "references": refs}


def main() -> None:
    parser = argparse.ArgumentParser(description="Check packaged delta-reframer skill status.")
    parser.add_argument("--skill-dir", type=Path, default=default_skill_dir())
    args = parser.parse_args()
    skill_dir = args.skill_dir.resolve()
    manifest_path = skill_dir / "references" / "knowledge_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig")) if manifest_path.exists() else {}
    skill_name = manifest.get("skill_name") or skill_dir.name
    resources = []
    for rel in ["references/anonymous_casebook.jsonl", "references/per_pdf_report_synthesis.md", "references/llm_deep_read_synthesis.md"]:
        path = skill_dir / rel
        resources.append(
            {
                "path": rel,
                "exists": path.exists(),
                "nonempty": nonempty(path),
                "bytes": path.stat().st_size if path.exists() else 0,
            }
        )
    overlay = project_overlay_dir(skill_name)
    fallback = fallback_engine_status(skill_dir)
    report_playbook = report_playbook_status(skill_dir)
    base_available = all(item["nonempty"] for item in resources)
    report = {
        "skill_dir": str(skill_dir),
        "skill_name": skill_name,
        "base_knowledge_available": base_available,
        "blank_initializer_available": bool(fallback["available"]),
        "usable": base_available or bool(fallback["available"]),
        "requires_old_pdfs": False,
        "requires_project_initialization": False if base_available else "only if user wants reusable base knowledge",
        "resources": resources,
        "fallback_engine": fallback,
        "report_playbook": report_playbook,
        "project_overlay_dir": str(overlay),
        "project_overlay_exists": overlay.exists(),
        "evolution_overlay": str(overlay / "evolution" / "evolving_casebook.jsonl"),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
