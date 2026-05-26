#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any


PATTERNS = {
    "low_novelty_or_incremental": [r"\bincremental\b", r"limited novelty", r"minor extension", r"simple extension"],
    "combination_or_coupling": [r"\bcombine", r"\bintegrat", r"\bhybrid\b", r"\bcoupl", r"\bunif"],
    "transfer_or_adaptation": [r"\badapt", r"\btransfer", r"\bextend", r"based on", r"builds? on"],
    "constraint_anchor": [r"heterogeneity", r"label scarcity", r"unlabeled", r"communication", r"privacy", r"cost", r"non[- ]iid", r"decentralized"],
    "evidence_pressure": [r"ablation", r"baseline", r"benchmark", r"evaluation", r"comparison", r"runtime", r"communication"],
}


QUALITY_REPORT_SECTIONS = [
    "0. 语言与证据约定 / Language And Evidence Contract",
    "1. 精读证据底座 / Deep Evidence Base",
    "2. 强包装诊断 / Strong Packaging Diagnosis",
    "2.5 潜在贡献挖掘 / Latent Contribution Mining",
    "2.6 顶会级故事重构 / Top-Conference Story Reconstruction",
    "3. 故事路线候选板 / Story Route Candidate Board",
    "4. Reviewer Attack Preplay",
    "5. 原文触发问题定位 / Manuscript Trigger Localization",
    "6. 分层修改建议 / Tiered Revision Plan",
    "7. Rebuttal 模式库 / Rebuttal Pattern Library",
    "8. 匿名案例附录 / Anonymous Case Appendix",
    "9. 残余风险 / Residual Risk",
]


STORY_ROUTE_COLUMNS = [
    "Rank",
    "Story route",
    "Novelty defense",
    "Evidence fit",
    "A+B/C resistance",
    "Baseline control",
    "Mechanism control",
    "Cost/reproducibility control",
    "Rewrite cost",
    "New-experiment pressure",
    "Best use",
]


ATTACK_PREPLAY_COLUMNS = [
    "Reviewer attack",
    "Why reviewer will ask",
    "Manuscript trigger",
    "Strong defense posture",
    "No-new-experiment repair",
]


MANUSCRIPT_TRIGGER_COLUMNS = [
    "Manuscript area",
    "Current strength",
    "Weak trigger",
    "Risk created",
    "Concrete repair",
]


REVISION_PLAN_COLUMNS = [
    "Action",
    "Manuscript location",
    "Evidence reused or needed",
    "Reviewer-defense purpose",
    "Ready-to-paste English if applicable",
]


REBUTTAL_PATTERN_COLUMNS = [
    "Defense posture",
    "Submit-ready English",
    "Risky wording to avoid",
    "Why risky",
]


RESIDUAL_RISK_COLUMNS = [
    "Claim boundary",
    "Safe wording",
    "Unsafe wording",
    "Evidence needed to strengthen",
]


TOP_CONFERENCE_RECONSTRUCTION_COLUMNS = [
    "Output",
    "Plain-language purpose",
    "What to write",
    "Evidence anchor",
    "Boundary",
]


CONTRIBUTION_LADDER_COLUMNS = [
    "Level",
    "Plain-language meaning",
    "Paper-ready claim",
    "Evidence anchor",
    "Risk if overclaimed",
]


LATENT_CONTRIBUTION_COLUMNS = [
    "Candidate contribution",
    "Evidence label",
    "Plain-language explanation",
    "Evidence anchor",
    "Safe use",
    "Unsafe overclaim",
]


PLAIN_LANGUAGE_ROUTE_COLUMNS = [
    "Route",
    "Plain-language meaning",
    "Concrete example or analogy",
    "Why this helps reviewers",
    "Where to use it",
    "When unsafe",
]


