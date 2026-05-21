#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
import unicodedata
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from common import default_state_dir


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATE_DIR = default_state_dir()
DEFAULT_OUT_DIR = Path("outputs/delta_contribution_knowledge_base")
FILE_PREFIX = "incremental"


CATEGORY_ORDER = [
    "LLM",
    "NLP",
    "CV",
    "VLM",
    "VLA",
    "Agent",
    "RL",
    "FL",
    "Semi-supervised",
    "Self-supervised",
    "Generative/Diffusion",
    "Robotics/Embodied",
    "Graph",
    "Safety/Alignment/Privacy/Fairness",
    "Interpretability",
    "Data/Benchmark",
    "Optimization",
    "Theory",
    "Systems/Efficiency",
    "Science/Bio",
    "Time-Series",
    "Causality",
    "Meta/Continual",
    "Audio/Speech",
    "Multimodal",
    "Neurosymbolic/Reasoning",
    "Other",
]


CATEGORY_RULES: dict[str, list[str]] = {
    "LLM": [
        r"\bllm(s)?\b",
        r"large language model(s)?",
        r"\blanguage model(s)?\b",
        r"foundation model(s)?",
        r"instruction tuning",
        r"prompt(ing)?",
        r"chain[- ]of[- ]thought",
        r"\brlhf\b",
        r"\bdpo\b",
        r"\blora\b",
        r"reasoning llm",
    ],
    "NLP": [
        r"natural language",
        r"\bnlp\b",
        r"text generation",
        r"text classification",
        r"machine translation",
        r"summarization",
        r"question answering",
        r"information retrieval",
        r"\brag\b",
        r"retrieval[- ]augmented",
        r"code generation",
        r"semantic parsing",
    ],
    "CV": [
        r"computer vision",
        r"\bimage(s)?\b",
        r"\bvideo(s)?\b",
        r"visual",
        r"segmentation",
        r"detection",
        r"recognition",
        r"3d reconstruction",
        r"depth estimation",
        r"camera pose",
        r"point cloud",
        r"object tracking",
    ],
    "VLM": [
        r"\bvlm(s)?\b",
        r"vision[- ]language",
        r"visual[- ]language",
        r"image[- ]text",
        r"video[- ]language",
        r"multimodal large language model",
        r"\bmllm(s)?\b",
        r"\bclip\b",
    ],
    "VLA": [
        r"\bvla\b",
        r"vision[- ]language[- ]action",
        r"vision language action",
        r"action[- ]conditioned vision",
        r"robot policy",
        r"robotic manipulation",
        r"embodied action",
    ],
    "Agent": [
        r"\bagent(s)?\b",
        r"multi[- ]agent",
        r"tool use",
        r"tool[- ]using",
        r"web agent",
        r"autonomous agent",
        r"agentic",
        r"planner agent",
    ],
    "RL": [
        r"reinforcement learning",
        r"\brl\b",
        r"offline rl",
        r"online rl",
        r"policy optimization",
        r"markov decision",
        r"\bmdp\b",
        r"bandit",
        r"reward model",
        r"imitation learning",
        r"preference optimization",
        r"policy gradient",
        r"q[- ]learning",
    ],
    "FL": [
        r"federated learning",
        r"\bfederated\b",
        r"client drift",
        r"cross[- ]device",
        r"cross[- ]silo",
        r"decentralized learning",
    ],
    "Semi-supervised": [
        r"semi[- ]supervised",
        r"weakly[- ]supervised",
        r"pseudo[- ]label",
        r"label[- ]efficient",
        r"few labeled",
    ],
    "Self-supervised": [
        r"self[- ]supervised",
        r"contrastive learning",
        r"masked autoencoder",
        r"masked modeling",
        r"representation learning",
        r"pretext",
    ],
    "Generative/Diffusion": [
        r"generative model",
        r"\bdiffusion\b",
        r"flow matching",
        r"score[- ]based",
        r"text[- ]to[- ]image",
        r"image generation",
        r"video generation",
        r"\bvae\b",
        r"\bgan\b",
        r"normalizing flow",
        r"autoregressive generation",
    ],
    "Robotics/Embodied": [
        r"robot",
        r"robotics",
        r"embodied",
        r"manipulation",
        r"navigation",
        r"autonomous driving",
        r"locomotion",
    ],
    "Graph": [
        r"graph neural",
        r"\bgnn\b",
        r"graph representation",
        r"knowledge graph",
        r"hypergraph",
        r"geometric deep learning",
        r"topolog",
    ],
    "Safety/Alignment/Privacy/Fairness": [
        r"alignment",
        r"safety",
        r"fairness",
        r"privacy",
        r"differential privacy",
        r"robustness",
        r"adversarial",
        r"jailbreak",
        r"red[- ]team",
        r"toxicity",
        r"watermark",
        r"unlearning",
    ],
    "Interpretability": [
        r"interpretability",
        r"explainable",
        r"\bxai\b",
        r"mechanistic interpretability",
        r"attribution",
        r"concept bottleneck",
        r"sparse autoencoder",
    ],
    "Data/Benchmark": [
        r"benchmark",
        r"new dataset",
        r"large[- ]scale dataset",
        r"dataset curation",
        r"leaderboard",
        r"data curation",
        r"data selection",
        r"synthetic data",
    ],
    "Optimization": [
        r"optimization",
        r"optimizer",
        r"gradient descent",
        r"learning rate",
        r"convex",
        r"bilevel",
        r"hyperparameter",
        r"training dynamics",
    ],
    "Theory": [
        r"learning theory",
        r"generalization bound",
        r"theorem",
        r"sample complexity",
        r"convergence",
        r"proof",
        r"statistical learning",
    ],
    "Systems/Efficiency": [
        r"systems",
        r"efficiency",
        r"efficient inference",
        r"efficient training",
        r"compute[- ]efficient",
        r"parameter[- ]efficient",
        r"compression",
        r"quantization",
        r"pruning",
        r"distillation",
        r"serving",
        r"hardware",
        r"parallel training",
        r"acceleration",
    ],
    "Science/Bio": [
        r"biology",
        r"protein",
        r"molecule",
        r"chemistry",
        r"physics",
        r"materials science",
        r"genomics",
        r"medical",
        r"healthcare",
        r"drug",
    ],
    "Time-Series": [
        r"time[- ]series",
        r"temporal",
        r"dynamical system",
        r"forecasting",
        r"sequence modeling",
        r"survival process",
    ],
    "Causality": [
        r"causal",
        r"causality",
        r"counterfactual",
        r"treatment effect",
        r"causal discovery",
    ],
    "Meta/Continual": [
        r"meta[- ]learning",
        r"transfer learning",
        r"continual learning",
        r"lifelong learning",
        r"domain adaptation",
        r"out[- ]of[- ]distribution",
    ],
    "Audio/Speech": [
        r"audio",
        r"speech",
        r"speaker",
        r"music",
        r"sound",
        r"acoustic",
    ],
    "Multimodal": [
        r"multimodal",
        r"multi[- ]modal",
        r"cross[- ]modal",
        r"modality",
        r"image and text",
        r"vision and language",
    ],
    "Neurosymbolic/Reasoning": [
        r"neurosymbolic",
        r"neuro[- ]symbolic",
        r"formal reasoning",
        r"logic",
        r"symbolic",
        r"reasoning",
        r"theorem proving",
    ],
}


