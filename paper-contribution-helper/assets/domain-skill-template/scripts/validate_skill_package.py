#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


REQUIRED = [
    "SKILL.md",
    "agents/openai.yaml",
    "references/knowledge_manifest.json",
    "references/anonymous_casebook.jsonl",
    "references/per_pdf_report_synthesis.md",
    "references/llm_deep_read_synthesis.md",
    "references/llm_deep_reading_workflow.md",
    "references/project_corpus_direct_workflow.md",
    "references/assistant_local_deep_read_workflow.md",
    "references/acp_command_file_workflow.md",
    "references/evidence_policy.md",
    "references/evolution_policy.md",
    "references/usage_workflows.md",
    "references/report_playbook/reader_friendly_reporting.md",
    "references/report_playbook/positive_reframing_patterns.md",
    "references/report_playbook/latent_contribution_mining.md",
    "references/report_playbook/reviewer_attack_taxonomy.md",
    "references/report_playbook/rebuttal_pattern_library.md",
    "references/report_playbook/github_review_skill_digest.md",
    "scripts/startup_check.py",
    "scripts/acp_command_file_bridge.py",
    "scripts/analyze_new_pdf.py",
    "scripts/evolve_casebook.py",
    "scripts/engine/common.py",
    "scripts/engine/startup_check.py",
    "scripts/engine/scan_corpus_catalog.py",
    "scripts/engine/configure_initialization.py",
    "scripts/engine/build_incremental_knowledge_base.py",
    "scripts/engine/standardize_local_pdf_intake.py",
    "scripts/engine/validate_project_corpus.py",
    "scripts/engine/initialize_from_project_corpus.py",
    "scripts/engine/analyze_extracted_papers.py",
    "scripts/engine/prepare_assistant_deep_read_packets.py",
    "scripts/engine/validate_assistant_deep_read_records.py",
    "scripts/engine/import_assistant_deep_read_records.py",
    "scripts/engine/synthesize_initialized_resources.py",
    "scripts/engine/evolve_from_paper.py",
    "references/base_delta/contract_state.md",
    "references/base_delta/contract_evidence.md",
    "references/base_delta/contract_output_language.md",
    "references/base_delta/contract_project_corpus.md",
    "references/base_delta/workflow_startup_initialization.md",
    "references/base_delta/workflow_knowledge_base_build.md",
    "references/base_delta/workflow_project_discovery.md",
    "references/base_delta/workflow_local_pdf_intake.md",
    "references/base_delta/workflow_target_domain_inference.md",
    "references/base_delta/workflow_target_paper_reframing.md",
    "references/base_delta/contract_story_options.md",
    "references/base_delta/contract_target_report_quality.md",
]

REQUIRED_TEXT = {
    "SKILL.md": [
        "workflow_target_paper_reframing.md",
        "do not stop at the script output",
        "LLM deep-reading",
        "contract_target_report_quality.md",
        "strong packaging diagnosis",
        "six ranked story-route slots",
        "recommended route combination",
        "reader-friendly plain-language explanations",
        "top-conference story reconstruction",
        "workflow_target_domain_inference.md",
        "project_corpus_direct_workflow.md",
        "assistant_local_deep_read_workflow.md",
        "Do not paste full PDF text",
        "PDF supplied without purpose",
        "domain seed",
        "project-internal files",
    ],
    "references/usage_workflows.md": [
        "workflow_target_paper_reframing.md",
        "contract_target_report_quality.md",
        "pre-pass",
        "llm_deep_reading.status=complete",
        "acp_command_file_bridge.py",
        "six ranked story-route slots",
        "risky wording to avoid",
        "plain-language explanation",
        "problem equation",
        "project_corpus_direct_workflow.md",
        "Do not paste full PDFs",
        "command-file",
        "PDF Mode Selection",
        "Domain-seed initialization",
        "project-internal",
    ],
    "references/project_corpus_direct_workflow.md": [
        "project-run",
        "local-pdf",
        "Do not paste full PDFs",
        "--reuse-llm",
        "llm_deep_reading.status=\"complete\"",
        "ACP command-file fallback",
        "Project-Internal Files",
        "project_internal_analysis_started",
        "--llm-deep-read-mode optional",
        "prepare_assistant_deep_read_packets.py",
        "import_assistant_deep_read_records.py",
    ],
    "references/assistant_local_deep_read_workflow.md": [
        "current assistant",
        "prepare_assistant_deep_read_packets.py",
        "validate_assistant_deep_read_records.py",
        "import_assistant_deep_read_records.py",
        "assistant_deep_read_records.jsonl",
        "workflow_alignment=\"llm-full-paper-deep-read\"",
    ],
    "references/base_delta/workflow_target_paper_reframing.md": [
        "contract_target_report_quality.md",
        "Story Option Board",
        "manuscript triggers",
        "recommended route combination",
        "top-conference story reconstruction",
        "plain-language meaning",
    ],
    "references/base_delta/workflow_target_domain_inference.md": [
        "at least 1 and at most 3",
        "focus domains or subfields",
        "routing metadata only",
    ],
    "references/base_delta/contract_target_report_quality.md": [
        "Strong packaging diagnosis",
        "Story-route candidate board",
        "Reviewer attack preplay",
        "Manuscript trigger localization",
        "Rebuttal pattern library",
        "risky wording to avoid",
        "safe claim boundaries",
        "plain-language version",
        "problem equation",
        "contribution ladder",
    ],
    "references/report_playbook/reader_friendly_reporting.md": [
        "Plain-language version",
        "Technical thesis",
        "Concrete example or analogy",
    ],
    "references/report_playbook/latent_contribution_mining.md": [
        "paper-explicit",
        "latent-but-supported",
        "future-boundary hook",
    ],
    "references/report_playbook/reviewer_attack_taxonomy.md": [
        "baseline fairness",
        "mechanism evidence",
        "no-new-experiment repair",
    ],
    "references/report_playbook/rebuttal_pattern_library.md": [
        "Setting Boundary Defense",
        "Constraint-Driven Coupling Defense",
        "Dangerous Patterns",
    ],
    "scripts/analyze_new_pdf.py": [
        "prepass_only",
        "full_reframing_report_scaffold.md",
        "delta-contribution-reframer",
        "QUALITY_REPORT_SECTIONS",
        "ATTACK_PREPLAY_COLUMNS",
        "RESIDUAL_RISK_COLUMNS",
        "TOP_CONFERENCE_RECONSTRUCTION_COLUMNS",
        "PLAIN_LANGUAGE_ROUTE_COLUMNS",
    ],
    "scripts/engine/analyze_extracted_papers.py": [
        "workflow_alignment",
        "delta-contribution-reframer",
        "llm-full-paper-deep-read",
        "Claim-Support Matrix",
        "Ranked Story Option Board",
    ],
    "scripts/engine/prepare_assistant_deep_read_packets.py": [
        "assistant_deep_read_packets",
        "packet.md",
        "chunk_files",
        "current-assistant-local-file-deep-read",
    ],
    "scripts/engine/validate_assistant_deep_read_records.py": [
        "llm-full-paper-deep-read",
        "reading_status",
        "claim_support_matrix",
        "story_option_board",
    ],
    "scripts/engine/import_assistant_deep_read_records.py": [
        "validate_assistant_deep_read_records.py",
        "analyze_extracted_papers.py",
        "--llm-provider",
        "jsonl",
    ],
    "scripts/acp_command_file_bridge.py": [
        "LLM_REQUEST_JSON",
        "LLM_RESPONSE_JSON",
        "PAPER_HELPER_ACPX_BIN",
        "prompt_file",
    ],
    "references/acp_command_file_workflow.md": [
        "command-file",
        "LLM_REQUEST_JSON",
        "scripts/acp_command_file_bridge.py",
        "API key",
        "fallback",
    ],
    "scripts/engine/synthesize_initialized_resources.py": [
        "validate_manifest_alignment",
        "REQUIRED_MANIFEST_FIELDS",
        "workflow_alignment",
        "llm_deep_reading",
        "surface_delta",
        "stronger_delta",
        "story_route_use",
        "raw_weakness_pattern",
    ],
}