def clean(text: str) -> str:
    text = re.sub(r"\r\n?", "\n", text or "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf_text(pdf_path: Path) -> tuple[str, str, str, list[dict[str, Any]]]:
    try:
        import fitz  # type: ignore

        doc = fitz.open(pdf_path)
        chunks: list[str] = []
        pages: list[dict[str, Any]] = []
        offset = 0
        for index, page in enumerate(doc):
            page_text = page.get_text("text") or ""
            chunks.append(page_text)
            pages.append({"page": index + 1, "text_chars": len(page_text), "start_char": offset})
            offset += len(page_text)
        text = clean("\n\n".join(chunks))
        return "ok", text, "", pages
    except Exception as fitz_exc:
        fitz_error = str(fitz_exc)
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(pdf_path))
        chunks = [(page.extract_text() or "") for page in reader.pages]
        pages = []
        offset = 0
        for index, page_text in enumerate(chunks):
            pages.append({"page": index + 1, "text_chars": len(page_text), "start_char": offset})
            offset += len(page_text)
        text = clean("\n\n".join(chunks))
        return "ok", text, "", pages
    except Exception as pypdf_exc:
        return "pdf_text_extraction_failed", "", f"fitz: {fitz_error}; pypdf: {pypdf_exc}", []


def snippets(text: str, patterns: list[str], limit: int = 8) -> list[str]:
    out: list[str] = []
    for sent in re.split(r"(?<=[.!?。！？])\s+", clean(text)):
        sent = clean(sent)
        if len(sent) < 20:
            continue
        if any(re.search(pattern, sent, flags=re.IGNORECASE) for pattern in patterns):
            out.append(sent[:420])
        if len(out) >= limit:
            break
    return out


def load_casebook(skill_dir: Path) -> list[dict[str, Any]]:
    path = skill_dir / "references" / "anonymous_casebook.jsonl"
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def default_overlay_dir(skill_name: str) -> Path:
    return Path.cwd() / f".{skill_name}"


