#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import openreview
import requests


API1_BASE = "https://api.openreview.net"
API2_BASE = "https://api2.openreview.net"
OPENREVIEW_BASE = "https://openreview.net"


DOMAIN_ALIASES = {
    "federated": [
        r"\bfederated\b",
        r"\bfederated learning\b",
        r"\bclient drift\b",
        r"\bnon[- ]iid\b",
        r"\bdata heterogeneity\b",
        r"\bcross[- ]device\b",
        r"\bcross[- ]silo\b",
    ],
    "semi-supervised": [
        r"\bsemi[- ]supervised\b",
        r"\bpseudo[- ]labels?\b",
        r"\bunlabeled data\b",
        r"\blabel[- ]scar",
        r"\bself[- ]training\b",
        r"\bconsistency regularization\b",
    ],
}

RISK_PATTERNS = {
    "low_novelty_or_incremental": [r"\bincremental\b", r"\blimited novelty\b", r"\bminor extension\b", r"\bsimple extension\b"],
    "abc_combination": [r"\bcombination\b", r"\bcombines?\b", r"\bintegrat(?:e|es|ed|ing)\b", r"\bhybrid\b"],
    "transfer_or_light_adaptation": [r"\badapt", r"\bextend", r"\btransfer", r"\bbased on\b", r"\bvariant of\b"],
    "engineering_or_efficiency": [r"\befficien", r"\bscalab", r"\bcommunication cost\b", r"\bcompute\b", r"\bruntime\b"],
    "evidence_or_benchmark": [r"\bbenchmark\b", r"\bdataset\b", r"\bevaluation\b", r"\bablation\b", r"\bbaseline\b"],
}

WEIGHTED_RISK_PATTERNS: dict[str, list[tuple[str, int, str]]] = {
    "low_novelty_or_incremental": [
        (r"\bincremental\b", 3, "explicit incremental"),
        (r"limited novelty|novelty (?:is |seems |appears )?(?:limited|low|weak|minor)", 5, "limited novelty"),
        (r"lack[s]? (?:of )?novelty|insufficient(?:ly)? novel|not sufficiently novel", 5, "lack of novelty"),
        (r"not (?:particularly |very |that )?novel\b|novelty is not (?:particularly )?high", 5, "not novel"),
        (r"limited contribution|contribution (?:appears|is|seems) limited|weak contribution|marginal contribution", 4, "limited contribution"),
        (r"minor modification|minor extension|straightforward extension|simple extension", 5, "minor extension"),
        (r"not clear (?:what is )?novel|unclear novelty", 4, "unclear novelty"),
    ],
    "abc_combination": [
        (r"combination of existing|combines existing|simple combination|na[iï]ve combination", 5, "existing-method combination"),
        (r"\b(combine|combines|combined|combining|integrate|integrates|integrating)\b", 2, "combine/integrate"),
        (r"\b(hybrid|unify|unifies|unified)\b", 2, "hybrid/unified"),
        (r"plug-and-play|modular", 1, "plug-and-play/modular"),
        (r"\b[A-Za-z0-9]+[+][A-Za-z0-9]+(?:[+][A-Za-z0-9]+)?", 3, "literal A+B pattern"),
    ],
    "transfer_or_light_adaptation": [
        (r"adapt(s|ed|ing)? .* to|adapts? .*? to", 2, "adapted to new setting"),
        (r"extend(s|ed|ing)? .* to|extension of|extends? .*? to", 2, "extension/transfer"),
        (r"based on|builds? on|variant of|similar to prior|closely related to prior", 2, "prior-method adaptation"),
        (r"\btransfer\b|method migration", 2, "transfer/migration"),
    ],
    "engineering_or_efficiency": [
        (r"mostly engineering|engineering contribution", 4, "mostly engineering"),
        (r"efficien(t|cy)|scalab(le|ility)|communication cost|computation cost|runtime|memory", 2, "efficiency/system"),
        (r"system|deployment|practical implementation|optimization", 1, "system optimization"),
    ],
    "evidence_or_benchmark": [
        (r"benchmark|dataset|evaluation protocol|empirical study|ablation|stress test", 1, "evidence/benchmark"),
        (r"baseline fairness|comparison is limited|limited experiments|experimental scope", 2, "evaluation concern"),
    ],
}

