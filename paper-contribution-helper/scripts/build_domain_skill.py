#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def script_dir() -> Path:
    return Path(__file__).resolve().parent


def engine_dir() -> Path:
    return script_dir() / "engine"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def default_run_dir(skill_name: str, source_mode: str) -> Path:
    return Path.cwd() / "runs" / f"{skill_name}_{source_mode}"


def default_build_home(skill_name: str) -> Path:
    return Path.cwd() / "build" / skill_name / ".delta-contribution-reframer"


PATH_CONFIG_FIELDS = {
    "target_paper",
    "out_dir",
    "project_run_dir",
    "run_dir",
    "pdf",
    "pdf_dir",
    "reviews_dir",
    "replies_dir",
    "metadata_dir",
    "build_home",
    "llm_request_dir",
    "llm_results_jsonl",
}

LIST_CONFIG_FIELDS = {"focus_domains", "years"}

DEFAULTS: dict[str, Any] = {
    "focus_domains": [],
    "years": [],
    "cap": 100,
    "review_pool_size": None,
    "preselect_multiplier": 4,
    "source_kind": "project-corpus",
    "domain_scope": "computer-science",
    "clean_build": True,
    "overwrite": False,
    "llm_deep_read_mode": "required",
    "llm_provider": "openai-responses",
    "llm_model": os.environ.get("OPENAI_MODEL", "gpt-5.2"),
    "llm_api_key_env": "OPENAI_API_KEY",
    "llm_api_base": os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1"),
    "llm_command": None,
    "llm_file_poll_interval": 2.0,
    "llm_chunk_chars": 55000,
    "llm_timeout": 240,
    "reuse_llm": False,
}


def config_lookup(config: dict[str, Any], field: str) -> Any:
    if field in config:
        return config[field]
    dashed = field.replace("_", "-")
    if dashed in config:
        return config[dashed]
    return None


def normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def apply_config_file(args: argparse.Namespace) -> argparse.Namespace:
    config_path = getattr(args, "config_file", None)
    if not config_path:
        return args
    config = json.loads(config_path.expanduser().resolve().read_text(encoding="utf-8-sig", errors="replace"))
    if not isinstance(config, dict):
        raise SystemExit(f"--config-file must contain one JSON object: {config_path}")
    for field in [
        "skill_name",
        "display_name",
        "focus_domains",
        "target_paper",
        "years",
        "source_mode",
        "out_dir",
        "project_run_dir",
        "run_dir",
        "pdf",
        "pdf_dir",
        "reviews_dir",
        "replies_dir",
        "metadata_dir",
        "cap",
        "review_pool_size",
        "preselect_multiplier",
        "source_kind",
        "domain_scope",
        "build_home",
        "clean_build",
        "overwrite",
        "llm_deep_read_mode",
        "llm_provider",
        "llm_model",
        "llm_api_key_env",
        "llm_api_base",
        "llm_command",
        "llm_request_dir",
        "llm_file_poll_interval",
        "llm_results_jsonl",
        "llm_chunk_chars",
        "llm_timeout",
        "reuse_llm",
    ]:
        current = getattr(args, field, None)
        incoming = config_lookup(config, field)
        if incoming is None:
            continue
        if field in LIST_CONFIG_FIELDS:
            if not current:
                setattr(args, field, normalize_list(incoming))
        elif field in PATH_CONFIG_FIELDS:
            if current is None:
                setattr(args, field, Path(str(incoming)))
        elif current is None:
            setattr(args, field, incoming)
    return args


def apply_defaults(args: argparse.Namespace) -> argparse.Namespace:
    for field, value in DEFAULTS.items():
        current = getattr(args, field, None)
        if current is None:
            setattr(args, field, list(value) if isinstance(value, list) else value)
    return args


def validate_args(args: argparse.Namespace) -> None:
    missing = []
    for field in ["skill_name", "years", "source_mode", "out_dir"]:
        value = getattr(args, field, None)
        if value is None or value == []:
            missing.append(field)
    if missing:
        raise SystemExit(f"Missing required build inputs: {', '.join(missing)}. Provide CLI args or --config-file.")


def analysis_helpers() -> Any:
    engine = str(engine_dir())
    if engine not in sys.path:
        sys.path.insert(0, engine)
    import analyze_extracted_papers  # type: ignore

    return analyze_extracted_papers