def safe_file_stem(value: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-._")
    return stem or "target-paper"


def default_public_report_path(pdf_path: Path) -> Path:
    return Path.cwd() / f"{safe_file_stem(pdf_path.stem)}_reframing_report.md"


def display_path(path: Path) -> str:
    return path.resolve().as_posix()


def write_scaffold(out_dir: Path, record: dict[str, Any], recommended: list[str]) -> str:
    lines = [
        "# Target Paper Incremental Reframing Report Scaffold",
        "",
        "This scaffold is not the final analysis by itself. The final report must satisfy `references/base_delta/contract_target_report_quality.md`.",
        "",
        "Required alignment: `delta-contribution-reframer` target-paper workflow.",
        "",
        "## 0. 语言与证据约定 / Language And Evidence Contract",
        "",
        "- Use Chinese for diagnosis, reasoning, ranking, risk analysis, anonymous analogies, and revision planning.",
        "- Use English only for manuscript-facing and rebuttal-ready snippets.",
        f"- PDF: `{record['pdf_name']}`",
        f"- PDF status: `{record['pdf_status']}`",
        f"- PDF text chars: {record['pdf_text_chars']}",
        f"- Review status: `{record['reviews_status']}`",
        f"- Reply status: `{record['replies_status']}`",
        f"- Review attack mode: `{record['review_attack_mode']}`",
        "- Treat target-paper PDF evidence as `new-paper-derived`.",
        "- Treat packaged casebook entries as `base-corpus analogy` only.",
        "- Readability rule: explain hard ideas in plain Chinese first, then give the technical thesis, concrete example/analogy, evidence anchor, and boundary.",
        "- Do not reduce content for readability. Add explanation around tables instead of deleting required analysis.",
        "",
        "## 1. 精读证据底座 / Deep Evidence Base",
        "",
        "Write a compact but specific evidence base. Do not summarize the paper generically. Extract the problem chain, target regime, broken old assumptions, method modules, key tables/figures/appendix anchors, and claim boundaries from the PDF.",
        "",
        "Minimum content:",
        "",
        "- What the paper is really trying to repair under its constrained regime.",
        "- Why the current surface framing may look incremental or like A+B/C.",
        "- Which replacement mechanisms make the contribution stronger than a module list.",
        "- Which evidence anchors support the stronger framing, and which anchors only support weaker claims.",
        "- Which attractive larger claims must remain future-boundary hooks.",
        "",
        "| Unavailable ideal mechanism or old assumption | Target-paper replacement mechanism | Evidence anchor | Evidence status |",
        "|---|---|---|---|",
        "| TODO | TODO | TODO | TODO |",
        "",
        "## 2. 强包装诊断 / Strong Packaging Diagnosis",
        "",
        "Diagnose the weak surface delta first, then recover the stronger actual delta. Explain why the weak framing invites novelty, A+B/C, mechanism, baseline, cost, privacy/safety, scope, or reproducibility attacks.",
        "",
        "```text",
        "Weak surface framing: TODO",
        "Why reviewers may read it as incremental: TODO",
        "Contribution layer 1 - setting/regime: TODO",
        "Contribution layer 2 - mechanism/coupling/interface: TODO",
        "Contribution layer 3 - evidence system: TODO",
        "Stronger actual contribution: TODO",
        "Recommended core phrase: TODO",
        "```",
        "",
        "## 2.5 潜在贡献挖掘 / Latent Contribution Mining",
        "",
        "Mine what is already supported by the PDF but not fully packaged by the manuscript. Use plain language so the author understands why each point is real and how far it can go.",
        "",
        "| " + " | ".join(LATENT_CONTRIBUTION_COLUMNS) + " |",
        "|" + "|".join("---" for _ in LATENT_CONTRIBUTION_COLUMNS) + "|",
        "| TODO | paper-explicit | TODO | TODO | abstract / intro / contribution | TODO |",
        "| TODO | latent-but-supported | TODO | TODO | method / experiment / rebuttal | TODO |",
        "| TODO | story-level reframing | TODO | TODO | contribution / related work / figure | TODO |",
        "| TODO | future-boundary hook | TODO | TODO | motivation / discussion only | TODO |",
        "",
        "## 2.6 顶会级故事重构 / Top-Conference Story Reconstruction",
        "",
        "This section turns the diagnosis into concrete author-facing outputs. Explain each output in simple words before giving paper-ready text.",
        "",
        "### 2.6.1 Problem Equation",
        "",
        "Use the form: `old assumption becomes unavailable + target constraint appears + naive method fails + this paper repairs the failure by TODO`.",
        "",
        "```text",
        "Plain-language version: TODO",
        "Paper-ready problem equation: TODO",
        "Evidence anchor: TODO",
        "Boundary: TODO",
        "```",
        "",
        "### 2.6.2 Contribution Ladder",
        "",
        "| " + " | ".join(CONTRIBUTION_LADDER_COLUMNS) + " |",
        "|" + "|".join("---" for _ in CONTRIBUTION_LADDER_COLUMNS) + "|",
        "| Component level | TODO | TODO | TODO | TODO |",
        "| Mechanism/coupling level | TODO | TODO | TODO | TODO |",
        "| Problem/regime level | TODO | TODO | TODO | TODO |",
        "| Evidence-system level | TODO | TODO | TODO | TODO |",
        "| Future-boundary level | TODO | TODO | TODO | TODO |",
        "",
        "### 2.6.3 Concrete Rewrite Outputs",
        "",
        "| " + " | ".join(TOP_CONFERENCE_RECONSTRUCTION_COLUMNS) + " |",
        "|" + "|".join("---" for _ in TOP_CONFERENCE_RECONSTRUCTION_COLUMNS) + "|",
        "| Abstract rewrite | TODO | TODO | TODO | TODO |",
        "| Introduction framing | TODO | TODO | TODO | TODO |",
        "| Contribution bullets | TODO | TODO | TODO | TODO |",
        "| Related-work boundary | TODO | TODO | TODO | TODO |",
        "| Method overview | TODO | TODO | TODO | TODO |",
        "| Figure/caption direction | TODO | TODO | TODO | TODO |",
        "",
        "## 3. 故事路线候选板 / Story Route Candidate Board",
        "",
        "Provide six ranked route slots by default. If the PDF evidence cannot support six, explicitly say which slots are unavailable and why. Do not collapse to a single route before comparing tradeoffs.",
        "",
        "### 3.1 推荐排序与维度比较 / Recommended Ranking And Dimension Comparison",
        "",
        "| " + " | ".join(STORY_ROUTE_COLUMNS) + " |",
        "|" + "|".join("---" for _ in STORY_ROUTE_COLUMNS) + "|",
        "| 1 | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO | default main line |",
        "| 2 | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO | novelty / related-work defense |",
        "| 3 | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO | method overview / Figure 1 |",
        "| 4 | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO | experiment organization |",
        "| 5 | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO | limitation / cost paragraph |",
        "| 6 | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO | discussion / future-boundary hook |",
        "",
        "For each route, include plain-language meaning, construction reason, core thesis, usable evidence, paper locations to rewrite, risk boundary, anonymous analogy if available, and at least one English manuscript or rebuttal snippet.",
        "",
        "### 3.1b 路线读法表 / Plain-Language Route Explainer",
        "",
        "Use this table to make the story routes less mentally expensive. Do not replace the technical comparison table; add this explanation layer on top of it.",
        "",
        "| " + " | ".join(PLAIN_LANGUAGE_ROUTE_COLUMNS) + " |",
        "|" + "|".join("---" for _ in PLAIN_LANGUAGE_ROUTE_COLUMNS) + "|",
        "| Option 1 | TODO | TODO | TODO | TODO | TODO |",
        "| Option 2 | TODO | TODO | TODO | TODO | TODO |",
        "| Option 3 | TODO | TODO | TODO | TODO | TODO |",
        "| Option 4 | TODO | TODO | TODO | TODO | TODO |",
        "| Option 5 | TODO | TODO | TODO | TODO | TODO |",
        "| Option 6 | TODO | TODO | TODO | TODO | TODO |",
        "",
        "### 3.2 Option 1: 默认主线 / Default Main Route",
        "",
        "- Plain-language meaning: TODO",
        "- Construction reason: TODO",
        "- Core thesis: TODO",
        "- Concrete example or analogy: TODO",
        "- Rewrite targets: abstract / contribution / method overview / figure caption / limitation / rebuttal as applicable.",
        "- Evidence anchors: TODO",
        "- Boundary: TODO",
        "",
        "```text",
        "Ready-to-paste English: TODO",
        "```",
        "",
        "### 3.3 Option 2: 破损假设或问题契约主线 / Broken-Assumption Or Problem-Contract Route",
        "",
        "- Plain-language meaning: TODO",
        "- Construction reason: TODO",
        "- Core thesis: TODO",
        "- Concrete example or analogy: TODO",
        "- Rewrite targets: TODO",
        "- Evidence anchors: TODO",
        "- Boundary: TODO",
        "",
        "```text",
        "Ready-to-paste English: TODO",
        "```",
        "",
        "### 3.4 Option 3: 缺失信号 / 压力到机制主线 / Missing-Signal / Pressure-To-Mechanism Route",
        "",
        "- Plain-language meaning: TODO",
        "- Construction reason: TODO",
        "- Core thesis: TODO",
        "- Concrete example or analogy: TODO",
        "- Rewrite targets: method overview / framework figure / component explanation.",
        "- Evidence anchors: TODO",
        "- Boundary: TODO",
        "",
        "| Missing signal or pressure | Failure in target regime | Target-paper replacement | Evidence |",
        "|---|---|---|---|",
        "| TODO | TODO | TODO | TODO |",
        "",
        "```text",
        "Ready-to-paste English: TODO",
        "```",
        "",
        "### 3.5 Option 4: 证据系统主线 / Evidence-System Route",
        "",
        "- Plain-language meaning: TODO",
        "- Construction reason: TODO",
        "- Core thesis: TODO",
        "- Concrete example or analogy: TODO",
        "- Rewrite targets: experiment roadmap / ablation discussion / appendix pointer.",
        "- Evidence anchors: TODO",
        "- Boundary: TODO",
        "",
        "```text",
        "Ready-to-paste English: TODO",
        "```",
        "",
        "### 3.6 Option 5: 质量-成本 / 部署边界主线 / Quality-Cost / Deployment-Boundary Route",
        "",
        "- Plain-language meaning: TODO",
        "- Construction reason: TODO",
        "- Core thesis: TODO",
        "- Concrete example or analogy: TODO",
        "- Rewrite targets: limitation / discussion / rebuttal.",
        "- Evidence anchors: TODO",
        "- Boundary: TODO",
        "",
        "```text",
        "Ready-to-paste English: TODO",
        "```",
        "",
        "### 3.7 Option 6: 未来科学边界主线 / Future Scientific Boundary Route",
        "",
        "- Plain-language meaning: TODO",
        "- Construction reason: TODO",
        "- Core thesis: TODO",
        "- Concrete example or analogy: TODO",
        "- Rewrite targets: introduction hook / discussion only; do not put unsupported future-boundary claims into main contribution.",
        "- Evidence anchors: TODO",
        "- Boundary: TODO",
        "",
        "```text",
        "Ready-to-paste English: TODO",
        "```",
        "",
        "### 3.8 推荐组合 / Recommended Combination",
        "",
        "- Default main route: TODO",
        "- Method/Figure route to combine: TODO",
        "- Related-work/baseline-defense route to combine: TODO",
        "- Experiment-organization route to combine: TODO",
        "- Limitation/discussion route to combine: TODO",
        "- Minimum Tier 0 combination if page budget is tight: TODO",
        "",
        "## 4. Reviewer Attack Preplay",
        "",
        "Use `simulated-review` labels unless real reviews are supplied. Cover novelty/incrementality, A+B/C combination, baseline fairness, mechanism evidence, cost/scalability, scope, and reproducibility when relevant.",
        "",
        "| " + " | ".join(ATTACK_PREPLAY_COLUMNS) + " |",
        "|" + "|".join("---" for _ in ATTACK_PREPLAY_COLUMNS) + "|",
        "| `simulated-review` novelty / incrementality | TODO | TODO | TODO | TODO |",
        "| `simulated-review` A+B/C combination | TODO | TODO | TODO | TODO |",
        "| `simulated-review` baseline fairness | TODO | TODO | TODO | TODO |",
        "| `simulated-review` mechanism evidence | TODO | TODO | TODO | TODO |",
        "| `simulated-review` cost / scalability | TODO | TODO | TODO | TODO |",
        "| `simulated-review` privacy/safety boundary if relevant | TODO | TODO | TODO | TODO |",
        "| `simulated-review` scope / generalization | TODO | TODO | TODO | TODO |",
        "| `simulated-review` reproducibility | TODO | TODO | TODO | TODO |",
        "",
        "## 5. 原文触发问题定位 / Manuscript Trigger Localization",
        "",
        "Map each likely attack back to exact manuscript triggers: overstrong claims, missing related-work boundaries, missing diagnostics, weak ablation framing, unclear comparison contracts, unsupported privacy/safety or cost claims, or unsupported generalization.",
        "",
        "First state what the current manuscript already does well, then state where the writing creates avoidable reviewer attack surface.",
        "",
        "| " + " | ".join(MANUSCRIPT_TRIGGER_COLUMNS) + " |",
        "|" + "|".join("---" for _ in MANUSCRIPT_TRIGGER_COLUMNS) + "|",
        "| Abstract / title | TODO | TODO | TODO | TODO |",
        "| Contribution bullets | TODO | TODO | TODO | TODO |",
        "| Related work / problem setup | TODO | TODO | TODO | TODO |",
        "| Method overview / Figure 1 | TODO | TODO | TODO | TODO |",
        "| Experiments / ablations | TODO | TODO | TODO | TODO |",
        "| Limitation / discussion | TODO | TODO | TODO | TODO |",
        "",
        "## 6. 分层修改建议 / Tiered Revision Plan",
        "",
        "### Tier 0: No New Experiments",
        "",
        "| " + " | ".join(REVISION_PLAN_COLUMNS) + " |",
        "|" + "|".join("---" for _ in REVISION_PLAN_COLUMNS) + "|",
        "| TODO | TODO | existing PDF evidence only | TODO | TODO |",
        "",
        "### Tier 1: Reuse Existing Materials",
        "",
        "| " + " | ".join(REVISION_PLAN_COLUMNS) + " |",
        "|" + "|".join("---" for _ in REVISION_PLAN_COLUMNS) + "|",
        "| TODO | TODO | cached logs / appendix / existing curves / existing implementation details | TODO | TODO |",
        "",
        "### Tier 2: New Evidence",
        "",
        "| " + " | ".join(REVISION_PLAN_COLUMNS) + " |",
        "|" + "|".join("---" for _ in REVISION_PLAN_COLUMNS) + "|",
        "| TODO | TODO | new diagnostic / new baseline / new scale / new safety-cost check if truly needed | TODO | TODO |",
        "",
        "## 7. Rebuttal 模式库 / Rebuttal Pattern Library",
        "",
        "Write rebuttal-safe English snippets. Keep each snippet bounded by the evidence ledger. For every pattern, include defense posture, submit-ready text, risky wording to avoid, and why the risky wording would weaken the paper.",
        "",
        "### Novelty / Incrementality",
        "",
        "| " + " | ".join(REBUTTAL_PATTERN_COLUMNS) + " |",
        "|" + "|".join("---" for _ in REBUTTAL_PATTERN_COLUMNS) + "|",
        "| TODO | TODO | TODO | TODO |",
        "",
        "### A+B/C Combination",
        "",
        "| " + " | ".join(REBUTTAL_PATTERN_COLUMNS) + " |",
        "|" + "|".join("---" for _ in REBUTTAL_PATTERN_COLUMNS) + "|",
        "| TODO | TODO | TODO | TODO |",
        "",
        "### Baseline Fairness",
        "",
        "| " + " | ".join(REBUTTAL_PATTERN_COLUMNS) + " |",
        "|" + "|".join("---" for _ in REBUTTAL_PATTERN_COLUMNS) + "|",
        "| TODO | TODO | TODO | TODO |",
        "",
        "### Mechanism Evidence",
        "",
        "| " + " | ".join(REBUTTAL_PATTERN_COLUMNS) + " |",
        "|" + "|".join("---" for _ in REBUTTAL_PATTERN_COLUMNS) + "|",
        "| TODO | TODO | TODO | TODO |",
        "",
        "### Cost / Reproducibility",
        "",
        "| " + " | ".join(REBUTTAL_PATTERN_COLUMNS) + " |",
        "|" + "|".join("---" for _ in REBUTTAL_PATTERN_COLUMNS) + "|",
        "| TODO | TODO | TODO | TODO |",
        "",
        "## 8. 匿名案例附录 / Anonymous Case Appendix",
        "",
    ]
    lines.extend(f"- `{label}`" for label in recommended if label)
    lines.extend(
        [
            "",
            "Use these only as analogies, never as facts about the target paper.",
            "",
            "| Case or lens | Original weak pattern | Effective packaging move | How to borrow for this target paper | Boundary |",
            "|---|---|---|---|---|",
            "| TODO | TODO | TODO | TODO | TODO |",
            "",
            "## 9. 残余风险 / Residual Risk",
            "",
            "List what remains weak after Tier 0/Tier 1 edits, and what would require new experiments, external evidence, or claim softening. Preserve safe claim boundaries explicitly.",
            "",
            "| " + " | ".join(RESIDUAL_RISK_COLUMNS) + " |",
            "|" + "|".join("---" for _ in RESIDUAL_RISK_COLUMNS) + "|",
            "| Mechanism | supported by evidence tier TODO | proves the mechanism | TODO |",
            "| Privacy/safety if relevant | no raw-data sharing / bounded safety claim TODO | formal guarantee without proof | TODO |",
            "| Cost | quality-cost tradeoff / reported schedule TODO | negligible overhead without logs | TODO |",
            "| Generalization | evaluated regime TODO | universal claim | TODO |",
            "| Reproducibility | implementation detail TODO | fully reproducible without release/protocol | TODO |",
            "",
        ]
    )
    text = "\n".join(lines)
    (out_dir / "full_reframing_report_scaffold.md").write_text(text, encoding="utf-8")
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description="Pre-pass for target PDF analysis. Final report must follow delta-contribution-reframer workflow.")
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--skill-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--public-report", type=Path, default=None)
    parser.add_argument("--no-public-scaffold", action="store_true")
    parser.add_argument("--reviews", type=Path, default=None)
    parser.add_argument("--replies", type=Path, default=None)
    args = parser.parse_args()

    skill_dir = args.skill_dir.resolve()
    manifest = json.loads((skill_dir / "references" / "knowledge_manifest.json").read_text(encoding="utf-8-sig"))
    skill_name = manifest.get("skill_name") or skill_dir.name
    out_dir = args.out_dir or (default_overlay_dir(skill_name) / "reports" / args.pdf.stem)
    out_dir.mkdir(parents=True, exist_ok=True)
    public_report = None if args.no_public_scaffold else (args.public_report or default_public_report_path(args.pdf))

    pdf_status, text, pdf_error, page_rows = extract_pdf_text(args.pdf)
    review_text = args.reviews.read_text(encoding="utf-8", errors="replace") if args.reviews and args.reviews.exists() else ""
    reply_text = args.replies.read_text(encoding="utf-8", errors="replace") if args.replies and args.replies.exists() else ""
    combined = "\n\n".join([text, review_text, reply_text])
    hits = {name: snippets(combined, pats) for name, pats in PATTERNS.items()}

    casebook = load_casebook(skill_dir)
    recommended = []
    for card in casebook[:12]:
        label = card.get("case_label", "")
        if "combination" in label and hits["combination_or_coupling"]:
            recommended.append(label)
        elif "incremental" in label and hits["low_novelty_or_incremental"]:
            recommended.append(label)
        elif "transfer" in label and hits["transfer_or_adaptation"]:
            recommended.append(label)
    if not recommended:
        recommended = [card.get("case_label", "") for card in casebook[:3]]

    source_ledger = {
        "pdf": str(args.pdf.resolve()),
        "pdf_name": args.pdf.name,
        "reviews": str(args.reviews.resolve()) if args.reviews else None,
        "replies": str(args.replies.resolve()) if args.replies else None,
        "skill_dir": str(skill_dir),
        "skill_name": skill_name,
    }
    record = {
        "schema_version": "2.0",
        "workflow_alignment": "delta-contribution-reframer",
        "prepass_only": True,
        "final_report_required": True,
        "required_final_sections": QUALITY_REPORT_SECTIONS,
        "report_quality_contract": "references/base_delta/contract_target_report_quality.md",
        "report_playbook_dependencies": [
            "references/report_playbook/reader_friendly_reporting.md",
            "references/report_playbook/positive_reframing_patterns.md",
            "references/report_playbook/latent_contribution_mining.md",
            "references/report_playbook/reviewer_attack_taxonomy.md",
            "references/report_playbook/rebuttal_pattern_library.md",
        ],
        "analyzed_at": dt.datetime.now().isoformat(timespec="seconds"),
        "pdf_name": args.pdf.name,
        "pdf_status": pdf_status,
        "pdf_error": pdf_error,
        "pdf_text_chars": len(text),
        "reviews_status": "available" if review_text else "missing / not reported",
        "replies_status": "available" if reply_text else "missing / not reported",
        "review_attack_mode": "real-review" if review_text else "simulated-review",
        "evidence_label": "new-paper-derived",
        "source_ledger": source_ledger,
        "pattern_hits": hits,
        "recommended_base_case_labels": recommended,
    }

    (out_dir / "pdf_text.txt").write_text(text, encoding="utf-8", errors="replace")
    (out_dir / "page_index.json").write_text(json.dumps({"pdf_status": pdf_status, "pages": page_rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "source_ledger.json").write_text(json.dumps(source_ledger, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "analysis_record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Target Paper Pre-Pass",
        "",
        "This is not the final reframing report. The final response must follow `references/base_delta/workflow_target_paper_reframing.md`.",
        "",
        f"- PDF: `{args.pdf.name}`",
        f"- PDF status: `{pdf_status}`",
        f"- Review status: `{record['reviews_status']}`",
        f"- Reply status: `{record['replies_status']}`",
        f"- Review attack mode: `{record['review_attack_mode']}`",
        "",
        "## Pattern Hits",
        "",
    ]
    for name, values in hits.items():
        lines.extend([f"### {name}", ""])
        lines.extend(f"- {value}" for value in values) if values else lines.append("- missing / not explicit")
        lines.append("")
    lines.extend(["## Base Case Analogies", ""])
    lines.extend(f"- `{label}`" for label in recommended if label)
    lines.extend(["", "These are analogies from packaged anonymous base knowledge, not evidence about the new paper.", ""])
    lines.extend(["## Required Next Step", "", "Produce the full target-paper report using `full_reframing_report_scaffold.md`, `references/base_delta/contract_target_report_quality.md`, and `references/report_playbook/reader_friendly_reporting.md`. Do not answer with the pre-pass alone.", ""])
    (out_dir / "analysis.md").write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    scaffold_text = write_scaffold(out_dir, record, recommended)
    public_report_created = False
    if public_report:
        public_report.parent.mkdir(parents=True, exist_ok=True)
        if not public_report.exists():
            public_report.write_text(scaffold_text, encoding="utf-8")
            public_report_created = True
    print(
        json.dumps(
            {
                "out_dir": display_path(out_dir),
                "prepass_record": display_path(out_dir / "analysis_record.json"),
                "full_report_scaffold": display_path(out_dir / "full_reframing_report_scaffold.md"),
                "public_report": display_path(public_report) if public_report else None,
                "public_report_created": public_report_created,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