PRIMARY_AREA_MAP: list[tuple[str, str]] = [
    ("foundation or frontier models", "LLM"),
    ("reinforcement learning", "RL"),
    ("generative models", "Generative/Diffusion"),
    ("datasets and benchmarks", "Data/Benchmark"),
    ("alignment, fairness, safety, privacy", "Safety/Alignment/Privacy/Fairness"),
    ("representation learning", "Self-supervised"),
    ("robotics", "Robotics/Embodied"),
    ("learning on graphs", "Graph"),
    ("interpretability", "Interpretability"),
    ("optimization", "Optimization"),
    ("learning theory", "Theory"),
    ("physical sciences", "Science/Bio"),
    ("neuroscience", "Science/Bio"),
    ("time series", "Time-Series"),
    ("causal", "Causality"),
    ("transfer learning", "Meta/Continual"),
    ("probabilistic methods", "Theory"),
    ("neurosymbolic", "Neurosymbolic/Reasoning"),
    ("systems", "Systems/Efficiency"),
]


NOVELTY_PATTERNS: list[tuple[str, int, str]] = [
    (r"\bincremental\b", 3, "explicit incremental"),
    (
        r"limited novelty|novelty (?:is |seems |appears )?(?:limited|low|weak|minor)",
        5,
        "limited novelty",
    ),
    (
        r"lack[s]? (?:of )?novelty|insufficient(?:ly)? novel|not sufficiently novel",
        5,
        "lack of novelty",
    ),
    (
        r"not (?:particularly |very |that )?novel\b|novelty is not (?:particularly )?high",
        5,
        "not novel",
    ),
    (
        r"limited contribution|contribution (?:appears|is|seems) limited|weak contribution|marginal contribution",
        4,
        "limited contribution",
    ),
    (
        r"minor modification|minor extension|straightforward extension|simple extension",
        5,
        "minor extension",
    ),
    (
        r"combination of existing|combines existing|simple combination|na[iï]ve combination",
        5,
        "existing-method combination",
    ),
    (
        r"similar to prior|closely related to prior|overlap[s]? with prior",
        3,
        "prior-work overlap",
    ),
    (r"main novelty lies in", 2, "narrow novelty"),
    (r"mostly engineering", 4, "mostly engineering"),
    (r"not clear (?:what is )?novel|unclear novelty", 4, "unclear novelty"),
]


COMBO_PATTERNS: list[tuple[str, int, str]] = [
    (
        r"\b(combine|combines|combined|combining|integrate|integrates|integrating)\b",
        2,
        "combine/integrate",
    ),
    (r"\b(hybrid|unify|unifies|unified)\b", 2, "hybrid/unified"),
    (r"plug-and-play|modular", 1, "plug-and-play/modular"),
    (r"variant of|extension of|based on|builds on|adapts? .*? to", 2, "variant/extension"),
    (r"\b[A-Za-z0-9]+[+][A-Za-z0-9]+(?:[+][A-Za-z0-9]+)?", 3, "literal A+B pattern"),
]


MATERIAL_SUFFIXES = [
    "paper.pdf",
    "MISSING_PDF.txt",
    "official_reviews.json",
    "official_reviews.md",
    "meta_review.json",
    "meta_review.md",
    "reviewer_followups.json",
    "reviewer_followups.md",
    "decision.json",
    "decision.md",
    "public_comments.json",
    "author_replies.json",
    "author_replies.md",
    "submission.json",
    "pdf_status.json",
    "forum_bundle.json",
]


CSV_FIELDS = [
    "paper_key",
    "year",
    "venue",
    "decision",
    "forum",
    "forum_url",
    "title",
    "authors",
    "primary_area",
    "keywords",
    "categories",
    "risk_tier",
    "risk_score",
    "novelty_score",
    "combo_score",
    "mean_rating",
    "min_rating",
    "mean_contribution",
    "min_contribution",
    "low_contribution_review_count",
    "review_count",
    "candidate_flags",
    "incremental_types",
    "novelty_evidence",
    "combo_evidence",
    "abstract",
    "pdf_available",
    "zip_path",
    "zip_paper_dir",
    "material_dir",
]


REPORT_TOP_N = 40


TYPE_REPORT_FILENAMES = {
    "低创新性被明确质疑": "explicit_low_novelty.md",
    "显式增量式工作": "explicit_incremental.md",
    "已有方法轻改/迁移": "minor_extension_or_transfer.md",
    "A+B/C 组合式方法": "abc_combination.md",
    "工程优化/系统调参型": "engineering_or_system_tuning.md",
    "数据集/基准驱动型": "dataset_or_benchmark_driven.md",
    "贡献评分偏低": "low_contribution_scores.md",
    "有低分争议但最终录用": "accepted_with_low_score_dispute.md",
    "其他弱信号": "other_weak_signals.md",
}


@dataclass
class PaperRow:
    data: dict[str, Any]
    zip_path: Path
    zip_paper_dir: str
    material_entries: dict[str, str]