def domain_chunk_prompt(target_name: str, chunk: str, chunk_index: int, total_chunks: int) -> str:
    return "\n".join(
        [
            "You are reading a target research paper only to infer search/filter domains for generating a specialized paper-contribution helper skill.",
            "The target paper is a domain seed in this step, not the paper being analyzed for contribution packaging.",
            "The domains will be used to screen comparable reference papers, so they must be concise and searchable.",
            "Return one valid JSON object only.",
            "",
            "Required JSON keys:",
            "- schema_version: string",
            "- chunk_index: integer",
            "- domain_candidates: list of objects with domain, subfield, search_label, evidence, confidence",
            "- method_and_setting_signals: list",
            "- avoid_as_primary_domain: list",
            "- uncertainty_notes: list",
            "",
            "Rules:",
            "- Prefer specific CS/AI/ML domains or subfields over broad labels like machine learning.",
            "- Include the subfield when the paper clearly belongs to one.",
            "- Do not infer more than five candidates for this chunk.",
            "- Ground every candidate in paper text evidence from this chunk.",
            "- Do not produce contribution diagnosis, story routes, reviewer attacks, rebuttal text, or manuscript edits.",
            "",
            f"Target paper file/name: {target_name}",
            f"Chunk: {chunk_index} of {total_chunks}",
            "",
            "PDF chunk text:",
            chunk,
        ]
    )


def domain_synthesis_prompt(target_name: str, chunk_results: list[dict[str, Any]]) -> str:
    return "\n".join(
        [
            "You are synthesizing full-paper domain readings for a delta-contribution reframer factory.",
            "Choose the best focus domains for screening reference papers for this target paper.",
            "This is domain-seed inference only; do not analyze or rewrite the target paper's contribution.",
            "Return one valid JSON object only.",
            "",
            "Required JSON keys:",
            "- schema_version: string",
            "- inferred_focus_domains: list of 1 to 3 concise search labels",
            "- domain_rationale: list of objects with focus_domain, why_it_matches, evidence, useful_query_terms",
            "- rejected_or_too_broad_domains: list",
            "- confidence: string",
            "- uncertainty_notes: list",
            "",
            "Selection rules:",
            "- Return at least one and at most three focus domains.",
            "- Each focus domain should be usable directly as a keyword/search filter.",
            "- Prefer labels that include a useful subfield, e.g. 'federated semi-supervised learning', 'multimodal retrieval', or 'graph neural networks'.",
            "- Avoid generic labels unless the paper gives no stronger subfield evidence.",
            "- Do not invent a domain unsupported by the chunk readings.",
            "- Do not produce contribution diagnosis, story routes, reviewer attacks, rebuttal text, or manuscript edits.",
            "",
            f"Target paper file/name: {target_name}",
            "",
            "Chunk-level readings:",
            json.dumps(chunk_results, ensure_ascii=False, indent=2),
        ]
    )


def normalize_inferred_domains(payload: dict[str, Any]) -> list[str]:
    raw = payload.get("inferred_focus_domains") or payload.get("focus_domains") or payload.get("domains") or []
    domains: list[str] = []
    if isinstance(raw, str):
        raw = [raw]
    for item in raw:
        if isinstance(item, dict):
            label = item.get("focus_domain") or item.get("search_label")
            if not label and item.get("domain") and item.get("subfield"):
                label = f"{item['domain']} {item['subfield']}"
            if not label:
                label = item.get("domain") or item.get("subfield")
        else:
            label = item
        label = str(label or "").strip()
        if label and label.lower() not in {existing.lower() for existing in domains}:
            domains.append(label)
        if len(domains) >= 3:
            break
    if not domains:
        raise SystemExit("Target-paper domain inference returned no usable focus domains.")
    return domains


