#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shlex
import subprocess
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

from common import clean, default_state_dir, read_json, write_json


DEFAULT_STATE_DIR = default_state_dir()


RISK_PATTERNS: dict[str, list[str]] = {
    "low_novelty_or_incremental": [
        r"\bincremental\b",
        r"limited novelty",
        r"lack of novelty",
        r"low novelty",
        r"minor extension",
        r"simple extension",
        r"straightforward extension",
    ],
    "abc_combination": [
        r"combination of existing",
        r"combines? existing",
        r"simple combination",
        r"\bcombine[sd]?\b",
        r"\bintegrat(e|es|ed|ing)\b",
        r"\bhybrid\b",
        r"\bunif(y|ies|ied)\b",
    ],
    "transfer_or_light_adaptation": [
        r"adapt(s|ed|ing)? .* to",
        r"extend(s|ed|ing)? .* to",
        r"based on",
        r"builds? on",
        r"variant of",
        r"transfer",
    ],
    "engineering_or_efficiency": [
        r"engineering",
        r"efficien(t|cy)",
        r"scalab(le|ility)",
        r"communication cost",
        r"computation cost",
        r"runtime",
        r"system",
        r"deployment",
    ],
    "evidence_or_benchmark": [
        r"benchmark",
        r"dataset",
        r"evaluation protocol",
        r"empirical study",
        r"ablation",
        r"stress test",
    ],
}


FAILURE_MODE_PATTERNS = [
    r"non[- ]iid",
    r"heterogeneity",
    r"client drift",
    r"label scarcity",
    r"few labeled",
    r"privacy",
    r"communication",
    r"scalability",
    r"distribution shift",
    r"domain shift",
    r"open[- ]set",
    r"partial label",
    r"pseudo[- ]label",
    r"confirmation bias",
    r"missing labels?",
    r"decentralized",
    r"federated",
]


REVIEW_ATTACK_PATTERNS: dict[str, list[str]] = {
    "novelty_incrementality": [r"novel", r"incremental", r"minor", r"contribution", r"significance"],
    "abc_or_mechanism": [r"combination", r"why", r"mechanism", r"necessary", r"motivation"],
    "baseline_fairness": [r"baseline", r"comparison", r"fair", r"state of the art", r"sota"],
    "ablation_evidence": [r"ablation", r"component", r"analysis", r"evidence"],
    "experiment_scope": [r"dataset", r"setting", r"scenario", r"limited", r"scale"],
    "cost_efficiency": [r"cost", r"efficien", r"communication", r"compute", r"runtime", r"memory"],
    "reproducibility": [r"code", r"reproduc", r"implementation", r"detail"],
}


WORKFLOW_COVERAGE = [
    "source_ledger",
    "evidence_boundary",
    "target_or_reference_regime",
    "broken_assumptions_or_failure_modes",
    "surface_delta_vs_stronger_delta",
    "claim_support_matrix",
    "ranked_story_option_board",
    "review_attack_analysis",
    "reply_move_analysis",
    "revision_or_rebuttal_reuse_priorities",
    "llm_full_paper_deep_read",
    "intermediate_artifacts",
]

LLM_DEEP_READ_ALIGNMENT = "llm-full-paper-deep-read"


def flatten(obj: Any) -> str:
    if isinstance(obj, dict) and "value" in obj:
        return flatten(obj["value"])
    if isinstance(obj, dict):
        return " ".join(flatten(v) for v in obj.values())
    if isinstance(obj, list):
        return " ".join(flatten(v) for v in obj)
    if obj is None:
        return ""
    return str(obj)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def extract_pdf_text(pdf_path: Path) -> tuple[str, str, str, list[dict[str, Any]]]:
    if not pdf_path.exists():
        return "missing_pdf", "", "paper.pdf not found", []
    try:
        import fitz  # type: ignore

        doc = fitz.open(pdf_path)
        page_rows: list[dict[str, Any]] = []
        chunks: list[str] = []
        for index, page in enumerate(doc):
            page_text = page.get_text("text") or ""
            chunks.append(page_text)
            page_rows.append({"page": index + 1, "text_chars": len(page_text), "start_char": sum(len(c) for c in chunks[:-1])})
        text = clean("\n\n".join(chunks))
        return ("ok" if text else "empty_text", text, "", page_rows)
    except Exception as fitz_exc:
        fitz_error = str(fitz_exc)
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(pdf_path))
        chunks = [(page.extract_text() or "") for page in reader.pages]
        page_rows = []
        offset = 0
        for index, page_text in enumerate(chunks):
            page_rows.append({"page": index + 1, "text_chars": len(page_text), "start_char": offset})
            offset += len(page_text)
        text = clean("\n\n".join(chunks))
        return ("ok" if text else "empty_text", text, "", page_rows)
    except Exception as pypdf_exc:
        return "pdf_text_extraction_failed", "", f"fitz: {fitz_error}; pypdf: {pypdf_exc}", []


def split_sentences(text: str, limit: int = 360) -> list[str]:
    raw = re.split(r"(?<=[.!?。！？])\s+", clean(text))
    out: list[str] = []
    for sent in raw:
        sent = clean(sent)
        if 20 <= len(sent) <= limit:
            out.append(sent)
    return out


def pattern_hits(text: str, patterns: list[str], max_hits: int = 8) -> list[str]:
    hits: list[str] = []
    for sent in split_sentences(text):
        if any(re.search(pattern, sent, flags=re.IGNORECASE) for pattern in patterns):
            hits.append(sent)
        if len(hits) >= max_hits:
            break
    return hits


def section_index(text: str) -> dict[str, Any]:
    lowered = text.lower()
    sections: dict[str, Any] = {}
    for label, patterns in {
        "abstract": [r"\babstract\b"],
        "introduction": [r"\b1\s+introduction\b", r"\bintroduction\b"],
        "related_work": [r"\brelated work\b", r"\bbackground\b"],
        "method": [r"\bmethod\b", r"\bapproach\b", r"\bframework\b", r"\balgorithm\b"],
        "experiments": [r"\bexperiment", r"\bevaluation\b"],
        "limitations": [r"\blimitation", r"\bdiscussion\b"],
    }.items():
        positions = [match.start() for pattern in patterns for match in [re.search(pattern, lowered)] if match]
        sections[label] = min(positions) if positions else None
    return {"text_chars": len(text), "section_offsets": sections}


