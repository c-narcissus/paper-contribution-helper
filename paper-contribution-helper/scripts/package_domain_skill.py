#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any


REQUIRED_INITIALIZED_RESOURCES = ["anonymous_casebook.jsonl", "per_pdf_report_synthesis.md", "llm_deep_read_synthesis.md"]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def checksum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def nonempty(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 2


def slugify(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "-", value.lower()).strip("-")
    return value or "delta-reframer-domain"


def factory_root() -> Path:
    return Path(__file__).resolve().parents[1]


def template_root() -> Path:
    return factory_root() / "assets" / "domain-skill-template"


def render_template(text: str, variables: dict[str, str]) -> str:
    rendered = text
    for key, value in variables.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    return rendered


def copy_template_tree(target: Path, variables: dict[str, str]) -> None:
    root = template_root()
    for source in root.rglob("*"):
        if source.is_dir():
            continue
        if "__pycache__" in source.parts or source.suffix in {".pyc", ".pyo"}:
            continue
        rel = source.relative_to(root)
        target_rel = Path(str(rel).removesuffix(".tmpl"))
        content = read_text(source)
        if source.suffix == ".tmpl":
            content = render_template(content, variables)
        write_text(target / target_rel, content)


def copy_knowledge(source_home: Path, target_skill: Path, allow_empty_base: bool, focus_domains: list[str], years: list[str]) -> list[dict[str, Any]]:
    source_refs = source_home / "references"
    target_refs = target_skill / "references"
    resources: list[dict[str, Any]] = []
    for name in REQUIRED_INITIALIZED_RESOURCES:
        source = source_refs / name
        if not nonempty(source) and not allow_empty_base:
            raise SystemExit(f"Required initialized resource is missing or empty: {source}")
        target = target_refs / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if nonempty(source):
            shutil.copy2(source, target)
        else:
            target.write_text("", encoding="utf-8")
        resources.append({"path": f"references/{name}", "sha256": checksum(target), "bytes": target.stat().st_size})
    profiles = sorted(source_refs.glob("domain_profile*.md"))
    if not profiles and not allow_empty_base:
        raise SystemExit(f"No domain profile found under {source_refs}")
    if profiles:
        for source in profiles:
            target = target_refs / source.name
            shutil.copy2(source, target)
            resources.append({"path": f"references/{source.name}", "sha256": checksum(target), "bytes": target.stat().st_size})
    else:
        target = target_refs / "domain_profile_blank.md"
        write_text(
            target,
            "\n".join(
                [
                    "# Blank Delta Reframer Domain Profile",
                    "",
                    f"- Focus domains: {', '.join(focus_domains) or 'unspecified'}",
                    f"- Years: {', '.join(years) or 'unspecified'}",
                    "- Base anonymous knowledge: not initialized.",
                    "- This generated skill carries the blank initializer engine and can build reusable knowledge from user-supplied paper sources.",
                ]
            ),
        )
        resources.append({"path": "references/domain_profile_blank.md", "sha256": checksum(target), "bytes": target.stat().st_size})
    return resources


def build_manifest(skill_name: str, display_name: str, knowledge_state: dict[str, Any], resources: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "skill_name": skill_name,
        "display_name": display_name,
        "packaged_at": dt.datetime.now().isoformat(timespec="seconds"),
        "source_kind": knowledge_state.get("source_kind"),
        "domain_scope": knowledge_state.get("domain_scope"),
        "focus_domains": knowledge_state.get("focus_domains", []),
        "years": knowledge_state.get("years", []),
        "base_paper_count": knowledge_state.get("paper_count"),
        "base_anonymous_case_count": (knowledge_state.get("summary") or {}).get("anonymous_case_count"),
        "knowledge_mode": "frozen anonymous base knowledge plus project-local evolution overlay",
        "llm_deep_read_required_for_base_corpus": True,
        "llm_deep_read_status": knowledge_state.get("llm_deep_read_status") or knowledge_state.get("llm_deep_read_status_counts", {}),
        "old_pdfs_required_for_reuse": False,
        "old_project_run_required_for_reuse": False,
        "new_target_paper_requires_user_supplied_evidence": True,
        "blank_initializer_available": True,
        "resources": resources,
        "path_policy": "All resource paths are package-relative.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Package synthesized anonymous knowledge into a standalone delta-reframer skill.")
    parser.add_argument("--source-project-home", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--skill-name", required=True)
    parser.add_argument("--display-name", default=None)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--allow-empty-base", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_home = args.source_project_home.resolve()
    out_dir = args.out_dir.resolve()
    skill_name = slugify(args.skill_name)
    display_name = args.display_name or skill_name.replace("-", " ").title()
    target_skill = out_dir / skill_name
    if target_skill.exists():
        if not args.overwrite:
            raise SystemExit(f"Target skill already exists; pass --overwrite to replace it: {target_skill}")
        shutil.rmtree(target_skill)
    target_skill.mkdir(parents=True, exist_ok=True)
    knowledge_state = read_json(source_home / "state" / "knowledge_state.json")
    focus_domains = [str(x) for x in knowledge_state.get("focus_domains", [])]
    years = [str(x) for x in knowledge_state.get("years", [])]
    variables = {
        "SKILL_NAME": skill_name,
        "DISPLAY_NAME": display_name,
        "DOMAINS": ", ".join(focus_domains) or "packaged domain",
        "YEARS": ", ".join(years) or "packaged years",
    }
    copy_template_tree(target_skill, variables)
    if not knowledge_state:
        knowledge_state = {
            "schema_version": "1.0",
            "knowledge_available": False,
            "source_kind": "not-initialized",
            "domain_scope": "computer-science",
            "focus_domains": [],
            "years": [],
            "paper_count": 0,
            "summary": {"anonymous_case_count": 0},
        }
    resources = copy_knowledge(source_home, target_skill, args.allow_empty_base, focus_domains, years)
    write_json(target_skill / "references" / "knowledge_manifest.json", build_manifest(skill_name, display_name, knowledge_state, resources))
    print(json.dumps({"skill_dir": str(target_skill), "resources": resources}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