def infer_focus_domains_from_target(args: argparse.Namespace, build_home: Path) -> list[str]:
    if args.llm_provider in {"off", "jsonl"}:
        raise SystemExit("--target-paper domain inference requires a live LLM provider: openai-responses, openai-chat, command, or command-file")
    helper = analysis_helpers()
    target = args.target_paper.expanduser().resolve()
    if not target.exists():
        raise SystemExit(f"Target paper does not exist: {target}")
    pdf_status, pdf_text, pdf_error, page_rows = helper.extract_pdf_text(target)
    if not pdf_text.strip():
        raise SystemExit(f"Could not extract target paper text for domain inference: {pdf_status}: {pdf_error}")

    chunks = helper.chunk_text(pdf_text, args.llm_chunk_chars)
    chunk_results: list[dict[str, Any]] = []
    for index, chunk in enumerate(chunks, 1):
        prompt = domain_chunk_prompt(target.name, chunk, index, len(chunks))
        chunk_results.append(helper.call_llm(prompt, args, "target-paper", f"domain-inference-chunk-{index:03d}"))

    synthesis = helper.call_llm(domain_synthesis_prompt(target.name, chunk_results), args, "target-paper", "domain-inference-synthesis")
    domains = normalize_inferred_domains(synthesis)
    state_dir = build_home / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    inference_record = {
        "schema_version": "1.0",
        "mode": "domain-seed-inference-for-specialized-skill-generation",
        "target_paper": str(target),
        "pdf_status": pdf_status,
        "pdf_error": pdf_error,
        "pdf_text_chars": len(pdf_text),
        "page_count": len(page_rows),
        "llm_provider": args.llm_provider,
        "inferred_focus_domains": domains,
        "synthesis": synthesis,
        "chunk_results": chunk_results,
    }
    out_path = state_dir / "target_domain_inference.json"
    out_path.write_text(json.dumps(inference_record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"target_domain_inference": str(out_path), "inferred_focus_domains": domains}, ensure_ascii=False, indent=2), file=sys.stderr)
    return domains


def ensure_focus_domains(args: argparse.Namespace, build_home: Path) -> None:
    args.focus_domains = [domain for domain in (args.focus_domains or []) if str(domain).strip()]
    if args.focus_domains:
        return
    if not args.target_paper:
        raise SystemExit("--focus-domains is required unless --target-paper is provided for target-paper domain inference")
    args.focus_domains = infer_focus_domains_from_target(args, build_home)


def prepare_run(args: argparse.Namespace, skill_name: str) -> tuple[Path, str]:
    source_mode = args.source_mode
    if source_mode == "blank":
        return Path(), "not-initialized"
    if source_mode == "project-run":
        if not args.project_run_dir:
            raise SystemExit("--project-run-dir is required for source-mode=project-run")
        return args.project_run_dir.resolve(), args.source_kind
    run_dir = (args.run_dir or default_run_dir(skill_name, source_mode)).resolve()
    if source_mode == "local-pdf":
        cmd = [sys.executable, str(engine_dir() / "standardize_local_pdf_intake.py"), "--run-dir", str(run_dir), "--source-kind", "local-pdf", "--domain-scope", args.domain_scope]
        if args.pdf:
            cmd.extend(["--pdf", str(args.pdf.resolve())])
        elif args.pdf_dir:
            cmd.extend(["--pdf-dir", str(args.pdf_dir.resolve())])
        else:
            raise SystemExit("--pdf or --pdf-dir is required for source-mode=local-pdf")
        if args.reviews_dir:
            cmd.extend(["--reviews-dir", str(args.reviews_dir.resolve())])
        if args.replies_dir:
            cmd.extend(["--replies-dir", str(args.replies_dir.resolve())])
        if args.metadata_dir:
            cmd.extend(["--metadata-dir", str(args.metadata_dir.resolve())])
        run(cmd)
        return run_dir, "local-pdf"
    if source_mode == "openreview-iclr":
        if len(args.years) != 1:
            raise SystemExit("source-mode=openreview-iclr currently expects exactly one --years value")
        cmd = [
            sys.executable,
            str(script_dir() / "discover_iclr_openreview.py"),
            "--year",
            str(args.years[0]),
            "--run-dir",
            str(run_dir),
            "--cap",
            str(args.cap),
            "--preselect-multiplier",
            str(args.preselect_multiplier),
            "--focus-domains",
            *args.focus_domains,
        ]
        if args.review_pool_size:
            cmd.extend(["--review-pool-size", str(args.review_pool_size)])
        run(cmd)
        return run_dir, "iclr-openreview"
    raise SystemExit(f"Unsupported source mode: {source_mode}")