def load_json_or_text(material_dir: Path, names: list[str]) -> tuple[str, list[Any]]:
    texts: list[str] = []
    json_items: list[Any] = []
    for name in names:
        path = material_dir / name
        if not path.exists():
            continue
        if path.suffix.lower() == ".json":
            data = read_json(path)
            if data:
                json_items.append(data)
                texts.append(flatten(data))
        else:
            texts.append(read_text(path))
    return clean("\n\n".join(texts)), json_items


def contribution_sentences(text: str) -> dict[str, list[str]]:
    return {
        "claimed_contributions": pattern_hits(
            text,
            [r"we propose", r"we introduce", r"we present", r"our contribution", r"we make", r"we develop"],
            max_hits=12,
        ),
        "borrowed_or_composed_components": pattern_hits(
            text,
            RISK_PATTERNS["abc_combination"] + RISK_PATTERNS["transfer_or_light_adaptation"],
            max_hits=12,
        ),
        "hidden_failure_modes": pattern_hits(text, FAILURE_MODE_PATTERNS, max_hits=12),
        "evidence_support": pattern_hits(text, RISK_PATTERNS["evidence_or_benchmark"], max_hits=12),
        "cost_or_system_constraints": pattern_hits(text, RISK_PATTERNS["engineering_or_efficiency"], max_hits=12),
    }


def classify_modes(text: str, review_text: str) -> dict[str, Any]:
    combined = clean(text[:25000] + "\n\n" + review_text)
    modes: dict[str, Any] = {}
    for name, patterns in RISK_PATTERNS.items():
        hits = pattern_hits(combined, patterns, max_hits=8)
        modes[name] = {"present": bool(hits), "evidence": hits}
    return modes


def classify_review_attacks(review_text: str) -> dict[str, list[str]]:
    attacks: dict[str, list[str]] = {}
    for name, patterns in REVIEW_ATTACK_PATTERNS.items():
        hits = pattern_hits(review_text, patterns, max_hits=8)
        if hits:
            attacks[name] = hits
    return attacks


def classify_reply_moves(reply_text: str) -> dict[str, list[str]]:
    return {
        "existing_evidence_resurfacing": pattern_hits(reply_text, [r"as shown", r"table", r"figure", r"appendix"], max_hits=8),
        "new_experiment_or_result": pattern_hits(reply_text, [r"we added", r"new experiment", r"additional experiment", r"additional result"], max_hits=8),
        "setting_boundary_defense": pattern_hits(reply_text, [r"scope", r"setting", r"focus", r"assumption", r"constraint"], max_hits=8),
        "claim_softening_or_clarification": pattern_hits(reply_text, [r"clarify", r"revise", r"make clear", r"emphasize"], max_hits=8),
    }


def safe_title(submission: dict[str, Any], paper_dir: Path) -> str:
    title = str(submission.get("title") or "").strip()
    return title or paper_dir.name


def target_regime_summary(source: dict[str, Any], contribution: dict[str, list[str]]) -> dict[str, Any]:
    constraints = contribution.get("hidden_failure_modes", [])[:8]
    return {
        "domain_or_area": source.get("primary_area") or "missing / not reported",
        "keywords": source.get("keywords") or [],
        "constraint_signals": constraints,
        "interpretation": "Use these constraint signals to move the contribution from component novelty toward regime-specific failure repair.",
    }


def evidence_boundary() -> dict[str, str]:
    return {
        "corpus-paper-derived": "PDF, submission metadata, public reviews, decision, and author replies when present.",
        "latent-but-supported": "Synthesis from constraints, claim structure, and review/reply patterns.",
        "simulated-review": "Required when public reviews are missing.",
        "base-corpus analogy": "Not used as fact evidence for this paper.",
    }


def surface_delta_summary(contribution: dict[str, list[str]]) -> dict[str, Any]:
    borrowed = contribution.get("borrowed_or_composed_components", [])[:8]
    return {
        "summary": "borrowed/adapted component or narrow empirical move" if borrowed else "missing / not explicit",
        "anchors": borrowed,
    }


def stronger_delta_summary(contribution: dict[str, list[str]]) -> dict[str, Any]:
    failures = contribution.get("hidden_failure_modes", [])[:8]
    return {
        "summary": "regime-specific failure repair" if failures else "narrow setting, mechanism interaction, and evidence-chain contribution",
        "failure_mode_anchors": failures,
        "claim_instruction": "Frame the contribution around why this constrained regime breaks an obvious reuse of prior components.",
    }


def story_option_board(modes: dict[str, Any], contribution: dict[str, list[str]], review_attacks: dict[str, list[str]]) -> list[dict[str, str]]:
    options: list[dict[str, str]] = []
    if modes.get("abc_combination", {}).get("present"):
        options.append({"rank": "1", "option": "Constraint-driven coupling", "use_when": "Known components are coupled to solve a setting-specific mismatch.", "risk": "Must explain why the coupling is necessary."})
    if modes.get("low_novelty_or_incremental", {}).get("present"):
        options.append({"rank": "2", "option": "Failure-mode elimination", "use_when": "Reviewers may call the method incremental.", "risk": "Needs module-to-failure ablations."})
    if modes.get("transfer_or_light_adaptation", {}).get("present"):
        options.append({"rank": "3", "option": "Bounded transfer", "use_when": "The work adapts an existing idea to a constrained regime.", "risk": "Must define source/target structural match."})
    if modes.get("engineering_or_efficiency", {}).get("present") or "cost_efficiency" in review_attacks:
        options.append({"rank": "4", "option": "Quality-cost tradeoff", "use_when": "The method improves robustness/accuracy with extra system cost.", "risk": "Needs runtime/communication accounting."})
    if modes.get("evidence_or_benchmark", {}).get("present") or contribution.get("hidden_failure_modes"):
        options.append({"rank": "5", "option": "Evidence-system contribution", "use_when": "The strongest value is evaluation under a hard regime.", "risk": "Should not replace a mechanism claim unless mechanism evidence is weak."})
    return options or [{"rank": "1", "option": "Scope-precise contribution", "use_when": "Explicit novelty signals are limited.", "risk": "Needs conservative claim boundaries."}]


