#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


REQUIRED = [
    "SKILL.md",
    "VERSION",
    "agents/openai.yaml",
    "references/module_index.md",
    "references/context_loading_policy.md",
    "references/path_policy.md",
    "references/architecture.md",
    "references/project_corpus_direct_workflow.md",
    "references/assistant_local_deep_read_workflow.md",
    "references/acp_command_file_workflow.md",
    "references/build_workflow.md",
    "references/source_modes.md",
    "references/target_domain_inference.md",
    "scripts/acp_command_file_bridge.py",
    "scripts/engine/prepare_assistant_deep_read_packets.py",
    "scripts/engine/validate_assistant_deep_read_records.py",
    "scripts/engine/import_assistant_deep_read_records.py",
    "scripts/build_domain_skill.py",
    "scripts/package_domain_skill.py",
]

TEXT_SUFFIXES = {".md", ".py", ".yaml", ".yml", ".json", ".jsonl", ".txt", ".tmpl"}
FORBIDDEN_TEXT = ["delta-contribution-reframer-" + "factory", "v1.0." + "1"]
GENERATED_DIRS = {"runs", "build", "dist", "__pycache__"}
ABSOLUTE_PATH_PATTERNS = [
    re.compile(r"(?<![A-Za-z0-9_])[A-Za-z]:[\\/](?![nrtbfavNRTBFAV])[^\s\"'<>]+"),
    re.compile(r"(?<![A-Za-z0-9_])/(?:Users|home|mnt|var/folders)/[^\s\"'<>]+"),
]


def text_files(root: Path) -> list[Path]:
    return [
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in TEXT_SUFFIXES
        and not GENERATED_DIRS.intersection(path.relative_to(root).parts)
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate paper-contribution-helper modular packaging.")
    parser.add_argument("--skill-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--max-skill-lines", type=int, default=120)
    args = parser.parse_args()
    skill_dir = args.skill_dir.resolve()

    missing = [rel for rel in REQUIRED if not (skill_dir / rel).exists()]
    cache_artifacts = [
        path.relative_to(skill_dir).as_posix()
        for path in skill_dir.rglob("*")
        if not GENERATED_DIRS.intersection(path.relative_to(skill_dir).parts[:-1])
        and ("__pycache__" in path.parts or path.suffix.lower() in {".pyc", ".pyo"})
    ]
    skill_lines = (skill_dir / "SKILL.md").read_text(encoding="utf-8", errors="replace").splitlines()
    long_router = len(skill_lines) > args.max_skill_lines

    forbidden_hits: list[dict[str, str]] = []
    absolute_path_hits: list[dict[str, str]] = []
    for path in text_files(skill_dir):
        rel = path.relative_to(skill_dir).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for needle in FORBIDDEN_TEXT:
            if needle in text:
                forbidden_hits.append({"path": rel, "match": needle})
        for pattern in ABSOLUTE_PATH_PATTERNS:
            for match in pattern.findall(text):
                absolute_path_hits.append({"path": rel, "match": match[:160]})

    report = {
        "skill_dir": str(skill_dir),
        "skill_md_lines": len(skill_lines),
        "max_skill_lines": args.max_skill_lines,
        "valid": not missing and not cache_artifacts and not long_router and not forbidden_hits and not absolute_path_hits,
        "missing": missing,
        "cache_artifacts": cache_artifacts,
        "long_router": long_router,
        "forbidden_text_hits": forbidden_hits,
        "absolute_path_hits": absolute_path_hits,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["valid"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