def synthesize(run_dir: Path, build_home: Path, args: argparse.Namespace, source_kind: str) -> None:
    state_dir = build_home / "state"
    references_dir = build_home / "references"
    state_dir.mkdir(parents=True, exist_ok=True)
    references_dir.mkdir(parents=True, exist_ok=True)
    run([sys.executable, str(engine_dir() / "validate_project_corpus.py"), "--run-dir", str(run_dir)])
    analyze_cmd = [
        sys.executable,
        str(engine_dir() / "analyze_extracted_papers.py"),
        "--out-dir",
        str(run_dir),
        "--state-dir",
        str(state_dir),
        "--llm-deep-read-mode",
        args.llm_deep_read_mode,
        "--llm-provider",
        args.llm_provider,
        "--llm-model",
        args.llm_model,
        "--llm-api-key-env",
        args.llm_api_key_env,
        "--llm-api-base",
        args.llm_api_base,
        "--llm-chunk-chars",
        str(args.llm_chunk_chars),
        "--llm-timeout",
        str(args.llm_timeout),
    ]
    if args.llm_command:
        analyze_cmd.extend(["--llm-command", args.llm_command])
    if args.llm_request_dir:
        analyze_cmd.extend(["--llm-request-dir", str(args.llm_request_dir.resolve())])
    analyze_cmd.extend(["--llm-file-poll-interval", str(args.llm_file_poll_interval)])
    if args.llm_results_jsonl:
        analyze_cmd.extend(["--llm-results-jsonl", str(args.llm_results_jsonl.resolve())])
    if args.reuse_llm:
        analyze_cmd.append("--reuse-llm")
    run(analyze_cmd)
    synthesis_config = state_dir / "synthesis_config.json"
    synthesis_config.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "run_dir": str(run_dir),
                "focus_domains": args.focus_domains,
                "years": [str(year) for year in args.years],
                "source_kind": source_kind,
                "domain_scope": args.domain_scope,
                "state_dir": str(state_dir),
                "references_dir": str(references_dir),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    run([sys.executable, str(engine_dir() / "synthesize_initialized_resources.py"), "--config-file", str(synthesis_config)])


def package(build_home: Path, args: argparse.Namespace, skill_name: str) -> None:
    cmd = [
        sys.executable,
        str(script_dir() / "package_domain_skill.py"),
        "--source-project-home",
        str(build_home),
        "--out-dir",
        str(args.out_dir.resolve()),
        "--skill-name",
        skill_name,
    ]
    if args.display_name:
        cmd.extend(["--display-name", args.display_name])
    if args.overwrite:
        cmd.append("--overwrite")
    if args.source_mode == "blank":
        cmd.append("--allow-empty-base")
    run(cmd)