def claim_support_matrix(contribution: dict[str, list[str]], review_attacks: dict[str, list[str]]) -> list[dict[str, str]]:
    claims = contribution.get("claimed_contributions", [])[:8] or ["missing / not explicit"]
    support = contribution.get("evidence_support", [])[:8]
    failures = contribution.get("hidden_failure_modes", [])[:8]
    matrix: list[dict[str, str]] = []
    for index, claim in enumerate(claims):
        matrix.append(
            {
                "claim": claim,
                "support": support[index % len(support)] if support else "missing / not explicit",
                "failure_mode_anchor": failures[index % len(failures)] if failures else "missing / not explicit",
                "risk": "novelty/baseline/ablation pressure" if review_attacks else "simulated-review required if no public reviews",
                "recommendation": "Tie this claim to a setting-specific failure mode and an explicit evidence item.",
            }
        )
    return matrix


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def chunk_text(text: str, max_chars: int) -> list[str]:
    text = text or ""
    if max_chars <= 0:
        max_chars = 55000
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        if end < len(text):
            boundary = max(text.rfind("\n\n", start, end), text.rfind(". ", start, end))
            if boundary > start + int(max_chars * 0.55):
                end = boundary + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end
    return chunks or [""]


def parse_json_loose(text: str) -> dict[str, Any]:
    text = clean(text)
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    try:
        payload = json.loads(text)
        return payload if isinstance(payload, dict) else {"value": payload}
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            payload = json.loads(match.group(0))
            return payload if isinstance(payload, dict) else {"value": payload}
        raise


def openai_response_text(payload: dict[str, Any]) -> str:
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]
    parts: list[str] = []
    for item in payload.get("output", []) or []:
        for content in item.get("content", []) or []:
            if isinstance(content.get("text"), str):
                parts.append(content["text"])
            elif isinstance(content.get("output_text"), str):
                parts.append(content["output_text"])
    for choice in payload.get("choices", []) or []:
        message = choice.get("message") or {}
        if isinstance(message.get("content"), str):
            parts.append(message["content"])
    return "\n".join(parts).strip()


def post_json(url: str, body: dict[str, Any], api_key: str, timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"LLM HTTP error {exc.code}: {detail[:1200]}") from exc