def clean_space(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def value(obj: Any) -> Any:
    if isinstance(obj, dict) and "value" in obj:
        return obj["value"]
    return obj


def numeric(obj: Any) -> float | None:
    obj = value(obj)
    if isinstance(obj, (int, float)):
        return float(obj)
    if isinstance(obj, str):
        match = re.search(r"-?\d+(?:\.\d+)?", obj)
        if match:
            return float(match.group(0))
    return None


def flatten(obj: Any) -> str:
    obj = value(obj)
    if isinstance(obj, dict):
        return " ".join(flatten(v) for v in obj.values())
    if isinstance(obj, list):
        return " ".join(flatten(v) for v in obj)
    if obj is None:
        return ""
    return str(obj)


def read_json(zf: zipfile.ZipFile, entry: str) -> Any:
    return json.loads(zf.read(entry).decode("utf-8"))


def find_entry(names: Iterable[str], paper_dir: str, suffix: str) -> str | None:
    end = "/" + suffix
    for name in names:
        if name.startswith(paper_dir + "/") and name.endswith(end):
            return name
    return None


def paper_dir_from_submission(entry: str) -> str:
    return entry.rsplit("/", 2)[0]


def slugify(text: str, max_len: int = 80) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    text = re.sub(r"_+", "_", text)
    return (text or "paper")[:max_len].strip("_")


def category_folder(category: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", category).strip("_")


def paper_number_from_dir(paper_dir: str) -> str:
    base = paper_dir.rstrip("/").split("/")[-1]
    match = re.match(r"(\d+)", base)
    return match.group(1) if match else "00000"


def match_patterns(
    text: str, patterns: list[tuple[str, int, str]], max_hits_per_pattern: int = 2
) -> tuple[int, list[str]]:
    lowered = text.lower()
    score = 0
    hits: list[str] = []
    for pattern, weight, label in patterns:
        matches = list(re.finditer(pattern, lowered, flags=re.IGNORECASE | re.DOTALL))
        if not matches:
            continue
        kept = matches[:max_hits_per_pattern]
        score += weight * len(kept)
        for match in kept:
            start = max(0, match.start() - 140)
            end = min(len(text), match.end() + 180)
            context = clean_space(text[start:end])
            hits.append(f"{label}: {context}")
    return score, hits


def classify_categories(submission: dict[str, Any]) -> list[str]:
    keywords = " ".join(str(k) for k in submission.get("keywords") or [])
    strong_text = clean_space(
        " ".join(
            [
                str(submission.get("title") or ""),
                str(submission.get("tldr") or ""),
                keywords,
            ]
        )
    )
    full_text = clean_space(" ".join([strong_text, str(submission.get("abstract") or "")]))
    lowered = full_text.lower()
    strong_lowered = strong_text.lower()
    found: set[str] = set()
    for category, rules in CATEGORY_RULES.items():
        search_text = strong_lowered if category == "Data/Benchmark" else lowered
        if any(re.search(rule, search_text, flags=re.IGNORECASE) for rule in rules):
            found.add(category)

    primary_area = str(submission.get("primary_area") or "").lower()
    for phrase, category in PRIMARY_AREA_MAP:
        if phrase in primary_area:
            found.add(category)

    if not found:
        found.add("Other")
    return [cat for cat in CATEGORY_ORDER if cat in found]


def infer_decision(zf: zipfile.ZipFile, names: list[str], paper_dir: str) -> str:
    decision_entry = find_entry(names, paper_dir, "decision.json")
    if not decision_entry:
        return ""
    try:
        decisions = read_json(zf, decision_entry)
    except Exception:
        return ""
    texts: list[str] = []
    for item in decisions if isinstance(decisions, list) else [decisions]:
        content = item.get("content", {}) if isinstance(item, dict) else {}
        texts.append(str(value(content.get("decision")) or ""))
        texts.append(str(value(content.get("comment")) or ""))
    return clean_space(" ".join(texts))


def collect_review_signals(
    zf: zipfile.ZipFile, names: list[str], paper_dir: str
) -> tuple[dict[str, Any], str, str]:
    official_entry = find_entry(names, paper_dir, "official_reviews.json")
    if not official_entry:
        return {
            "review_count": 0,
            "ratings": [],
            "contributions": [],
            "low_contribution_count": 0,
        }, "", ""

    reviews = read_json(zf, official_entry)
    ratings: list[float] = []
    contributions: list[float] = []
    concern_parts: list[str] = []
    full_review_parts: list[str] = []

    for review in reviews:
        content = review.get("content", {}) if isinstance(review, dict) else {}
        rating = numeric(content.get("rating"))
        contribution = numeric(content.get("contribution"))
        if rating is not None:
            ratings.append(rating)
        if contribution is not None:
            contributions.append(contribution)
        for field in ("weaknesses", "questions"):
            concern_parts.append(flatten(content.get(field)))
        full_review_parts.append(flatten(content))

    meta_entry = find_entry(names, paper_dir, "meta_review.json")
    if meta_entry:
        try:
            concern_parts.append(flatten(read_json(zf, meta_entry)))
        except Exception:
            pass

    decision_entry = find_entry(names, paper_dir, "decision.json")
    if decision_entry:
        try:
            concern_parts.append(flatten(read_json(zf, decision_entry)))
        except Exception:
            pass

    low_contribution_count = sum(1 for score in contributions if score <= 2)
    return (
        {
            "review_count": len(reviews),
            "ratings": ratings,
            "contributions": contributions,
            "low_contribution_count": low_contribution_count,
        },
        clean_space(" ".join(concern_parts)),
        clean_space(" ".join(full_review_parts)),
    )


def mean_or_blank(values: list[float]) -> str:
    if not values:
        return ""
    return f"{sum(values) / len(values):.3f}"


def min_or_blank(values: list[float]) -> str:
    if not values:
        return ""
    return f"{min(values):.3f}"


def build_flags(
    novelty_score: int,
    combo_score: int,
    contributions: list[float],
    ratings: list[float],
) -> tuple[str, str, float]:
    mean_contribution = sum(contributions) / len(contributions) if contributions else 0.0
    low_contribution_count = sum(1 for score in contributions if score <= 2)
    min_rating = min(ratings) if ratings else 0.0

    risk_score = float(novelty_score)
    if low_contribution_count >= 2:
        risk_score += 2
    if contributions and mean_contribution <= 2.25:
        risk_score += 2
    if ratings and min_rating <= 4:
        risk_score += 1
    risk_score += min(4.0, combo_score * 0.5)

    high = (
        novelty_score >= 8
        or (novelty_score >= 5 and (low_contribution_count >= 1 or mean_contribution <= 2.5))
        or (
            contributions
            and mean_contribution <= 2.0
            and low_contribution_count >= 2
            and (novelty_score >= 3 or combo_score >= 4)
        )
    )
    medium = not high and (
        (novelty_score >= 3 and (low_contribution_count >= 1 or combo_score >= 2))
        or (low_contribution_count >= 2 and combo_score >= 4)
        or (contributions and mean_contribution <= 2.25 and ratings and min_rating <= 4)
    )
    tier = "high" if high else ("medium" if medium else "low")

    flags: list[str] = []
    if novelty_score >= 5:
        flags.append("explicit_novelty_or_incremental_concern")
    elif novelty_score >= 3:
        flags.append("weak_novelty_signal")
    if combo_score >= 4:
        flags.append("A_plus_B_combo_signal")
    elif combo_score >= 2:
        flags.append("light_combo_signal")
    if low_contribution_count >= 2:
        flags.append("multiple_low_contribution_reviews")
    elif low_contribution_count == 1:
        flags.append("one_low_contribution_review")
    if contributions and mean_contribution <= 2.25:
        flags.append("low_mean_contribution")
    if ratings and min_rating <= 4:
        flags.append("has_rating_4_or_lower")
    return tier, "; ".join(flags), risk_score


def infer_incremental_types(
    novelty_evidence: list[str],
    combo_evidence: list[str],
    categories: list[str],
    contributions: list[float],
    ratings: list[float],
    risk_tier: str,
) -> list[str]:
    evidence_text = " ".join(novelty_evidence + combo_evidence).lower()
    mean_contribution = sum(contributions) / len(contributions) if contributions else 0.0
    low_contribution_count = sum(1 for score in contributions if score <= 2)
    min_rating = min(ratings) if ratings else 0.0

    types: list[str] = []
    if re.search(
        r"limited novelty|lack of novelty|not novel|not particularly novel|unclear novelty",
        evidence_text,
    ):
        types.append("低创新性被明确质疑")
    if "explicit incremental" in evidence_text or re.search(r"\bincremental\b", evidence_text):
        types.append("显式增量式工作")
    if re.search(
        r"minor extension|minor modification|straightforward extension|simple extension|narrow novelty|variant/extension",
        evidence_text,
    ):
        types.append("已有方法轻改/迁移")
    if re.search(
        r"existing-method combination|combine/integrate|hybrid/unified|plug-and-play/modular|literal a\+b",
        evidence_text,
    ):
        types.append("A+B/C 组合式方法")
    if "mostly engineering" in evidence_text or (
        "Systems/Efficiency" in categories and risk_tier in {"high", "medium"}
    ):
        types.append("工程优化/系统调参型")
    if "Data/Benchmark" in categories and risk_tier in {"high", "medium"}:
        types.append("数据集/基准驱动型")
    if low_contribution_count >= 2 or (contributions and mean_contribution <= 2.25):
        types.append("贡献评分偏低")
    if ratings and min_rating <= 4:
        types.append("有低分争议但最终录用")

    deduped: list[str] = []
    for item in types:
        if item not in deduped:
            deduped.append(item)
    return deduped or ["其他弱信号"]


def matches_focus_domains(submission: dict[str, Any], categories: list[str], focus_domains: list[str] | None) -> bool:
    if not focus_domains:
        return True
    keywords = " ".join(str(k) for k in submission.get("keywords") or [])
    haystack = clean_space(" ".join([
        str(submission.get("title") or ""),
        str(submission.get("abstract") or ""),
        str(submission.get("primary_area") or ""),
        keywords,
        " ".join(categories),
    ])).lower()
    return any(term.lower() in haystack for term in focus_domains)


def build_rows(zip_dir: Path, years: set[int], focus_domains: list[str] | None = None) -> list[PaperRow]:
    rows: list[PaperRow] = []
    zip_paths = sorted(zip_dir.glob("*.zip"))
    for zip_path in zip_paths:
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            for submission_entry in [name for name in names if name.endswith("/submission.json")]:
                submission = read_json(zf, submission_entry)
                submission_year = int(submission.get("year") or 0)
                if submission_year not in years:
                    continue

                paper_dir = paper_dir_from_submission(submission_entry)
                review_signals, concern_text, _ = collect_review_signals(zf, names, paper_dir)
                novelty_score, novelty_hits = match_patterns(concern_text, NOVELTY_PATTERNS)

                combo_basis = clean_space(
                    " ".join(
                        [
                            str(submission.get("title") or ""),
                            str(submission.get("abstract") or ""),
                            str(submission.get("primary_area") or ""),
                            " ".join(str(k) for k in submission.get("keywords") or []),
                            concern_text[:5000],
                        ]
                    )
                )
                combo_score, combo_hits = match_patterns(combo_basis, COMBO_PATTERNS)

                ratings = review_signals["ratings"]
                contributions = review_signals["contributions"]
                risk_tier, flags, risk_score = build_flags(
                    novelty_score, combo_score, contributions, ratings
                )

                paper_number = paper_number_from_dir(paper_dir)
                title = str(submission.get("title") or "")
                forum = str(submission.get("forum") or submission.get("id") or "")
                paper_key = f"{paper_number}_{slugify(title)}_{forum[:8]}"
                categories = classify_categories(submission)
                if not matches_focus_domains(submission, categories, focus_domains):
                    continue

                incremental_types = infer_incremental_types(
                    novelty_hits,
                    combo_hits,
                    categories,
                    contributions,
                    ratings,
                    risk_tier,
                )
                material_entries = {
                    suffix: entry
                    for suffix in MATERIAL_SUFFIXES
                    if (entry := find_entry(names, paper_dir, suffix))
                }
                decision = infer_decision(zf, names, paper_dir)
                material_dir = str(Path("materials") / "_by_paper" / paper_key)

                row = {
                    "paper_key": paper_key,
                    "year": submission.get("year") or submission_year,
                    "venue": submission.get("venue") or "",
                    "decision": decision,
                    "forum": forum,
                    "forum_url": submission.get("forum_url") or "",
                    "title": title,
                    "authors": "; ".join(str(a) for a in submission.get("authors") or []),
                    "primary_area": submission.get("primary_area") or "",
                    "keywords": "; ".join(str(k) for k in submission.get("keywords") or []),
                    "categories": "; ".join(categories),
                    "risk_tier": risk_tier,
                    "risk_score": f"{risk_score:.2f}",
                    "novelty_score": novelty_score,
                    "combo_score": combo_score,
                    "mean_rating": mean_or_blank(ratings),
                    "min_rating": min_or_blank(ratings),
                    "mean_contribution": mean_or_blank(contributions),
                    "min_contribution": min_or_blank(contributions),
                    "low_contribution_review_count": review_signals["low_contribution_count"],
                    "review_count": review_signals["review_count"],
                    "candidate_flags": flags,
                    "incremental_types": "; ".join(incremental_types),
                    "novelty_evidence": " || ".join(novelty_hits[:8]),
                    "combo_evidence": " || ".join(combo_hits[:8]),
                    "abstract": clean_space(str(submission.get("abstract") or "")),
                    "pdf_available": "paper.pdf" in material_entries,
                    "zip_path": str(zip_path),
                    "zip_paper_dir": paper_dir,
                    "material_dir": material_dir,
                }
                rows.append(PaperRow(row, zip_path, paper_dir, material_entries))
    return rows


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_markdown(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8-sig")


def write_category_summaries(out_dir: Path, rows: list[PaperRow]) -> None:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        tier = str(row.data["risk_tier"])
        for category in str(row.data["categories"]).split("; "):
            counts[category]["all"] += 1
            counts[category][tier] += 1

    summary_rows = []
    for category in CATEGORY_ORDER:
        if category not in counts:
            continue
        c = counts[category]
        summary_rows.append(
            {
                "category": category,
                "all_count": c["all"],
                "high_count": c["high"],
                "medium_count": c["medium"],
                "low_count": c["low"],
            }
        )
    write_csv(
        out_dir / "index" / f"{FILE_PREFIX}_category_summary.csv",
        summary_rows,
        ["category", "all_count", "high_count", "medium_count", "low_count"],
    )


def is_core_incremental_candidate(row: dict[str, Any]) -> bool:
    if row["risk_tier"] not in {"high", "medium"}:
        return False
    types = set(str(row["incremental_types"]).split("; "))
    core_types = {
        "低创新性被明确质疑",
        "显式增量式工作",
        "已有方法轻改/迁移",
        "A+B/C 组合式方法",
    }
    return bool(types & core_types)


def write_category_type_matrix(out_dir: Path, rows: list[PaperRow]) -> None:
    matrix: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for row in rows:
        data = row.data
        if data["risk_tier"] not in {"high", "medium"}:
            continue
        categories = [item for item in str(data["categories"]).split("; ") if item]
        types = [item for item in str(data["incremental_types"]).split("; ") if item]
        for category in categories:
            for type_name in types:
                matrix[(category, type_name)]["total"] += 1
                matrix[(category, type_name)][str(data["risk_tier"])] += 1

    out_rows = []
    for (category, type_name), counts in sorted(matrix.items()):
        out_rows.append(
            {
                "category": category,
                "incremental_type": type_name,
                "total_count": counts["total"],
                "high_count": counts["high"],
                "medium_count": counts["medium"],
            }
        )
    write_csv(
        out_dir / "index" / f"{FILE_PREFIX}_category_type_matrix.csv",
        out_rows,
        ["category", "incremental_type", "total_count", "high_count", "medium_count"],
    )


def extract_materials(out_dir: Path, rows: list[PaperRow], tiers: set[str], limit: int | None) -> None:
    selected = [row for row in rows if row.data["risk_tier"] in tiers]
    selected.sort(key=lambda r: float(r.data["risk_score"]), reverse=True)
    if limit is not None:
        selected = selected[:limit]

    by_zip: dict[Path, list[PaperRow]] = defaultdict(list)
    for row in selected:
        by_zip[row.zip_path].append(row)

    extracted_abs_dirs: dict[str, Path] = {}
    for zip_path, grouped_rows in by_zip.items():
        with zipfile.ZipFile(zip_path) as zf:
            for row in grouped_rows:
                material_dir = out_dir / row.data["material_dir"]
                material_dir.mkdir(parents=True, exist_ok=True)
                extracted_abs_dirs[row.data["paper_key"]] = material_dir
                for suffix, entry in row.material_entries.items():
                    target = material_dir / suffix
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(entry) as src, target.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
                write_paper_evidence(material_dir / "evidence.md", row)

    write_category_material_indexes(out_dir, selected, extracted_abs_dirs)


def markdown_link(label: str, path: Path | str) -> str:
    if isinstance(path, Path):
        target = path.as_posix()
    else:
        target = path
    return f"[{label}]({target})"


def write_paper_evidence(path: Path, row: PaperRow) -> None:
    d = row.data
    material_dir = path.parent
    lines = [
        f"# {d['title']}",
        "",
        f"- Paper key: `{d['paper_key']}`",
        f"- Venue: {d['venue']}",
        f"- Decision: {d['decision']}",
        f"- OpenReview: {d['forum_url']}",
        f"- Categories: {d['categories']}",
        f"- Risk tier: **{d['risk_tier']}**, score {d['risk_score']}",
        f"- Ratings: mean {d['mean_rating']}, min {d['min_rating']}",
        f"- Contribution: mean {d['mean_contribution']}, min {d['min_contribution']}",
        f"- Flags: {d['candidate_flags']}",
        f"- Incremental types: {d['incremental_types']}",
        "",
        "## Local Files",
        "",
    ]
    for filename in MATERIAL_SUFFIXES:
        file_path = material_dir / filename
        if file_path.exists():
            lines.append(f"- {markdown_link(filename, file_path.name)}")
    lines.extend(
        [
            "",
            "## Novelty / Incremental Evidence",
            "",
            d["novelty_evidence"] or "(no explicit novelty phrase hit)",
            "",
            "## A+B / Combination Evidence",
            "",
            d["combo_evidence"] or "(no explicit combination phrase hit)",
            "",
            "## Abstract",
            "",
            d["abstract"],
            "",
        ]
    )
    write_markdown(path, "\n".join(lines))


def write_category_material_indexes(
    out_dir: Path, selected: list[PaperRow], extracted_abs_dirs: dict[str, Path]
) -> None:
    category_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in selected:
        material_dir = extracted_abs_dirs.get(row.data["paper_key"])
        if material_dir is None:
            continue
        record = dict(row.data)
        rel_material_dir = Path(row.data["material_dir"])
        record["material_dir"] = rel_material_dir.as_posix()
        record["paper_pdf_path"] = (rel_material_dir / "paper.pdf").as_posix() if (material_dir / "paper.pdf").exists() else ""
        record["official_reviews_md_path"] = (
            (rel_material_dir / "official_reviews.md").as_posix()
            if (material_dir / "official_reviews.md").exists()
            else ""
        )
        record["author_replies_md_path"] = (
            (rel_material_dir / "author_replies.md").as_posix()
            if (material_dir / "author_replies.md").exists()
            else ""
        )
        for category in str(row.data["categories"]).split("; "):
            category_rows[category].append(record)

    material_fields = CSV_FIELDS + [
        "paper_pdf_path",
        "official_reviews_md_path",
        "author_replies_md_path",
    ]
    for category, records in category_rows.items():
        folder = out_dir / "materials" / "by_category" / category_folder(category)
        folder.mkdir(parents=True, exist_ok=True)
        records.sort(key=lambda r: float(r["risk_score"]), reverse=True)
        write_csv(folder / "manifest.csv", records, material_fields)
        lines = [f"# {category}", ""]
        for record in records:
            material_dir = Path("../..") / Path(record["material_dir"])
            lines.extend(
                [
                    f"## {record['paper_key']}",
                    "",
                    f"- Title: {record['title']}",
                    f"- Risk: {record['risk_tier']} / {record['risk_score']}",
                    f"- OpenReview: {record['forum_url']}",
                    f"- Material folder: {markdown_link('folder', material_dir)}",
                    f"- Evidence: {markdown_link('evidence.md', material_dir / 'evidence.md')}",
                    f"- PDF: {markdown_link('paper.pdf', material_dir / 'paper.pdf') if record['paper_pdf_path'] else 'missing'}",
                    f"- Reviews: {markdown_link('official_reviews.md', material_dir / 'official_reviews.md') if record['official_reviews_md_path'] else 'missing'}",
                    f"- Replies: {markdown_link('author_replies.md', material_dir / 'author_replies.md') if record['author_replies_md_path'] else 'missing'}",
                    "",
                ]
            )
        write_markdown(folder / "paper_links.md", "\n".join(lines))


def excerpt(text: str, max_len: int = 520) -> str:
    text = clean_space(text)
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rstrip() + "..."


def relative_material_path(out_dir: Path, row: dict[str, Any]) -> str:
    material_dir = Path(row.get("material_dir") or "")
    return material_dir.as_posix()


def write_analysis_reports(out_dir: Path, rows: list[PaperRow]) -> None:
    reports_dir = out_dir / "reports"
    category_dir = reports_dir / "category_reports"
    category_dir.mkdir(parents=True, exist_ok=True)
    for stale in category_dir.glob("*.md"):
        stale.unlink()

    selected = [
        row.data for row in rows if row.data["risk_tier"] in {"high", "medium"}
    ]
    selected.sort(key=lambda r: float(r["risk_score"]), reverse=True)

    type_counter: Counter[str] = Counter()
    for row in selected:
        for item in str(row["incremental_types"]).split("; "):
            if item:
                type_counter[item] += 1

    overview_lines = [
        "# Second-Pass Candidate Reports",
        "",
        "This layer reorganizes the high+medium candidate set by research category and by incremental-work type. The labels are heuristic and are intended for triage.",
        "",
        "## Incremental Type Counts",
        "",
    ]
    for item, count in type_counter.most_common():
        file_name = TYPE_REPORT_FILENAMES.get(item, f"{slugify(item, 64)}.md")
        overview_lines.append(f"- [{item}](type_reports/{file_name}): {count}")

    overview_lines.extend(["", "## Category Reports", ""])
    for category in CATEGORY_ORDER:
        category_rows = [
            row for row in selected if category in str(row["categories"]).split("; ")
        ]
        if not category_rows:
            continue
        high_count = sum(1 for row in category_rows if row["risk_tier"] == "high")
        medium_count = sum(1 for row in category_rows if row["risk_tier"] == "medium")
        file_name = f"{category_folder(category)}.md"
        overview_lines.append(
            f"- [{category}]({(Path('category_reports') / file_name).as_posix()}): {len(category_rows)} candidates, {high_count} high, {medium_count} medium"
        )

        lines = [
            f"# {category}",
            "",
            f"- Candidate count: {len(category_rows)}",
            f"- High risk: {high_count}",
            f"- Medium risk: {medium_count}",
            "",
            "## Top Candidates",
            "",
        ]
        for index, row in enumerate(category_rows[:REPORT_TOP_N], start=1):
            material_dir = relative_material_path(out_dir, row)
            lines.extend(
                [
                    f"### {index}. {row['title']}",
                    "",
                    f"- Paper key: `{row['paper_key']}`",
                    f"- Risk: {row['risk_tier']} / {row['risk_score']}",
                    f"- Incremental types: {row['incremental_types']}",
                    f"- Categories: {row['categories']}",
                    f"- Scores: rating mean {row['mean_rating']} min {row['min_rating']}; contribution mean {row['mean_contribution']} min {row['min_contribution']}",
                    f"- OpenReview: {row['forum_url']}",
                    f"- Material folder: {material_dir}",
                    f"- Evidence file: {Path(material_dir, 'evidence.md')}",
                    "",
                    "**Novelty evidence:** "
                    + (excerpt(str(row["novelty_evidence"])) or "(no explicit phrase hit)"),
                    "",
                    "**Combination evidence:** "
                    + (excerpt(str(row["combo_evidence"])) or "(no explicit phrase hit)"),
                    "",
                ]
            )
        write_markdown(category_dir / file_name, "\n".join(lines))

    by_type_dir = reports_dir / "type_reports"
    by_type_dir.mkdir(parents=True, exist_ok=True)
    for stale in by_type_dir.glob("*.md"):
        stale.unlink()
    for type_name in type_counter:
        type_rows = [
            row
            for row in selected
            if type_name in str(row["incremental_types"]).split("; ")
        ]
        type_rows.sort(key=lambda r: float(r["risk_score"]), reverse=True)
        file_name = TYPE_REPORT_FILENAMES.get(type_name, f"{slugify(type_name, 64)}.md")
        lines = [
            f"# {type_name}",
            "",
            f"- Candidate count: {len(type_rows)}",
            "",
            "## Top Candidates",
            "",
        ]
        for index, row in enumerate(type_rows[:REPORT_TOP_N], start=1):
            material_dir = relative_material_path(out_dir, row)
            lines.extend(
                [
                    f"### {index}. {row['title']}",
                    "",
                    f"- Paper key: `{row['paper_key']}`",
                    f"- Risk: {row['risk_tier']} / {row['risk_score']}",
                    f"- Categories: {row['categories']}",
                    f"- OpenReview: {row['forum_url']}",
                    f"- Material folder: {material_dir}",
                    "",
                    "**Evidence:** "
                    + (
                        excerpt(
                            " ".join(
                                [
                                    str(row["novelty_evidence"]),
                                    str(row["combo_evidence"]),
                                ]
                            )
                        )
                        or "(no explicit phrase hit)"
                    ),
                    "",
                ]
            )
        write_markdown(by_type_dir / file_name, "\n".join(lines))

    write_markdown(reports_dir / "overview.md", "\n".join(overview_lines))


def write_summary(out_dir: Path, rows: list[PaperRow], material_tiers: set[str], material_limit: int | None, years: set[int], focus_domains: list[str] | None, source_kind: str, domain_scope: str, per_paper_analysis: bool) -> None:
    tier_counts = Counter(str(row.data["risk_tier"]) for row in rows)
    venue_counts = Counter(str(row.data["venue"]) for row in rows)
    category_counts: Counter[str] = Counter()
    category_high: Counter[str] = Counter()
    for row in rows:
        for category in str(row.data["categories"]).split("; "):
            category_counts[category] += 1
            if row.data["risk_tier"] == "high":
                category_high[category] += 1

    high_rows = sorted(
        [row for row in rows if row.data["risk_tier"] == "high"],
        key=lambda r: float(r.data["risk_score"]),
        reverse=True,
    )[:30]

    lines = [
        "# Incremental / Low-Novelty Knowledge Base Index",
        "",
        "This is a heuristic first-pass triage over local OpenReview exports. It uses abstracts, keywords, primary areas, official reviews, and meta-reviews. Treat `risk_tier` as a candidate label, not a final judgment.",
        "",
        "## Scope",
        "",
        f"- Source kind: {source_kind}",
        f"- Domain scope: {domain_scope}",
        f"- Years: {sorted(years)}",
        f"- Focus domains: {focus_domains or ['all']}",
        f"- Total papers indexed: {len(rows)}",
        f"- Venue counts: {dict(venue_counts)}",
        f"- Risk tiers: {dict(tier_counts)}",
        f"- Extracted material tiers: {sorted(material_tiers)}",
        f"- Extraction limit: {material_limit if material_limit is not None else 'none'}",
        f"- Per-paper analysis: {'enabled' if per_paper_analysis else 'disabled'}",
        "",
        "## Output Files",
        "",
        "- `index/incremental_all_index.csv`: all indexed papers.",
        "- `index/incremental_all_index.jsonl`: same rows in JSONL.",
        "- `index/incremental_low_novelty_candidates.csv`: high + medium candidate rows.",
        "- `index/incremental_core_candidates.csv`: high + medium rows with explicit low-novelty, incremental, minor-extension, or A+B/C labels.",
        "- `index/incremental_high_risk_candidates.csv`: high risk rows only.",
        "- `index/incremental_category_summary.csv`: category counts by tier.",
        "- `index/incremental_category_type_matrix.csv`: category-by-incremental-type counts.",
        "- `materials/_by_paper/`: extracted PDFs/reviews/replies/metadata for selected material tiers.",
        "- `materials/by_category/<category>/`: per-category manifests and links to extracted materials.",
        "- `analysis/per_paper/<paper_key>/`: per-paper PDF/review/reply analysis and intermediate artifacts.",
        "- `analysis/per_paper_analysis_manifest.jsonl`: machine-readable per-paper analysis manifest.",
        "- `reports/per_paper_analysis_index.md`: human-readable per-paper analysis index.",
        "- `reports/overview.md`: second-pass category/type reports over high+medium candidates.",
        "",
        "## Top Categories",
        "",
    ]
    for category, count in category_counts.most_common(30):
        lines.append(f"- {category}: {count} total, {category_high[category]} high-risk candidates")

    lines.extend(["", "## Highest-Scoring High-Risk Candidates", ""])
    for row in high_rows:
        d = row.data
        lines.append(
            f"- `{d['paper_key']}` | score {d['risk_score']} | {d['categories']} | {d['title']}"
        )

    lines.extend(
        [
            "",
            "## Heuristic Notes",
            "",
            "- `novelty_score` is driven by review/meta-review phrases such as incremental, limited novelty, lack of novelty, minor extension, simple combination, and limited contribution.",
            "- `combo_score` is driven by title/abstract/review signals such as combine, integrate, hybrid, unified, plug-and-play, variant, extension, and literal A+B style expressions.",
            "- `risk_tier=high` requires explicit novelty/incremental concern or low contribution scores coupled with combination signals.",
            "- Multi-label categories are keyword/rule based and intentionally broad.",
            "",
        ]
    )
    write_markdown(out_dir / "summary.md", "\n".join(lines))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build an incremental/low-novelty knowledge base from accepted-paper zip exports."
    )
    parser.add_argument("--corpus-source", "--zip-dir", dest="zip_dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--source-kind", default="iclr-openreview", help="Corpus/source convention. Default: iclr-openreview.")
    parser.add_argument("--domain-scope", default="computer-science", help="Broad domain assumption. Default: computer-science.")
    parser.add_argument("--year", dest="years", action="append", type=int, default=None, help="Year to include. Repeat for multiple years.")
    parser.add_argument("--focus-domains", nargs="*", default=None, help="Optional domain/category/keyword filters.")
    parser.add_argument(
        "--material-tier",
        action="append",
        choices=["high", "medium", "low"],
        default=None,
        help="Risk tier to extract into material folders. Repeat for multiple tiers. Default: high and medium.",
    )
    parser.add_argument(
        "--material-limit",
        type=int,
        default=None,
        help="Optional max number of selected material rows to extract, after sorting by risk_score.",
    )
    parser.add_argument(
        "--no-extract",
        action="store_true",
        help="Only write index tables; do not extract PDFs/reviews/replies.",
    )
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=DEFAULT_STATE_DIR,
        help="Directory for initialization state files. Defaults to the current project's .delta-contribution-reframer/state directory.",
    )
    parser.add_argument(
        "--skip-per-paper-analysis",
        action="store_true",
        help="Skip per-paper PDF/review/reply analysis. Use only for indexing dry runs, not complete initialization.",
    )
    return parser.parse_args()

def update_initialization_state(state_dir: Path, out_dir: Path, rows: list[PaperRow], years: set[int], focus_domains: list[str] | None, material_tiers: set[str], source_kind: str, domain_scope: str, per_paper_analysis: bool) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now().isoformat(timespec="seconds")
    knowledge_state = {
        "schema_version": "1.0",
        "knowledge_available": bool(rows),
        "resources": [
            {"path": str((out_dir / "index" / "incremental_all_index.csv").as_posix()), "kind": "all_index", "status": "available"},
            {"path": str((out_dir / "index" / "incremental_low_novelty_candidates.csv").as_posix()), "kind": "candidate_index", "status": "available"},
            {"path": str((out_dir / "reports" / "overview.md").as_posix()), "kind": "overview_report", "status": "available"},
            {"path": str((out_dir / "materials" / "_by_paper").as_posix()), "kind": "extracted_materials", "status": "available" if material_tiers else "not_extracted"},
        ],
        "paper_count": len(rows),
        "source_kind": source_kind,
        "domain_scope": domain_scope,
        "per_paper_analysis_required": per_paper_analysis,
        "updated_at": now,
    }
    initialization_state = {
        "schema_version": "1.0",
        "initialized": bool(rows),
        "status": "ready" if rows else "empty_result",
        "reason": "Incremental knowledge base generated from configured corpus." if rows else "No papers matched the configured filters.",
        "focus_domains": focus_domains or [],
        "years": sorted(str(year) for year in years),
        "source_kind": source_kind,
        "domain_scope": domain_scope,
        "per_paper_analysis_required": per_paper_analysis,
        "per_paper_analysis_complete": False,
        "corpus_source": "user-provided corpus source",
        "requires_user_input_when_empty": ["focus_domains", "years", "corpus_source"],
        "updated_at": now,
    }
    (state_dir / "knowledge_state.json").write_text(json.dumps(knowledge_state, ensure_ascii=False, indent=2), encoding="utf-8")
    (state_dir / "initialization_state.json").write_text(json.dumps(initialization_state, ensure_ascii=False, indent=2), encoding="utf-8")


def run_per_paper_analysis(out_dir: Path, state_dir: Path) -> None:
    script = Path(__file__).resolve().with_name("analyze_extracted_papers.py")
    subprocess.run(
        [
            sys.executable,
            str(script),
            "--out-dir",
            str(out_dir),
            "--state-dir",
            str(state_dir),
        ],
        check=True,
    )


def main() -> None:
    args = parse_args()
    zip_dir = args.zip_dir.resolve()
    out_dir = args.out_dir.resolve()
    state_dir = args.state_dir.resolve()
    material_tiers = set(args.material_tier or ["high", "medium"])

    if not zip_dir.exists():
        raise SystemExit(f"corpus source does not exist: {zip_dir}")

    years = set(args.years or [])
    if not years:
        raise SystemExit("At least one --year is required.")

    rows = build_rows(zip_dir, years, args.focus_domains)
    out_dir.mkdir(parents=True, exist_ok=True)
    index_dir = out_dir / "index"
    all_dicts = [row.data for row in rows]
    candidate_dicts = [
        row.data for row in rows if row.data["risk_tier"] in {"high", "medium"}
    ]
    core_candidate_dicts = [
        row.data for row in rows if is_core_incremental_candidate(row.data)
    ]
    high_dicts = [row.data for row in rows if row.data["risk_tier"] == "high"]

    write_csv(index_dir / "incremental_all_index.csv", all_dicts, CSV_FIELDS)
    write_jsonl(index_dir / "incremental_all_index.jsonl", all_dicts)
    write_csv(index_dir / "incremental_low_novelty_candidates.csv", candidate_dicts, CSV_FIELDS)
    write_csv(index_dir / "incremental_core_candidates.csv", core_candidate_dicts, CSV_FIELDS)
    write_csv(index_dir / "incremental_high_risk_candidates.csv", high_dicts, CSV_FIELDS)
    write_category_summaries(out_dir, rows)
    write_category_type_matrix(out_dir, rows)
    write_analysis_reports(out_dir, rows)

    if not args.no_extract:
        extract_materials(out_dir, rows, material_tiers, args.material_limit)

    per_paper_analysis_enabled = not args.no_extract and not args.skip_per_paper_analysis
    write_summary(
        out_dir,
        rows,
        material_tiers if not args.no_extract else set(),
        args.material_limit,
        years,
        args.focus_domains,
        args.source_kind,
        args.domain_scope,
        per_paper_analysis_enabled,
    )
    update_initialization_state(
        state_dir,
        out_dir,
        rows,
        years,
        args.focus_domains,
        material_tiers if not args.no_extract else set(),
        args.source_kind,
        args.domain_scope,
        per_paper_analysis_enabled,
    )
    if per_paper_analysis_enabled:
        run_per_paper_analysis(out_dir, state_dir)

    print(f"indexed_papers={len(rows)}")
    print(f"high={len(high_dicts)} medium={len(candidate_dicts)-len(high_dicts)} low={len(rows)-len(candidate_dicts)}")
    print(f"out_dir={out_dir}")

if __name__ == "__main__":
    main()