def validate_generated(args: argparse.Namespace, skill_name: str) -> dict[str, object]:
    skill_dir = args.out_dir.resolve() / skill_name
    validate_cmd = [sys.executable, str(skill_dir / "scripts" / "validate_skill_package.py"), "--skill-dir", str(skill_dir)]
    startup_cmd = [sys.executable, str(skill_dir / "scripts" / "startup_check.py"), "--skill-dir", str(skill_dir)]
    run(validate_cmd)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    startup = subprocess.run(startup_cmd, check=True, capture_output=True, text=True, encoding="utf-8", env=env)
    return json.loads(startup.stdout)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a self-contained delta-contribution reframer skill from user inputs.")
    parser.add_argument("--config-file", type=Path, default=None, help="JSON build configuration. Long lists such as focus_domains and years should use this file route.")
    parser.add_argument("--skill-name", default=None)
    parser.add_argument("--display-name", default=None)
    parser.add_argument("--focus-domains", nargs="*", default=[], help="Focus domains used for corpus screening. Optional when --target-paper is provided.")
    parser.add_argument("--target-paper", type=Path, default=None, help="Target paper PDF used to infer 1-3 focus domains when --focus-domains is omitted.")
    parser.add_argument("--years", nargs="*", default=[])
    parser.add_argument("--source-mode", choices=["blank", "project-run", "local-pdf", "openreview-iclr"], default=None)
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--project-run-dir", type=Path, default=None)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--pdf", type=Path, default=None)
    parser.add_argument("--pdf-dir", type=Path, default=None)
    parser.add_argument("--reviews-dir", type=Path, default=None)
    parser.add_argument("--replies-dir", type=Path, default=None)
    parser.add_argument("--metadata-dir", type=Path, default=None)
    parser.add_argument("--cap", type=int, default=None)
    parser.add_argument("--review-pool-size", type=int, default=None, help="OpenReview mode: fetch reviews for this many domain candidates before final risk-aware cap selection.")
    parser.add_argument("--preselect-multiplier", type=int, default=None, help="OpenReview mode: review pool multiplier when --review-pool-size is not set.")
    parser.add_argument("--source-kind", default=None)
    parser.add_argument("--domain-scope", default=None)
    parser.add_argument("--build-home", type=Path, default=None)
    parser.add_argument("--clean-build", action="store_true", default=None)
    parser.add_argument("--overwrite", action="store_true", default=None)
    parser.add_argument("--llm-deep-read-mode", choices=["required", "optional", "off"], default=None)
    parser.add_argument("--llm-provider", choices=["openai-responses", "openai-chat", "command", "command-file", "jsonl", "off"], default=None)
    parser.add_argument("--llm-model", default=None)
    parser.add_argument("--llm-api-key-env", default=None)
    parser.add_argument("--llm-api-base", default=None)
    parser.add_argument("--llm-command", default=None, help="Command invoked once per prompt. For command, the request is sent on stdin. For command-file, request/response file paths are exposed through placeholders and LLM_* environment variables.")
    parser.add_argument("--llm-request-dir", type=Path, default=None, help="File exchange root for --llm-provider=command-file. Defaults to <run-dir>/analysis/llm_file_exchange.")
    parser.add_argument("--llm-file-poll-interval", type=float, default=None)
    parser.add_argument("--llm-results-jsonl", type=Path, default=None, help="Precomputed LLM deep-read JSONL keyed by paper_key when --llm-provider=jsonl.")
    parser.add_argument("--llm-chunk-chars", type=int, default=None)
    parser.add_argument("--llm-timeout", type=int, default=None)
    parser.add_argument("--reuse-llm", action="store_true", default=None, help="Reuse existing per-paper llm_deep_read_record.json artifacts when present.")
    args = parser.parse_args()
    args = apply_defaults(apply_config_file(args))
    validate_args(args)
    return args


def main() -> None:
    args = parse_args()
    skill_name = re_slug(args.skill_name)
    build_home = (args.build_home or default_build_home(skill_name)).resolve()
    if build_home.exists() and args.clean_build:
        shutil.rmtree(build_home)
    ensure_focus_domains(args, build_home)
    run_dir, source_kind = prepare_run(args, skill_name)
    if args.source_mode == "blank":
        state_dir = build_home / "state"
        refs_dir = build_home / "references"
        state_dir.mkdir(parents=True, exist_ok=True)
        refs_dir.mkdir(parents=True, exist_ok=True)
        (refs_dir / "anonymous_casebook.jsonl").write_text("", encoding="utf-8")
        (refs_dir / "per_pdf_report_synthesis.md").write_text("", encoding="utf-8")
        (refs_dir / "llm_deep_read_synthesis.md").write_text("", encoding="utf-8")
        (state_dir / "knowledge_state.json").write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "knowledge_available": False,
                    "source_kind": "not-initialized",
                    "domain_scope": args.domain_scope,
                    "focus_domains": args.focus_domains,
                    "years": args.years,
                    "paper_count": 0,
                    "llm_deep_read_required": True,
                    "llm_deep_read_complete": False,
                    "llm_deep_read_status": {},
                    "summary": {"anonymous_case_count": 0},
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    else:
        if args.llm_deep_read_mode == "required" and args.llm_provider == "off":
            raise SystemExit("--llm-provider=off is incompatible with --llm-deep-read-mode=required")
        if args.llm_provider == "command" and not args.llm_command:
            raise SystemExit("--llm-command is required when --llm-provider=command")
        if args.llm_provider == "jsonl" and not args.llm_results_jsonl:
            raise SystemExit("--llm-results-jsonl is required when --llm-provider=jsonl")
        synthesize(run_dir, build_home, args, source_kind)
    package(build_home, args, skill_name)
    startup = validate_generated(args, skill_name)
    print(json.dumps({"skill_name": skill_name, "run_dir": str(run_dir), "build_home": str(build_home), "startup": startup}, ensure_ascii=False, indent=2))


def re_slug(value: str) -> str:
    import re

    return re.sub(r"[^A-Za-z0-9]+", "-", value.lower()).strip("-") or "delta-reframer-domain"


if __name__ == "__main__":
    main()