REVIEW_CONCERN_BUCKETS = ["official_reviews", "meta_review", "decision", "reviewer_followups", "public_comments", "other"]

INDEX_FIELDS = [
    "paper_key",
    "title",
    "year",
    "venue",
    "source_kind",
    "source_url",
    "categories",
    "risk_tier",
    "risk_score",
    "novelty_score",
    "combo_score",
    "candidate_flags",
    "incremental_types",
    "screening_reason",
    "evidence_snippets",
    "pdf_available",
    "review_available",
    "reply_available",
    "material_dir",
    "domain_score",
    "forum",
    "note_id",
]


def unwrap(value: Any) -> Any:
    if isinstance(value, dict) and "value" in value and len(value) <= 3:
        return value["value"]
    return value


def content_value(content: dict[str, Any], *keys: str, default: Any = "") -> Any:
    for key in keys:
        if key in content:
            return unwrap(content[key])
    return default


def flatten(obj: Any) -> str:
    obj = unwrap(obj)
    if isinstance(obj, dict):
        return " ".join(flatten(v) for v in obj.values())
    if isinstance(obj, list):
        return " ".join(flatten(v) for v in obj)
    if obj is None:
        return ""
    return str(obj)


def clean(text: str) -> str:
    text = re.sub(r"\r\n?", "\n", text or "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def slugify(text: str, max_len: int = 70) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return (text[:max_len].strip("-") or "paper")


def note_to_json(note: Any) -> dict[str, Any]:
    data = note.to_json() if hasattr(note, "to_json") else {
        "id": getattr(note, "id", ""),
        "forum": getattr(note, "forum", ""),
        "number": getattr(note, "number", None),
        "content": getattr(note, "content", {}),
        "invitations": getattr(note, "invitations", []),
        "signatures": getattr(note, "signatures", []),
        "replyto": getattr(note, "replyto", None),
    }
    return json.loads(json.dumps(data, ensure_ascii=False, default=str))


def domain_patterns(domain: str) -> list[str]:
    lowered = domain.lower()
    patterns: list[str] = []
    if "\u8054\u90a6" in domain or lowered in {"fl", "federated learning"} or "federated" in lowered or "联邦" in domain:
        patterns.extend(DOMAIN_ALIASES["federated"])
    if "\u534a\u76d1\u7763" in domain or "semi" in lowered or "半监督" in domain:
        patterns.extend(DOMAIN_ALIASES["semi-supervised"])
    if patterns:
        return list(dict.fromkeys(patterns))
    parts = [part for part in re.split(r"[\s,;/_-]+", lowered) if len(part) > 2]
    return [re.escape(part) for part in parts] or [re.escape(lowered)]


def submission_dict(note: Any, year: str) -> dict[str, Any]:
    content = getattr(note, "content", {}) or {}
    return {
        "id": note.id,
        "forum": note.forum,
        "number": getattr(note, "number", None),
        "title": content_value(content, "title"),
        "abstract": content_value(content, "abstract"),
        "TLDR": content_value(content, "TLDR", "tldr", "TL;DR"),
        "keywords": content_value(content, "keywords", default=[]),
        "primary_area": content_value(content, "primary_area", "subject_areas", default=""),
        "venue": content_value(content, "venue", default=f"ICLR {year}"),
        "venueid": content_value(content, "venueid", default=f"ICLR.cc/{year}/Conference"),
        "year": year,
        "pdf": content_value(content, "pdf", default=""),
        "source_url": f"{OPENREVIEW_BASE}/forum?id={note.forum}",
        "raw_note": note_to_json(note),
    }


def paper_key(submission: dict[str, Any], year: str) -> str:
    return f"iclr{year}_{submission.get('number') or 'x'}_{slugify(str(submission.get('title') or submission.get('id')) , 32)}"


def pattern_hits(text: str, patterns: list[str]) -> list[str]:
    return [pattern for pattern in patterns if re.search(pattern, text, flags=re.IGNORECASE)]


def snippets(text: str, patterns: list[str], limit: int = 4) -> list[str]:
    out: list[str] = []
    for sent in re.split(r"(?<=[.!?])\s+", clean(text)):
        if any(re.search(pattern, sent, flags=re.IGNORECASE) for pattern in patterns):
            out.append(sent[:260])
        if len(out) >= limit:
            break
    return out


def score_domains(submission: dict[str, Any], focus_domains: list[str]) -> tuple[list[str], int, list[str]]:
    text = " ".join(flatten(submission.get(field)) for field in ["title", "abstract", "TLDR", "keywords", "primary_area"])
    categories: list[str] = []
    reasons: list[str] = []
    score = 0
    for domain in focus_domains:
        hits = pattern_hits(text, domain_patterns(domain))
        if hits:
            categories.append(domain)
            score += min(8, 2 * len(hits))
            reasons.append(f"{domain}: {', '.join(hits[:4])}")
    return categories, score, reasons


def classify_risk(text: str) -> tuple[str, list[str], list[str]]:
    types: list[str] = []
    ev: list[str] = []
    for name, patterns in RISK_PATTERNS.items():
        if pattern_hits(text, patterns):
            types.append(name)
            ev.extend(snippets(text, patterns, 2))
    risk = "high" if "low_novelty_or_incremental" in types or "abc_combination" in types or len(types) >= 2 else "medium"
    return risk, types or ["domain-relevant"], ev[:8]


def numeric(value: Any) -> float | None:
    value = unwrap(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"-?\d+(?:\.\d+)?", value)
        if match:
            return float(match.group(0))
    return None


def match_weighted(text: str, groups: dict[str, list[tuple[str, int, str]]]) -> tuple[dict[str, int], dict[str, list[str]]]:
    scores: dict[str, int] = {}
    evidence: dict[str, list[str]] = {}
    for group, patterns in groups.items():
        group_score = 0
        group_evidence: list[str] = []
        for pattern, weight, label in patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                group_score += weight
                matched = snippets(text, [pattern], 1)
                group_evidence.append(f"{label}: {matched[0] if matched else pattern}")
        if group_score:
            scores[group] = group_score
            evidence[group] = group_evidence
    return scores, evidence


def review_signal_bundle(buckets: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    ratings: list[float] = []
    contributions: list[float] = []
    concern_parts: list[str] = []
    all_parts: list[str] = []
    for bucket in REVIEW_CONCERN_BUCKETS:
        for note in buckets.get(bucket, []):
            content = note.get("content") or {}
            flat = flatten(content)
            all_parts.append(flat)
            if bucket == "official_reviews":
                for key in ["rating", "recommendation", "soundness", "presentation"]:
                    score = numeric(content.get(key))
                    if score is not None and key in {"rating", "recommendation"}:
                        ratings.append(score)
                for key in ["contribution", "novelty", "significance"]:
                    score = numeric(content.get(key))
                    if score is not None:
                        contributions.append(score)
                for key in ["weaknesses", "questions", "limitations", "summary"]:
                    concern_parts.append(flatten(content.get(key)))
            elif bucket in {"meta_review", "decision", "reviewer_followups"}:
                concern_parts.append(flat)
    return {
        "ratings": ratings,
        "contributions": contributions,
        "review_count": len(buckets.get("official_reviews", [])),
        "concern_text": clean(" ".join(concern_parts)),
        "forum_text": clean(" ".join(all_parts)),
    }


def classify_evidence_risk(submission: dict[str, Any], buckets: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    metadata_text = " ".join(flatten(submission.get(field)) for field in ["title", "abstract", "TLDR", "keywords", "primary_area"])
    signals = review_signal_bundle(buckets)
    concern_text = signals["concern_text"]
    review_scores, review_evidence = match_weighted(concern_text, WEIGHTED_RISK_PATTERNS)
    metadata_scores, metadata_evidence = match_weighted(metadata_text, WEIGHTED_RISK_PATTERNS)

    novelty_score = review_scores.get("low_novelty_or_incremental", 0)
    combo_score = review_scores.get("abc_combination", 0) + min(4, metadata_scores.get("abc_combination", 0))
    transfer_score = review_scores.get("transfer_or_light_adaptation", 0) + min(3, metadata_scores.get("transfer_or_light_adaptation", 0))
    engineering_score = review_scores.get("engineering_or_efficiency", 0) + min(3, metadata_scores.get("engineering_or_efficiency", 0))
    benchmark_score = review_scores.get("evidence_or_benchmark", 0) + min(2, metadata_scores.get("evidence_or_benchmark", 0))

    ratings = signals["ratings"]
    contributions = signals["contributions"]
    low_contribution_count = sum(1 for score in contributions if score <= 2)
    mean_contribution = sum(contributions) / len(contributions) if contributions else 0.0
    min_rating = min(ratings) if ratings else 0.0

    risk_score = float(novelty_score)
    risk_score += min(4.0, combo_score * 0.5)
    risk_score += min(3.0, transfer_score * 0.5)
    risk_score += min(3.0, engineering_score * 0.5)
    risk_score += min(2.0, benchmark_score * 0.25)
    if low_contribution_count >= 2:
        risk_score += 2
    if contributions and mean_contribution <= 2.25:
        risk_score += 2
    if ratings and min_rating <= 4:
        risk_score += 1

    high = (
        novelty_score >= 5
        or risk_score >= 6
        or (novelty_score >= 3 and (low_contribution_count >= 1 or combo_score >= 2))
        or (contributions and mean_contribution <= 2.0 and (combo_score >= 2 or transfer_score >= 2))
    )
    medium = not high and (risk_score >= 3 or combo_score >= 2 or transfer_score >= 2 or engineering_score >= 2)
    risk_tier = "high" if high else ("medium" if medium else "low")

    types: list[str] = []
    if novelty_score:
        types.append("low_novelty_or_incremental")
    if combo_score:
        types.append("abc_combination")
    if transfer_score:
        types.append("transfer_or_light_adaptation")
    if engineering_score:
        types.append("engineering_or_efficiency")
    if benchmark_score:
        types.append("evidence_or_benchmark")
    if low_contribution_count or (contributions and mean_contribution <= 2.25):
        types.append("low_contribution_score")
    if ratings and min_rating <= 4:
        types.append("accepted_despite_low_score_dispute")

    evidence: list[str] = []
    for source in [review_evidence, metadata_evidence]:
        for group in WEIGHTED_RISK_PATTERNS:
            evidence.extend(source.get(group, [])[:2])

    flags: list[str] = []
    if novelty_score >= 5:
        flags.append("explicit_review_novelty_or_incrementality_concern")
    elif novelty_score:
        flags.append("weak_review_novelty_signal")
    if combo_score >= 4:
        flags.append("strong_A_plus_B_or_combination_signal")
    elif combo_score:
        flags.append("light_combination_signal")
    if low_contribution_count >= 2:
        flags.append("multiple_low_contribution_reviews")
    elif low_contribution_count == 1:
        flags.append("one_low_contribution_review")
    if contributions and mean_contribution <= 2.25:
        flags.append("low_mean_contribution")
    if ratings and min_rating <= 4:
        flags.append("has_rating_4_or_lower")

    return {
        "risk_tier": risk_tier,
        "risk_score": risk_score,
        "novelty_score": novelty_score,
        "combo_score": combo_score,
        "incremental_types": types or ["domain-relevant"],
        "evidence_snippets": evidence[:10],
        "candidate_flags": flags,
        "review_count": signals["review_count"],
        "ratings": ratings,
        "contributions": contributions,
        "forum_text": signals["forum_text"],
    }


def classify_forum(notes: list[Any]) -> dict[str, list[dict[str, Any]]]:
    buckets = {name: [] for name in ["official_reviews", "meta_review", "decision", "author_replies", "reviewer_followups", "public_comments", "other"]}
    for note in notes:
        data = note_to_json(note)
        invitations = " ".join(getattr(note, "invitations", []) or [])
        signatures = " ".join(getattr(note, "signatures", []) or [])
        if "/-/Official_Review" in invitations:
            buckets["official_reviews"].append(data)
        elif "/-/Meta_Review" in invitations:
            buckets["meta_review"].append(data)
        elif "/-/Decision" in invitations:
            buckets["decision"].append(data)
        elif "/-/Official_Comment" in invitations and "/Authors" in signatures:
            buckets["author_replies"].append(data)
        elif "/-/Official_Comment" in invitations and "/Reviewer_" in signatures:
            buckets["reviewer_followups"].append(data)
        elif "/-/Public_Comment" in invitations:
            buckets["public_comments"].append(data)
        elif getattr(note, "replyto", None):
            buckets["other"].append(data)
    return buckets


def note_md(note: dict[str, Any]) -> str:
    content = note.get("content") or {}
    title = flatten(content.get("title")) or note.get("id", "note")
    lines = [f"## {title}", ""]
    for key, value in content.items():
        if key == "title":
            continue
        text = clean(flatten(value))
        if text:
            lines.extend([f"### {key}", "", text, ""])
    return "\n".join(lines).strip()


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_md(path: Path, notes: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n\n".join(note_md(note) for note in notes).strip() + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=INDEX_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            row = dict(row)
            for key, value in list(row.items()):
                if isinstance(value, list):
                    row[key] = "; ".join(str(x) for x in value)
            writer.writerow(row)


def download_pdf(session: requests.Session, submission: dict[str, Any], out_path: Path) -> tuple[bool, str]:
    candidates = []
    pdf = str(submission.get("pdf") or "")
    if pdf.startswith("/"):
        candidates.append(f"{OPENREVIEW_BASE}{pdf}")
    candidates.append(f"{OPENREVIEW_BASE}/pdf?id={submission['id']}")
    for url in candidates:
        for attempt in range(1, 4):
            try:
                response = session.get(url, timeout=60, headers={"User-Agent": "delta-reframer-factory/1.0"})
                if response.status_code == 429:
                    time.sleep(5 * attempt)
                    continue
                response.raise_for_status()
                if response.content[:4] != b"%PDF":
                    return False, f"not a pdf: {url}"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(response.content)
                return True, url
            except Exception as exc:  # noqa: BLE001
                if attempt == 3:
                    return False, f"{url}: {exc}"
                time.sleep(2 * attempt)
    return False, "no pdf url"


def get_accepted_submissions(year: str) -> tuple[Any, str, list[Any]]:
    api2_client = openreview.api.OpenReviewClient(baseurl=API2_BASE)
    notes = list(api2_client.get_all_notes(content={"venueid": f"ICLR.cc/{year}/Conference"}))
    if notes:
        return api2_client, "openreview-api2", notes

    api1_client = openreview.Client(baseurl=API1_BASE)
    notes = list(api1_client.get_all_notes(content={"venueid": f"ICLR.cc/{year}/Conference"}))
    return api1_client, "openreview-api1", notes


def get_forum_notes(client: Any, forum: str) -> list[Any]:
    try:
        return list(client.get_notes(forum=forum, limit=1000))
    except TypeError:
        return list(client.get_notes(forum=forum))


def row_for(
    submission: dict[str, Any],
    key: str,
    categories: list[str],
    score: int,
    reasons: list[str],
    risk: str,
    types: list[str],
    ev: list[str],
    pdf: bool,
    review: bool,
    reply: bool,
    risk_score: float = 0.0,
    novelty_score: int = 0,
    combo_score: int = 0,
    candidate_flags: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "paper_key": key,
        "title": submission.get("title", ""),
        "year": submission.get("year", ""),
        "venue": submission.get("venue", ""),
        "source_kind": "iclr-openreview",
        "source_url": submission.get("source_url", ""),
        "categories": categories,
        "risk_tier": risk,
        "risk_score": f"{risk_score:.2f}",
        "novelty_score": novelty_score,
        "combo_score": combo_score,
        "candidate_flags": candidate_flags or [],
        "incremental_types": types,
        "screening_reason": "; ".join(reasons),
        "evidence_snippets": " || ".join(dict.fromkeys(ev)),
        "pdf_available": pdf,
        "review_available": review,
        "reply_available": reply,
        "material_dir": (Path("materials") / "_by_paper" / key).as_posix(),
        "domain_score": score,
        "forum": submission.get("forum", ""),
        "note_id": submission.get("id", ""),
    }


def balanced_select(candidates: list[dict[str, Any]], cap: int, focus_domains: list[str], score_key: str = "score") -> list[dict[str, Any]]:
    if len(candidates) <= cap:
        return candidates
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    quota = max(1, cap // max(1, len(focus_domains)))
    by_domain: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        for category in candidate["categories"]:
            by_domain[category].append(candidate)
    sort_key = lambda x: (-float(x.get(score_key, x.get("score", 0)) or 0), -float(x.get("score", 0) or 0), str(x["submission"].get("title") or ""))
    for domain in focus_domains:
        count = 0
        for candidate in sorted(by_domain.get(domain, []), key=sort_key):
            if count >= quota:
                break
            if candidate["key"] not in seen:
                selected.append(candidate)
                seen.add(candidate["key"])
            count += 1
    for candidate in sorted(candidates, key=sort_key):
        if len(selected) >= cap:
            break
        if candidate["key"] not in seen:
            selected.append(candidate)
            seen.add(candidate["key"])
    return selected[:cap]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a project corpus run from ICLR OpenReview accepted papers.")
    parser.add_argument("--year", required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--focus-domains", nargs="+", required=True)
    parser.add_argument("--cap", type=int, default=100)
    parser.add_argument("--review-pool-size", type=int, default=None, help="Number of domain candidates to fetch reviews for before final evidence-risk selection.")
    parser.add_argument("--preselect-multiplier", type=int, default=4, help="Fallback review pool multiplier when --review-pool-size is not set.")
    parser.add_argument("--sleep", type=float, default=1.05)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = args.run_dir.resolve()
    for rel in ["discovery", "index", "materials/_by_paper", "logs", "reports"]:
        (run_dir / rel).mkdir(parents=True, exist_ok=True)
    write_json(
        run_dir / "config.json",
        {
            "schema_version": "1.0",
            "source_kind": "iclr-openreview",
            "source_api": "api2-with-api1-fallback",
            "domain_scope": "computer-science",
            "year": args.year,
            "venueid": f"ICLR.cc/{args.year}/Conference",
            "focus_domains": args.focus_domains,
            "cap": args.cap,
            "created_at": dt.datetime.now().isoformat(timespec="seconds"),
        },
    )
    client, source_api, notes = get_accepted_submissions(args.year)
    discovered: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for note in notes:
        sub = submission_dict(note, args.year)
        key = paper_key(sub, args.year)
        categories, score, reasons = score_domains(sub, args.focus_domains)
        text = " ".join(flatten(sub.get(field)) for field in ["title", "abstract", "TLDR", "keywords", "primary_area"])
        risk, types, ev = classify_risk(text)
        discovered.append({"paper_key": key, "forum": sub["forum"], "title": sub["title"], "categories": categories, "domain_score": score})
        all_rows.append(row_for(sub, key, categories or ["Other"], score, reasons, risk if categories else "unscored", types if categories else [], ev, bool(sub.get("pdf")), False, False))
        if categories:
            candidates.append({"key": key, "submission": sub, "categories": categories, "score": score, "reasons": reasons})
    review_pool_size = args.review_pool_size or max(args.cap, args.cap * max(1, args.preselect_multiplier))
    review_pool_size = min(len(candidates), review_pool_size)
    review_pool = balanced_select(candidates, review_pool_size, args.focus_domains, score_key="score")
    write_jsonl(run_dir / "discovery" / "discovered_papers.jsonl", discovered)
    write_jsonl(run_dir / "discovery" / "search_queries.jsonl", [{"source": source_api, "query": {"content.venueid": f"ICLR.cc/{args.year}/Conference"}, "focus_domains": args.focus_domains}])
    write_csv(run_dir / "index" / "all_candidates.csv", all_rows)

    session = requests.Session()
    enriched: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    pool_rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    logs: list[dict[str, Any]] = []
    for idx, candidate in enumerate(review_pool, 1):
        sub = candidate["submission"]
        key = candidate["key"]
        logs.append({"event": "fetch_forum", "paper_key": key, "index": idx, "total": len(review_pool)})
        try:
            buckets = classify_forum(get_forum_notes(client, sub["forum"]))
        except Exception as exc:  # noqa: BLE001
            buckets = {name: [] for name in ["official_reviews", "meta_review", "decision", "author_replies", "reviewer_followups", "public_comments", "other"]}
            failures.append({"paper_key": key, "stage": "fetch_forum", "error": str(exc)})
        review_available = bool(buckets["official_reviews"] or buckets["meta_review"] or buckets["decision"])
        reply_available = bool(buckets["author_replies"] or buckets["reviewer_followups"] or buckets["public_comments"])
        risk_info = classify_evidence_risk(sub, buckets)
        candidate = dict(candidate)
        candidate.update(
            {
                "buckets": buckets,
                "review_available": review_available,
                "reply_available": reply_available,
                "risk_tier": risk_info["risk_tier"],
                "risk_score": risk_info["risk_score"],
                "novelty_score": risk_info["novelty_score"],
                "combo_score": risk_info["combo_score"],
                "incremental_types": risk_info["incremental_types"],
                "evidence_snippets": risk_info["evidence_snippets"],
                "candidate_flags": risk_info["candidate_flags"],
            }
        )
        enriched.append(candidate)
        pool_rows.append(
            row_for(
                sub,
                key,
                candidate["categories"],
                candidate["score"],
                candidate["reasons"] + risk_info["candidate_flags"],
                risk_info["risk_tier"],
                risk_info["incremental_types"],
                risk_info["evidence_snippets"],
                bool(sub.get("pdf")),
                review_available,
                reply_available,
                risk_info["risk_score"],
                risk_info["novelty_score"],
                risk_info["combo_score"],
                risk_info["candidate_flags"],
            )
        )
        time.sleep(args.sleep)

    write_csv(run_dir / "index" / "review_pool_candidates.csv", sorted(pool_rows, key=lambda r: float(r["risk_score"]), reverse=True))
    selected = balanced_select(enriched, args.cap, args.focus_domains, score_key="risk_score")

    for idx, candidate in enumerate(selected, 1):
        sub = candidate["submission"]
        key = candidate["key"]
        buckets = candidate["buckets"]
        folder = run_dir / "materials" / "_by_paper" / key
        folder.mkdir(parents=True, exist_ok=True)
        logs.append({"event": "download_selected_pdf", "paper_key": key, "index": idx, "total": len(selected), "risk_score": candidate["risk_score"]})
        review_available = bool(candidate["review_available"])
        reply_available = bool(candidate["reply_available"])
        pdf_ok, pdf_detail = download_pdf(session, sub, folder / "paper.pdf")
        if not pdf_ok:
            failures.append({"paper_key": key, "stage": "download_pdf", "error": pdf_detail})
        write_json(folder / "submission.json", {k: v for k, v in sub.items() if k != "raw_note"})
        write_json(folder / "submission_raw.json", sub["raw_note"])
        for bucket, names in [
            ("official_reviews", ("official_reviews.json", "official_reviews.md")),
            ("meta_review", ("meta_review.json", "meta_review.md")),
            ("decision", ("decision.json", "decision.md")),
            ("author_replies", ("author_replies.json", "author_replies.md")),
        ]:
            if buckets[bucket]:
                write_json(folder / names[0], buckets[bucket])
                write_md(folder / names[1], buckets[bucket])
        for bucket in ["reviewer_followups", "public_comments", "other"]:
            if buckets[bucket]:
                write_json(folder / f"{bucket}.json", buckets[bucket])
        write_json(
            folder / "source_status.json",
            {
                "schema_version": "1.0",
                "source_kind": "iclr-openreview",
                "domain_scope": "computer-science",
                "source_url": sub["source_url"],
                "pdf_available": pdf_ok,
                "reviews_missing": not review_available,
                "replies_missing": not reply_available,
                "review_attack_mode": "real-review" if review_available else "simulated-review-only",
                "download_status": "ok" if pdf_ok else "partial",
                "notes": [f"pdf downloaded from {pdf_detail}" if pdf_ok else pdf_detail],
            },
        )
        rows.append(
            row_for(
                sub,
                key,
                candidate["categories"],
                candidate["score"],
                candidate["reasons"] + candidate["candidate_flags"],
                candidate["risk_tier"],
                candidate["incremental_types"],
                candidate["evidence_snippets"],
                pdf_ok,
                review_available,
                reply_available,
                float(candidate["risk_score"]),
                int(candidate["novelty_score"]),
                int(candidate["combo_score"]),
                candidate["candidate_flags"],
            )
        )
        time.sleep(args.sleep)
    high_rows = [row for row in rows if row["risk_tier"] == "high"] or rows
    write_csv(run_dir / "index" / "screened_incremental_candidates.csv", rows)
    write_csv(run_dir / "index" / "high_risk_candidates.csv", high_rows)
    write_csv(run_dir / "index" / "incremental_all_index.csv", rows)
    write_jsonl(run_dir / "logs" / "download_manifest.jsonl", rows)
    write_jsonl(run_dir / "logs" / "failures.jsonl", failures)
    write_jsonl(run_dir / "discovery" / "source_api_logs.jsonl", logs)
    counts = Counter(category for row in rows for category in row["categories"])
    with (run_dir / "index" / "category_summary.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["category", "count"])
        writer.writeheader()
        for category, count in counts.most_common():
            writer.writerow({"category": category, "count": count})
    overview = [
        "# ICLR OpenReview Project Discovery Summary",
        "",
        f"- Year: {args.year}",
        f"- Accepted submissions discovered: {len(notes)}",
        f"- Domain candidates before cap: {len(candidates)}",
        f"- Review-aware preselection pool: {len(review_pool)}",
        f"- Selected/downloaded: {len(rows)}",
        f"- Cap: {args.cap}",
        f"- Failures: {len(failures)}",
    ]
    (run_dir / "reports" / "overview.md").write_text("\n".join(overview) + "\n", encoding="utf-8")
    risk_counts = Counter(row["risk_tier"] for row in rows)
    print(json.dumps({"run_dir": str(run_dir), "source_api": source_api, "accepted_submissions_discovered": len(notes), "domain_candidates": len(candidates), "review_pool": len(review_pool), "selected": len(rows), "failures": len(failures), "category_counts": dict(counts), "risk_counts": dict(risk_counts)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