def absolute_patterns() -> list[re.Pattern[str]]:
    prefixes = ["/" + part + "/" for part in ["Users", "home", "mnt", "var/folders"]]
    patterns = [re.compile(r"(?<![A-Za-z0-9_])[A-Za-z]:[\\/](?![nrtbfavNRTBFAV])[^\n\r\"']+")]
    patterns.extend(re.compile(re.escape(prefix)) for prefix in prefixes)
    return patterns


def forbidden_generated_artifacts(skill_dir: Path) -> list[str]:
    forbidden: list[str] = []
    for path in skill_dir.rglob("*"):
        rel = path.relative_to(skill_dir).as_posix()
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
            forbidden.append(rel)
    return forbidden


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a packaged self-contained delta reframer skill.")
    parser.add_argument("--skill-dir", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    skill_dir = args.skill_dir.resolve()
    missing: list[str] = []
    empty: list[str] = []
    absolute_findings: list[dict[str, str]] = []
    forbidden_artifacts = forbidden_generated_artifacts(skill_dir)
    for rel in REQUIRED:
        path = skill_dir / rel
        if not path.exists():
            missing.append(rel)
        elif path.is_file() and path.stat().st_size == 0 and rel not in {
            "references/anonymous_casebook.jsonl",
            "references/per_pdf_report_synthesis.md",
            "references/llm_deep_read_synthesis.md",
        }:
            empty.append(rel)
    missing_text: list[dict[str, str]] = []
    for rel, needles in REQUIRED_TEXT.items():
        path = skill_dir / rel
        text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
        for needle in needles:
            if needle not in text:
                missing_text.append({"path": rel, "missing": needle})
    scan_files = [skill_dir / "SKILL.md"]
    scan_files.extend(path for path in (skill_dir / "references").rglob("*") if path.is_file())
    scan_files.extend(path for path in (skill_dir / "scripts").rglob("*.py") if path.is_file())
    for path in scan_files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in absolute_patterns():
            for match in pattern.findall(text):
                absolute_findings.append({"path": str(path.relative_to(skill_dir)), "match": match[:120]})
    report = {
        "skill_dir": str(skill_dir),
        "base_knowledge_available": (skill_dir / "references" / "anonymous_casebook.jsonl").stat().st_size > 2
        and (skill_dir / "references" / "per_pdf_report_synthesis.md").stat().st_size > 2
        and (skill_dir / "references" / "llm_deep_read_synthesis.md").stat().st_size > 2
        if (skill_dir / "references" / "anonymous_casebook.jsonl").exists()
        and (skill_dir / "references" / "per_pdf_report_synthesis.md").exists()
        and (skill_dir / "references" / "llm_deep_read_synthesis.md").exists()
        else False,
        "blank_initializer_available": not missing and not empty,
        "valid": not missing and not empty and not absolute_findings,
        "missing": missing,
        "empty": empty,
        "missing_required_text": missing_text,
        "absolute_path_findings": absolute_findings,
        "forbidden_generated_artifacts": forbidden_artifacts,
    }
    report["valid"] = report["valid"] and not missing_text and not forbidden_artifacts
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["valid"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