def safe_path_part(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-") or "item"


def call_file_llm(prompt: str, args: argparse.Namespace, paper_key: str, stage: str) -> dict[str, Any]:
    exchange_root = (args.llm_request_dir or (args.out_dir / "analysis" / "llm_file_exchange")).resolve()
    request_dir = exchange_root / safe_path_part(paper_key)
    request_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{safe_path_part(stage)}-{sha256_text(prompt)[:12]}"
    request_path = request_dir / f"{stem}.request.json"
    response_path = request_dir / f"{stem}.response.json"
    request = {
        "schema_version": "1.0",
        "provider": "command-file",
        "paper_key": paper_key,
        "stage": stage,
        "prompt_sha256": sha256_text(prompt),
        "prompt": prompt,
        "response_json": str(response_path),
        "instructions": "Read this request file and write one valid JSON object to response_json. Do not write Markdown fences.",
    }
    request_path.write_text(json.dumps(request, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.llm_command:
        if response_path.exists():
            response_path.unlink()
        rendered = args.llm_command.format(
            request_json=str(request_path),
            response_json=str(response_path),
            paper_key=paper_key,
            stage=stage,
        )
        env = os.environ.copy()
        env.update(
            {
                "LLM_REQUEST_JSON": str(request_path),
                "LLM_RESPONSE_JSON": str(response_path),
                "LLM_PAPER_KEY": paper_key,
                "LLM_STAGE": stage,
            }
        )
        proc = subprocess.run(
            shlex.split(rendered, posix=(os.name != "nt")),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=args.llm_timeout,
            check=False,
            env=env,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"LLM file command failed for {paper_key} stage={stage}: {proc.stderr[:1200]}")
        if response_path.exists():
            return parse_json_loose(response_path.read_text(encoding="utf-8"))
        if proc.stdout.strip():
            return parse_json_loose(proc.stdout)
        raise RuntimeError(f"LLM file command produced no response file: {response_path}")

    deadline = time.time() + args.llm_timeout
    while time.time() < deadline:
        if response_path.exists():
            return parse_json_loose(response_path.read_text(encoding="utf-8"))
        time.sleep(args.llm_file_poll_interval)
    raise RuntimeError(f"Timed out waiting for LLM response file: {response_path}")


def call_llm(prompt: str, args: argparse.Namespace, paper_key: str, stage: str) -> dict[str, Any]:
    if args.llm_provider in {"openai-responses", "openai-chat"}:
        api_key = os.environ.get(args.llm_api_key_env, "")
        if not api_key:
            raise RuntimeError(f"Missing API key environment variable: {args.llm_api_key_env}")
        base = args.llm_api_base.rstrip("/")
        if args.llm_provider == "openai-responses":
            payload = {
                "model": args.llm_model,
                "input": [
                    {"role": "system", "content": "Return one valid JSON object only. Do not use Markdown fences."},
                    {"role": "user", "content": prompt},
                ],
            }
            response = post_json(f"{base}/responses", payload, api_key, args.llm_timeout)
        else:
            payload = {
                "model": args.llm_model,
                "messages": [
                    {"role": "system", "content": "Return one valid JSON object only. Do not use Markdown fences."},
                    {"role": "user", "content": prompt},
                ],
                "response_format": {"type": "json_object"},
            }
            response = post_json(f"{base}/chat/completions", payload, api_key, args.llm_timeout)
        text = openai_response_text(response)
        if not text:
            raise RuntimeError(f"LLM returned no text for {paper_key} stage={stage}")
        return parse_json_loose(text)

    if args.llm_provider == "command":
        if not args.llm_command:
            raise RuntimeError("--llm-command is required for provider=command")
        request = {"paper_key": paper_key, "stage": stage, "prompt": prompt}
        proc = subprocess.run(
            shlex.split(args.llm_command),
            input=json.dumps(request, ensure_ascii=False),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=args.llm_timeout,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"LLM command failed for {paper_key} stage={stage}: {proc.stderr[:1200]}")
        return parse_json_loose(proc.stdout)

    if args.llm_provider == "command-file":
        return call_file_llm(prompt, args, paper_key, stage)

    raise RuntimeError(f"Unsupported LLM provider for live calls: {args.llm_provider}")


def build_chunk_prompt(source: dict[str, Any], chunk: str, chunk_index: int, total_chunks: int) -> str:
    return "\n".join(
        [
            "You are deep-reading one chunk of a research paper for a delta-contribution reframer factory.",
            "Read the supplied text carefully and return JSON only.",
            "",
            "Required JSON keys:",
            "- schema_version: string",
            "- paper_key: string",
            "- chunk_index: integer",
            "- total_chunks: integer",
            "- source_grounding: list of evidence anchors with locator, quote_or_paraphrase, confidence",
            "- scientific_problem: list",
            "- method_mechanics: list",
            "- formulas_algorithms_assumptions: list",
            "- figure_table_experiment_notes: list",
            "- claims_and_support: list",
            "- limitations_and_reproducibility_gaps: list",
            "- novelty_incrementality_signals: list",
            "- reviewer_risk_signals: list",
            "- delta_reframing_notes: list",
            "- uncertainty_notes: list",
            "",
            "Rules:",
            "- Mark missing or unclear information as not reported.",
            "- Distinguish paper-stated facts from inference.",
            "- Do not invent citations, numbers, baselines, formulas, or reviewer reactions.",
            "",
            f"Paper key: {source.get('paper_key')}",
            f"Title: {source.get('title')}",
            f"Venue/year: {source.get('venue')} / {source.get('year')}",
            f"Chunk: {chunk_index} of {total_chunks}",
            "",
            "PDF chunk text:",
            chunk,
        ]
    )


def build_synthesis_prompt(
    source: dict[str, Any],
    chunk_results: list[dict[str, Any]],
    review_text: str,
    reply_text: str,
    rule_record: dict[str, Any],
) -> str:
    compact_rule = {
        "source_ledger": rule_record.get("source_ledger"),
        "surface_delta": rule_record.get("surface_delta"),
        "stronger_delta": rule_record.get("stronger_delta"),
        "claim_support_matrix": rule_record.get("claim_support_matrix"),
        "story_option_board": rule_record.get("story_option_board"),
        "review_attack_analysis": rule_record.get("review_attack_analysis"),
        "reply_move_analysis": rule_record.get("reply_move_analysis"),
    }
    return "\n".join(
        [
            "You are synthesizing full-paper chunk readings into one authoritative deep-read record for a delta-contribution reframer factory.",
            "Return JSON only. The JSON must be source-grounded and suitable for downstream anonymous synthesis.",
            "",
            "Required JSON keys:",
            "- schema_version",
            "- workflow_alignment: must be llm-full-paper-deep-read",
            "- reading_status: complete",
            "- paper_key",
            "- source_grounding_summary",
            "- authoritative_report_markdown",
            "- paper_identity",
            "- scientific_problem_and_positioning",
            "- method_deep_read",
            "- formulas_algorithms_and_assumptions",
            "- figure_table_and_experiment_analysis",
            "- claim_support_matrix: list of objects with claim, support, failure_mode_anchor, risk, recommendation",
            "- delta_reframing: object with surface_delta and stronger_delta",
            "- story_option_board: list of objects with rank, option, use_when, risk",
            "- reviewer_attack_preplay",
            "- review_reply_coverage",
            "- reproducibility_gaps",
            "- limitations_and_scope_boundaries",
            "- no_new_experiment_reuse_priorities",
            "- reusable_anonymous_patterns",
            "- uncertainty_notes",
            "",
            "Report requirements:",
            "- Include source ledger, evidence boundary, scientific problem, method, formulas, experiments, figures/tables if visible, claim-support, novelty/incrementality, reviewer risks, rebuttal-safe boundaries, and reusable delta-story routes.",
            "- Keep the report factual. Mark anything missing as not reported.",
            "- Do not include author names, forum IDs, URLs, or uniquely identifying reusable examples in reusable_anonymous_patterns.",
            "",
            f"Paper key: {source.get('paper_key')}",
            f"Title: {source.get('title')}",
            f"Venue/year: {source.get('venue')} / {source.get('year')}",
            "",
            "Rule pre-pass record:",
            json.dumps(compact_rule, ensure_ascii=False),
            "",
            "Public review text, if available:",
            review_text[:30000] or "not available",
            "",
            "Author reply text, if available:",
            reply_text[:30000] or "not available",
            "",
            "Chunk reading JSON results:",
            json.dumps(chunk_results, ensure_ascii=False),
        ]
    )


def normalize_llm_claim_rows(rows: Any, fallback: list[dict[str, str]]) -> list[dict[str, str]]:
    if not isinstance(rows, list):
        return fallback
    normalized: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        normalized.append(
            {
                "claim": clean(flatten(row.get("claim") or row.get("paper_claim") or "")) or "missing / not explicit",
                "support": clean(flatten(row.get("support") or row.get("evidence") or "")) or "missing / not explicit",
                "failure_mode_anchor": clean(flatten(row.get("failure_mode_anchor") or row.get("failure_mode") or "")) or "missing / not explicit",
                "risk": clean(flatten(row.get("risk") or row.get("reviewer_risk") or "")) or "reviewer risk not specified",
                "recommendation": clean(flatten(row.get("recommendation") or row.get("repair") or "")) or "Tie claim to evidence and boundary.",
            }
        )
    return normalized or fallback


def normalize_llm_story_options(options: Any, fallback: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(options, list):
        return fallback
    normalized: list[dict[str, Any]] = []
    for idx, option in enumerate(options, 1):
        if not isinstance(option, dict):
            continue
        normalized.append(
            {
                "rank": option.get("rank") or idx,
                "option": clean(flatten(option.get("option") or option.get("story_option") or "")) or "delta reframing route",
                "use_when": clean(flatten(option.get("use_when") or option.get("condition") or "")) or "when evidence supports this route",
                "risk": clean(flatten(option.get("risk") or option.get("boundary") or "")) or "avoid overclaiming beyond evidence",
            }
        )
    return normalized or fallback


def write_llm_artifacts(paper_report_dir: Path, result: dict[str, Any], chunk_results: list[dict[str, Any]], prompt_manifest: str) -> dict[str, Any]:
    report = clean(flatten(result.get("authoritative_report_markdown") or ""))
    if not report:
        report = "# LLM Deep-Read Report\n\nThe LLM result did not include an authoritative_report_markdown field.\n"
    (paper_report_dir / "llm_deep_read_report.md").write_text(report.rstrip() + "\n", encoding="utf-8")
    write_json(paper_report_dir / "llm_deep_read_record.json", result)
    with (paper_report_dir / "llm_chunk_results.jsonl").open("w", encoding="utf-8") as handle:
        for chunk in chunk_results:
            handle.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    (paper_report_dir / "llm_deep_read_prompt.md").write_text(prompt_manifest.rstrip() + "\n", encoding="utf-8")
    status = {
        "status": "complete",
        "workflow_alignment": LLM_DEEP_READ_ALIGNMENT,
        "report": "llm_deep_read_report.md",
        "record": "llm_deep_read_record.json",
        "chunk_result_count": len(chunk_results),
        "prompt_sha256": sha256_text(prompt_manifest),
        "updated_at": dt.datetime.now().isoformat(timespec="seconds"),
    }
    write_json(paper_report_dir / "llm_deep_read_status.json", status)
    return status


def load_llm_results(path: Path | None) -> dict[str, dict[str, Any]]:
    if not path:
        return {}
    results: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            key = str(payload.get("paper_key") or payload.get("paper_id") or "")
            if key:
                results[key] = payload
    return results


def run_llm_deep_read(
    paper_report_dir: Path,
    source: dict[str, Any],
    pdf_text: str,
    review_text: str,
    reply_text: str,
    rule_record: dict[str, Any],
    args: argparse.Namespace,
    imported_results: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    paper_key = str(source.get("paper_key") or rule_record.get("paper_key") or paper_report_dir.name)
    existing_record = paper_report_dir / "llm_deep_read_record.json"
    existing_status = paper_report_dir / "llm_deep_read_status.json"
    if args.reuse_llm and existing_record.exists() and existing_status.exists():
        result = read_json(existing_record)
        return read_json(existing_status), result
    if args.llm_deep_read_mode == "off" or args.llm_provider == "off":
        return {"status": "not_run", "workflow_alignment": None, "reason": "llm deep reading disabled"}, None
    try:
        if args.llm_provider == "jsonl":
            if paper_key not in imported_results:
                raise RuntimeError(f"No imported LLM deep-read result for paper_key={paper_key}")
            result = imported_results[paper_key]
            chunks = result.get("chunk_results") if isinstance(result.get("chunk_results"), list) else []
            status = write_llm_artifacts(
                paper_report_dir,
                result,
                chunks,
                f"Imported from JSONL for {paper_key}; source text was not stored in this prompt manifest.",
            )
            return status, result

        if not pdf_text.strip():
            raise RuntimeError(f"No extracted PDF text available for LLM deep reading: {paper_key}")
        chunks = chunk_text(pdf_text, args.llm_chunk_chars)
        chunk_results: list[dict[str, Any]] = []
        prompt_summaries: list[str] = []
        for index, chunk in enumerate(chunks, 1):
            prompt = build_chunk_prompt(source, chunk, index, len(chunks))
            prompt_summaries.append(f"## Chunk {index}/{len(chunks)}\n\nPrompt sha256: `{sha256_text(prompt)}`\n\n{prompt[:4000]}\n")
            chunk_result = call_llm(prompt, args, paper_key, f"chunk-{index}")
            chunk_result.setdefault("paper_key", paper_key)
            chunk_result.setdefault("chunk_index", index)
            chunk_result.setdefault("total_chunks", len(chunks))
            chunk_results.append(chunk_result)
            time.sleep(0.1)
        synthesis_prompt = build_synthesis_prompt(source, chunk_results, review_text, reply_text, rule_record)
        prompt_summaries.append(f"## Synthesis\n\nPrompt sha256: `{sha256_text(synthesis_prompt)}`\n\n{synthesis_prompt[:6000]}\n")
        result = call_llm(synthesis_prompt, args, paper_key, "synthesis")
        result.setdefault("paper_key", paper_key)
        result.setdefault("workflow_alignment", LLM_DEEP_READ_ALIGNMENT)
        result.setdefault("reading_status", "complete")
        status = write_llm_artifacts(paper_report_dir, result, chunk_results, "\n\n".join(prompt_summaries))
        return status, result
    except Exception as exc:  # noqa: BLE001
        status = {
            "status": "failed",
            "workflow_alignment": LLM_DEEP_READ_ALIGNMENT,
            "error": str(exc),
            "updated_at": dt.datetime.now().isoformat(timespec="seconds"),
        }
        write_json(paper_report_dir / "llm_deep_read_status.json", status)
        if args.llm_deep_read_mode == "required":
            raise
        return status, None


def write_per_paper_report(report_path: Path, record: dict[str, Any]) -> None:
    source = record["source_ledger"]
    modes = record["incremental_mode_analysis"]
    contribution = record["claim_delta_matrix"]
    review_attacks = record["review_attack_analysis"]
    reply_moves = record["reply_move_analysis"]
    regime = record["target_regime_summary"]
    boundary = record["evidence_boundary"]
    surface_delta = record["surface_delta"]
    stronger_delta = record["stronger_delta"]

    lines = [
        "# Per-Paper Delta-Contribution Reframing Analysis",
        "",
        "## 0. Source Ledger",
        "",
        f"- Paper key: `{record['paper_key']}`",
        f"- Title: {source.get('title')}",
        f"- Venue/year: {source.get('venue')} / {source.get('year')}",
        f"- Primary area: {source.get('primary_area')}",
        f"- Keywords: {source.get('keywords')}",
        f"- Material dir: `{source.get('material_dir')}`",
        f"- Analysis status: `{record['analysis_status']}`",
        f"- PDF status: `{record['pdf_status']}`",
        f"- PDF text chars: {record['pdf_text_chars']}",
        f"- Review status: `{record['review_status']}`",
        f"- Reply status: `{record['reply_status']}`",
        f"- Review attack mode: `{record['review_attack_mode']}`",
        f"- LLM deep-read status: `{(record.get('llm_deep_reading') or {}).get('status', 'not_run')}`",
        f"- Deep-read workflow: `{record.get('deep_read_workflow_alignment', 'missing')}`",
        "",
        "## 1. Evidence Boundary",
        "",
        f"- `corpus-paper-derived`: {boundary['corpus-paper-derived']}",
        f"- `latent-but-supported`: {boundary['latent-but-supported']}",
        f"- `simulated-review`: {boundary['simulated-review']}",
        f"- `base-corpus analogy`: {boundary['base-corpus analogy']}",
        "",
        "## 2. Reference Regime And Broken Assumptions",
        "",
        f"- Domain/area: {regime.get('domain_or_area')}",
        f"- Keywords: {regime.get('keywords')}",
        f"- Interpretation: {regime.get('interpretation')}",
        "",
        "### Constraint Signals",
        "",
    ]
    lines.extend(f"- {hit}" for hit in regime.get("constraint_signals", [])) if regime.get("constraint_signals") else lines.append("- missing / not explicit")

    lines.extend(["", "## 3. Surface Delta Vs Stronger Delta", "", "### Surface Delta", ""])
    lines.append(f"- Summary: {surface_delta.get('summary')}")
    lines.extend(f"- {hit}" for hit in surface_delta.get("anchors", [])[:8]) if surface_delta.get("anchors") else lines.append("- missing / not explicit")
    lines.extend(["", "### Stronger Delta Candidate", ""])
    hidden = stronger_delta.get("failure_mode_anchors", [])
    if hidden:
        lines.append(f"- Summary: {stronger_delta.get('summary')}")
        lines.append(f"- Claim instruction: {stronger_delta.get('claim_instruction')}")
        lines.extend(f"- {hit}" for hit in hidden[:8])
    else:
        lines.append(f"- Summary: {stronger_delta.get('summary')}")
        lines.append(f"- Claim instruction: {stronger_delta.get('claim_instruction')}")

    lines.extend(["", "## 4. Incremental Risk And Packaging Entry Points", ""])
    for mode, payload in modes.items():
        lines.extend([f"### {mode}", ""])
        lines.extend(f"- {hit}" for hit in payload.get("evidence", [])[:6]) if payload.get("present") else lines.append("- missing / not explicit")
        lines.append("")

    lines.extend(["## 5. Claim-Support Matrix", "", "| Claim | Support | Failure-mode anchor | Risk | Recommendation |", "|---|---|---|---|---|"])
    for row in record["claim_support_matrix"]:
        lines.append(f"| {row['claim']} | {row['support']} | {row['failure_mode_anchor']} | {row['risk']} | {row['recommendation']} |")
    lines.append("")

    lines.extend(["## 6. Ranked Story Option Board", "", "| Rank | Story option | Use when | Risk |", "|---:|---|---|---|"])
    for option in record["story_option_board"]:
        lines.append(f"| {option['rank']} | {option['option']} | {option['use_when']} | {option['risk']} |")
    lines.append("")

    lines.extend(["## 7. Review Attack Analysis", ""])
    if review_attacks:
        for attack, hits in review_attacks.items():
            lines.extend([f"### {attack}", ""])
            lines.extend(f"- {hit}" for hit in hits[:6])
            lines.append("")
    else:
        lines.extend(["- Public review text is missing. Any attack inferred from this paper must be labeled `simulated-review`.", ""])

    lines.extend(["## 8. Reply Move Analysis", ""])
    if any(reply_moves.values()):
        for move, hits in reply_moves.items():
            if not hits:
                continue
            lines.extend([f"### {move}", ""])
            lines.extend(f"- {hit}" for hit in hits[:6])
            lines.append("")
    else:
        lines.extend(["- Public author replies are missing or no reusable reply move was detected.", ""])

    lines.extend(
        [
            "## 9. LLM Full-Paper Deep Read",
            "",
        ]
    )
    llm_status = record.get("llm_deep_reading") or {}
    if llm_status.get("status") == "complete":
        lines.extend(
            [
                f"- Status: `{llm_status.get('status')}`",
                f"- Workflow alignment: `{llm_status.get('workflow_alignment')}`",
                f"- Chunk results: {llm_status.get('chunk_result_count')}",
                f"- Report: `llm_deep_read_report.md`",
                f"- Machine record: `llm_deep_read_record.json`",
                "",
                "The LLM report is the authoritative full-paper reading artifact. The sections above merge it with the delta-contribution rule pre-pass.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                f"- Status: `{llm_status.get('status', 'not_run')}`",
                f"- Error/reason: {llm_status.get('error') or llm_status.get('reason') or 'not available'}",
                "- This report is not acceptable for initialized corpus packaging unless the LLM status is `complete`.",
                "",
            ]
        )

    lines.extend(
        [
            "## 10. Revision Or Rebuttal Reuse Priorities",
            "",
            "- Tier 0: Define the narrow regime and avoid overclaiming primitive novelty.",
            "- Tier 0: If components are borrowed or adapted, state the coupling/failure-mode contribution explicitly.",
            "- Tier 1: Build a claim-support matrix tying each module to evidence, ablation, or review defense.",
            "- Tier 1: If cost, baseline, or scope attacks appear, add a comparison contract before arguing results.",
            "- Tier 2: Add targeted ablations or diagnostics only where the claim cannot be supported by existing evidence.",
            "",
            "## 11. Workflow Coverage",
            "",
        ]
    )
    lines.extend(f"- `{item}`" for item in record["workflow_coverage"])
    lines.extend(
        [
            "",
            "## 12. Intermediate Artifacts",
            "",
            "- `pdf_text.txt`: PDF text extraction result when available.",
            "- `page_index.json`: page-level text coverage metadata.",
            "- `source_ledger.json`: submission/metadata ledger.",
            "- `paper_sections.json`: heuristic section offsets.",
            "- `review_reply_ledger.json`: review/reply availability and raw text summary.",
            "- `claim_delta_matrix.json`: claim, borrowed-component, and failure-mode evidence.",
            "- `llm_deep_read_report.md`: authoritative full-paper LLM deep-read report.",
            "- `llm_deep_read_record.json`: machine-readable LLM deep-read record.",
            "- `llm_chunk_results.jsonl`: ordered chunk-level LLM readings.",
            "- `llm_deep_read_status.json`: status and audit metadata for the LLM pass.",
            "- `analysis_record.json`: machine-readable full record.",
            "",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def analyze_one(
    material_dir: Path,
    reports_root: Path,
    out_dir: Path,
    args: argparse.Namespace,
    imported_llm_results: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    submission = read_json(material_dir / "submission.json")
    pdf_status, pdf_text, pdf_error, page_rows = extract_pdf_text(material_dir / "paper.pdf")
    review_text, review_json = load_json_or_text(material_dir, ["official_reviews.json", "official_reviews.md", "meta_review.json", "meta_review.md", "decision.json", "decision.md"])
    reply_text, reply_json = load_json_or_text(material_dir, ["author_replies.json", "author_replies.md", "reviewer_followups.json", "reviewer_followups.md", "public_comments.json"])
    paper_text = pdf_text or clean(" ".join([str(submission.get("title") or ""), str(submission.get("abstract") or "")]))
    paper_key = material_dir.name
    paper_report_dir = reports_root / paper_key
    paper_report_dir.mkdir(parents=True, exist_ok=True)

    source_ledger = {
        "paper_key": paper_key,
        "title": safe_title(submission, material_dir),
        "year": submission.get("year"),
        "venue": submission.get("venue"),
        "primary_area": submission.get("primary_area"),
        "keywords": submission.get("keywords"),
        "material_dir": material_dir.relative_to(out_dir).as_posix() if material_dir.is_relative_to(out_dir) else material_dir.as_posix(),
        "pdf_present": (material_dir / "paper.pdf").exists(),
        "reviews_present": bool(review_text),
        "replies_present": bool(reply_text),
    }
    claim_delta = contribution_sentences(paper_text)
    modes = classify_modes(paper_text, review_text)
    review_attacks = classify_review_attacks(review_text)
    reply_moves = classify_reply_moves(reply_text)
    record = {
        "schema_version": "2.0",
        "workflow_alignment": "delta-contribution-reframer",
        "workflow_coverage": WORKFLOW_COVERAGE,
        "paper_id": paper_key,
        "paper_key": paper_key,
        "analysis_status": "complete" if pdf_status == "ok" else "partial",
        "pdf_status": pdf_status,
        "pdf_error": pdf_error,
        "pdf_text_chars": len(pdf_text),
        "review_status": "available" if review_text else "missing",
        "reply_status": "available" if reply_text else "missing",
        "review_attack_mode": "real-review" if review_text else "simulated-review",
        "source_ledger": source_ledger,
        "evidence_boundary": evidence_boundary(),
        "paper_sections": section_index(paper_text),
        "target_regime_summary": target_regime_summary(source_ledger, claim_delta),
        "broken_assumptions_or_failure_modes": claim_delta.get("hidden_failure_modes", [])[:12],
        "surface_delta": surface_delta_summary(claim_delta),
        "stronger_delta": stronger_delta_summary(claim_delta),
        "incremental_mode_analysis": modes,
        "claim_delta_matrix": claim_delta,
        "claim_support_matrix": claim_support_matrix(claim_delta, review_attacks),
        "story_option_board": story_option_board(modes, claim_delta, review_attacks),
        "review_attack_analysis": review_attacks,
        "reply_move_analysis": reply_moves,
        "review_reply_ledger": {
            "review_json_items": len(review_json),
            "reply_json_items": len(reply_json),
            "review_text_chars": len(review_text),
            "reply_text_chars": len(reply_text),
        },
    }

    llm_status, llm_result = run_llm_deep_read(
        paper_report_dir,
        source_ledger,
        pdf_text,
        review_text,
        reply_text,
        record,
        args,
        imported_llm_results,
    )
    record["analysis_method"] = "llm_deep_read_plus_delta_rule_prepass" if llm_status.get("status") == "complete" else "delta_rule_prepass_only"
    record["deep_read_workflow_alignment"] = LLM_DEEP_READ_ALIGNMENT if llm_status.get("status") == "complete" else None
    record["llm_deep_reading"] = llm_status
    record["llm_deep_read_record"] = "llm_deep_read_record.json" if llm_result else None
    if llm_result:
        record["llm_deep_read_summary"] = {
            "source_grounding_summary": llm_result.get("source_grounding_summary"),
            "scientific_problem_and_positioning": llm_result.get("scientific_problem_and_positioning"),
            "reproducibility_gaps": llm_result.get("reproducibility_gaps"),
            "limitations_and_scope_boundaries": llm_result.get("limitations_and_scope_boundaries"),
        }
        record["claim_support_matrix"] = normalize_llm_claim_rows(llm_result.get("claim_support_matrix"), record["claim_support_matrix"])
        record["story_option_board"] = normalize_llm_story_options(llm_result.get("story_option_board"), record["story_option_board"])
        delta = llm_result.get("delta_reframing") if isinstance(llm_result.get("delta_reframing"), dict) else {}
        if isinstance(delta.get("surface_delta"), dict):
            record["surface_delta"] = delta["surface_delta"]
        if isinstance(delta.get("stronger_delta"), dict):
            record["stronger_delta"] = delta["stronger_delta"]

    (paper_report_dir / "pdf_text.txt").write_text(pdf_text, encoding="utf-8", errors="replace")
    write_json(paper_report_dir / "page_index.json", {"pdf_status": pdf_status, "pages": page_rows})
    write_json(paper_report_dir / "source_ledger.json", source_ledger)
    write_json(paper_report_dir / "paper_sections.json", record["paper_sections"])
    write_json(paper_report_dir / "review_reply_ledger.json", record["review_reply_ledger"])
    write_json(paper_report_dir / "claim_delta_matrix.json", claim_delta)
    write_json(paper_report_dir / "analysis_record.json", record)
    write_per_paper_report(paper_report_dir / "analysis.md", record)
    record["analysis_report"] = (paper_report_dir / "analysis.md").relative_to(out_dir).as_posix() if paper_report_dir.is_relative_to(out_dir) else (paper_report_dir / "analysis.md").as_posix()
    return record


def index_link_target(index_path: Path, out_dir: Path, report: str) -> str:
    report_path = Path(report)
    if not report_path.is_absolute():
        report_path = out_dir / report_path
    try:
        return Path(os.path.relpath(report_path, start=index_path.parent)).as_posix()
    except ValueError:
        return report_path.as_posix()


def write_index(out_dir: Path, records: list[dict[str, Any]]) -> None:
    index_path = out_dir / "reports" / "per_paper_analysis_index.md"
    lines = [
        "# Per-Paper Analysis Index",
        "",
        "Every extracted paper material directory has a delta-contribution-reframer-aligned analysis report. Real corpus builds also require a complete full-paper LLM deep-read for every selected PDF. Missing or unreadable PDFs are recorded as partial analyses rather than silently skipped.",
        "",
        "| Paper key | Status | PDF | LLM deep read | Reviews | Replies | Workflow | Report |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for record in records:
        report = record.get("analysis_report", "")
        report_link = index_link_target(index_path, out_dir, report)
        if report_link and not (index_path.parent / Path(report_link)).resolve().exists():
            raise RuntimeError(f"Generated report link does not resolve from index: {report_link}")
        llm_status = (record.get("llm_deep_reading") or {}).get("status", "not_run")
        lines.append(f"| `{record['paper_key']}` | {record['analysis_status']} | {record['pdf_status']} | {llm_status} | {record['review_status']} | {record['reply_status']} | {record.get('workflow_alignment', '')} | [{Path(report).name}]({report_link}) |")
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("\n".join(lines), encoding="utf-8")

    manifest_path = out_dir / "analysis" / "per_paper_analysis_manifest.jsonl"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as handle:
        for record in records:
            line = json.dumps(record, ensure_ascii=False).replace(chr(0x2028), "\\u2028").replace(chr(0x2029), "\\u2029")
            handle.write(line + "\n")


def update_states(state_dir: Path, out_dir: Path, records: list[dict[str, Any]]) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    counter = Counter(record["analysis_status"] for record in records)
    pdf_counter = Counter(record["pdf_status"] for record in records)
    llm_counter = Counter((record.get("llm_deep_reading") or {}).get("status", "not_run") for record in records)
    aligned = all(record.get("workflow_alignment") == "delta-contribution-reframer" for record in records)
    llm_aligned = all(record.get("deep_read_workflow_alignment") == LLM_DEEP_READ_ALIGNMENT for record in records)
    all_llm_complete = bool(records) and llm_counter.get("complete", 0) == len(records)
    state = {
        "schema_version": "2.0",
        "workflow_alignment": "delta-contribution-reframer",
        "deep_read_workflow_alignment": LLM_DEEP_READ_ALIGNMENT,
        "updated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "paper_count": len(records),
        "report_coverage_complete": bool(records),
        "all_reports_workflow_aligned": aligned,
        "all_llm_deep_reads_workflow_aligned": llm_aligned,
        "all_llm_deep_reads_complete": all_llm_complete,
        "all_pdfs_text_extracted": bool(records) and counter.get("partial", 0) == 0,
        "complete_count": counter.get("complete", 0),
        "partial_count": counter.get("partial", 0),
        "pdf_status_counts": dict(pdf_counter),
        "llm_deep_read_status_counts": dict(llm_counter),
        "manifest": (out_dir / "analysis" / "per_paper_analysis_manifest.jsonl").as_posix(),
        "index": (out_dir / "reports" / "per_paper_analysis_index.md").as_posix(),
        "required_workflow_coverage": WORKFLOW_COVERAGE,
    }
    write_json(state_dir / "per_paper_analysis_state.json", state)

    knowledge_path = state_dir / "knowledge_state.json"
    knowledge = read_json(knowledge_path)
    if knowledge:
        resources = list(knowledge.get("resources") or [])
        resources.extend(
            [
                {"path": state["manifest"], "kind": "per_paper_analysis_manifest", "status": "available" if records else "empty", "workflow_alignment": "delta-contribution-reframer"},
                {"path": state["index"], "kind": "per_paper_analysis_index", "status": "available" if records else "empty", "workflow_alignment": "delta-contribution-reframer"},
            ]
        )
        knowledge["resources"] = resources
        knowledge["per_paper_analysis"] = state
        write_json(knowledge_path, knowledge)

    init_path = state_dir / "initialization_state.json"
    init_state = read_json(init_path)
    if init_state:
        init_state["per_paper_report_coverage_complete"] = bool(records)
        init_state["all_reports_workflow_aligned"] = aligned
        init_state["all_llm_deep_reads_complete"] = all_llm_complete
        init_state["all_pdfs_text_extracted"] = bool(records) and counter.get("partial", 0) == 0
        init_state["per_paper_analysis_complete"] = bool(records)
        init_state["per_paper_analysis_state"] = state
        write_json(init_path, init_state)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze every extracted paper material folder with delta-contribution-reframer-aligned reports.")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, default=DEFAULT_STATE_DIR)
    parser.add_argument("--llm-deep-read-mode", choices=["required", "optional", "off"], default="required")
    parser.add_argument("--llm-provider", choices=["openai-responses", "openai-chat", "command", "command-file", "jsonl", "off"], default="openai-responses")
    parser.add_argument("--llm-model", default=os.environ.get("OPENAI_MODEL", "gpt-5.2"))
    parser.add_argument("--llm-api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--llm-api-base", default=os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1"))
    parser.add_argument("--llm-command", default=None)
    parser.add_argument("--llm-request-dir", type=Path, default=None, help="File exchange root for --llm-provider=command-file. Defaults to <out-dir>/analysis/llm_file_exchange.")
    parser.add_argument("--llm-file-poll-interval", type=float, default=2.0)
    parser.add_argument("--llm-results-jsonl", type=Path, default=None)
    parser.add_argument("--llm-chunk-chars", type=int, default=55000)
    parser.add_argument("--llm-timeout", type=int, default=240)
    parser.add_argument("--reuse-llm", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir.resolve()
    materials_root = out_dir / "materials" / "_by_paper"
    if not materials_root.exists():
        raise SystemExit(f"materials folder not found: {materials_root}")
    if args.llm_deep_read_mode == "required":
        if args.llm_provider == "off":
            raise SystemExit("--llm-provider=off is not allowed when --llm-deep-read-mode=required")
        if args.llm_provider == "command" and not args.llm_command:
            raise SystemExit("--llm-command is required when --llm-provider=command")
        if args.llm_provider == "jsonl" and not args.llm_results_jsonl:
            raise SystemExit("--llm-results-jsonl is required when --llm-provider=jsonl")

    reports_root = out_dir / "analysis" / "per_paper"
    imported_llm_results = load_llm_results(args.llm_results_jsonl.resolve() if args.llm_results_jsonl else None)
    records = [
        analyze_one(material_dir, reports_root, out_dir, args, imported_llm_results)
        for material_dir in sorted(path for path in materials_root.iterdir() if path.is_dir())
    ]
    if args.llm_deep_read_mode == "required":
        incomplete = [record["paper_key"] for record in records if (record.get("llm_deep_reading") or {}).get("status") != "complete"]
        if incomplete:
            preview = ", ".join(incomplete[:10])
            extra = f" ... {len(incomplete) - 10} more" if len(incomplete) > 10 else ""
            raise SystemExit(f"LLM deep reading is required but incomplete for: {preview}{extra}")
    write_index(out_dir, records)
    update_states(args.state_dir.resolve(), out_dir, records)
    print(
        json.dumps(
            {
                "analyzed_papers": len(records),
                "workflow_alignment": "delta-contribution-reframer",
                "deep_read_workflow_alignment": LLM_DEEP_READ_ALIGNMENT,
                "llm_deep_read_complete": sum(1 for record in records if (record.get("llm_deep_reading") or {}).get("status") == "complete"),
                "out_dir": str(out_dir),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
