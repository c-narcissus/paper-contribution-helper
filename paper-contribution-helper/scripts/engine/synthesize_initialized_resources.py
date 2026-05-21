#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from common import default_references_dir, default_state_dir, write_json


SKILL_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ALIGNMENT = "delta-contribution-reframer"
REQUIRED_DEEP_READ_ALIGNMENT = "llm-full-paper-deep-read"
REQUIRED_MANIFEST_FIELDS = [
    "deep_read_workflow_alignment",
    "llm_deep_reading",
    "llm_deep_read_record",
    "source_ledger",
    "evidence_boundary",
    "target_regime_summary",
    "broken_assumptions_or_failure_modes",
    "surface_delta",
    "stronger_delta",
    "claim_support_matrix",
    "story_option_board",
    "workflow_coverage",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    physical_line_count = 0
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        for line in handle:
            physical_line_count += 1
            line = line.strip()
            if line:
                records.append(json.loads(line))
    if records and physical_line_count != len(records):
        raise SystemExit(f"Malformed JSONL manifest: expected one JSON object per physical line in {path}")
    return records


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            line = json.dumps(record, ensure_ascii=False).replace(chr(0x2028), "\\u2028").replace(chr(0x2029), "\\u2029")
            handle.write(line + "\n")


def validate_manifest_alignment(manifest: list[dict[str, Any]], manifest_path: Path) -> None:
    if not manifest:
        raise SystemExit(f"Per-paper analysis manifest is empty: {manifest_path}")
    problems: list[str] = []
    for index, record in enumerate(manifest, 1):
        paper_key = str(record.get("paper_key") or record.get("paper_id") or f"record-{index}")
        if record.get("workflow_alignment") != REQUIRED_ALIGNMENT:
            problems.append(f"{paper_key}: workflow_alignment must be {REQUIRED_ALIGNMENT}")
        if record.get("deep_read_workflow_alignment") != REQUIRED_DEEP_READ_ALIGNMENT:
            problems.append(f"{paper_key}: deep_read_workflow_alignment must be {REQUIRED_DEEP_READ_ALIGNMENT}")
        llm_status = record.get("llm_deep_reading") if isinstance(record.get("llm_deep_reading"), dict) else {}
        if llm_status.get("status") != "complete":
            problems.append(f"{paper_key}: llm_deep_reading.status must be complete")
        if not record.get("llm_deep_read_record"):
            problems.append(f"{paper_key}: llm_deep_read_record is required")
        missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in record]
        if missing:
            problems.append(f"{paper_key}: missing fields {', '.join(missing)}")
        if not isinstance(record.get("claim_support_matrix"), list) or not record.get("claim_support_matrix"):
            problems.append(f"{paper_key}: claim_support_matrix must be a non-empty list")
        if not isinstance(record.get("story_option_board"), list) or not record.get("story_option_board"):
            problems.append(f"{paper_key}: story_option_board must be a non-empty list")
        if not isinstance(record.get("workflow_coverage"), list) or "claim_support_matrix" not in record.get("workflow_coverage", []):
            problems.append(f"{paper_key}: workflow_coverage must include claim_support_matrix")
        if not isinstance(record.get("evidence_boundary"), dict):
            problems.append(f"{paper_key}: evidence_boundary must be an object")
        if not isinstance(record.get("surface_delta"), dict) or not isinstance(record.get("stronger_delta"), dict):
            problems.append(f"{paper_key}: surface_delta and stronger_delta must be objects")
    if problems:
        preview = "\n".join(problems[:20])
        extra = f"\n... {len(problems) - 20} more" if len(problems) > 20 else ""
        raise SystemExit(f"Per-paper manifest is not delta-contribution-reframer aligned:\n{preview}{extra}")


def split_semicolon(text: str | None) -> list[str]:
    if not text:
        return []
    return [repair_text(part.strip()) for part in text.split(";") if part.strip()]


MOJIBAKE_REPAIRS = {
    "鑱旈偊瀛︿範": "联邦学习",
    "鑱旈偊瀛︿範?": "联邦学习",
    "鍗婄洃鐫ｅ涔": "半监督学习",
    "鍗婄洃鐫ｅ涔?": "半监督学习",
}


def repair_text(value: str) -> str:
    text = str(value or "").strip()
    for broken, fixed in MOJIBAKE_REPAIRS.items():
        text = text.replace(broken, fixed)
    return text


def infer_year(paper_key: str) -> str:
    match = re.search(r"iclr(20\d{2})_", paper_key)
    return match.group(1) if match else ""


def present_modes(record: dict[str, Any]) -> list[str]:
    modes = record.get("incremental_mode_analysis") or {}
    return [name for name, payload in modes.items() if isinstance(payload, dict) and payload.get("present")]


def present_reply_moves(record: dict[str, Any]) -> list[str]:
    moves = record.get("reply_move_analysis") or {}
    return [name for name, hits in moves.items() if hits]


def present_review_attacks(record: dict[str, Any]) -> list[str]:
    attacks = record.get("review_attack_analysis") or {}
    return [name for name, hits in attacks.items() if hits]


def slugify(parts: list[str], max_len: int = 40) -> str:
    raw = "_".join(parts) or "initialized"
    raw = re.sub(r"[^A-Za-z0-9]+", "_", raw).strip("_").lower()
    raw = raw[:max_len].strip("_")
    return raw or "initialized"


def profile_slug(parts: list[str]) -> str:
    canonical = json.dumps([str(part) for part in parts], ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha1(canonical.encode("utf-8")).hexdigest()[:8]
    return f"{slugify(parts)}_{digest}"


def label_for_card(categories: list[str], modes: list[str], attacks: list[str]) -> str:
    if "low_novelty_or_incremental" in modes and "ablation_evidence" in attacks:
        return "incremental-gain-with-ablation-pressure"
    if "abc_combination" in modes and "abc_or_mechanism" in attacks:
        return "combination-method-needs-mechanism-claim"
    if "transfer_or_light_adaptation" in modes and "experiment_scope" in attacks:
        return "light-transfer-with-scope-generalization-risk"
    if "engineering_or_efficiency" in modes and "cost_efficiency" in attacks:
        return "efficiency-system-claim-under-cost-scrutiny"
    if "evidence_or_benchmark" in modes and "baseline_fairness" in attacks:
        return "benchmark-driven-claim-needs-baseline-fairness"
    if any(category in {"FL", "Federated", "Federated Learning"} for category in categories):
        return "federated-setting-evidence-boundary"
    if any("Semi" in category or "label" in category.lower() for category in categories):
        return "label-scarcity-method-under-novelty-scrutiny"
    return "delta-sized-accepted-paper-pattern"


def make_reframe_template(label: str) -> dict[str, str]:
    templates = {
        "incremental-gain-with-ablation-pressure": {
            "story_move": "把“提升幅度”改写为“在受约束设置下稳定消除特定失效模式”，并把 ablation 组织成机制排除表。",
            "paper_snippet": "Our contribution is not a standalone component swap; it identifies a failure mode in the constrained setting and shows that each design choice is necessary to remove that failure.",
        },
        "combination-method-needs-mechanism-claim": {
            "story_move": "承认组件来自已有谱系，但把贡献定位为组合后的机制闭环、接口约束或目标冲突解决。",
            "paper_snippet": "The novelty lies in the interaction design: the components are individually known, but their coupling resolves a mismatch that neither component addresses in isolation.",
        },
        "light-transfer-with-scope-generalization-risk": {
            "story_move": "避免宣称通用迁移；明确源任务和目标任务之间的结构同构，再用边界条件解释为什么轻量适配成立。",
            "paper_snippet": "We focus on the regime where the source and target settings share the same structural bottleneck, which makes a lightweight adaptation sufficient and testable.",
        },
        "efficiency-system-claim-under-cost-scrutiny": {
            "story_move": "把系统/效率贡献写成资源约束下的可部署性，而不是仅展示更快或更省。",
            "paper_snippet": "The method targets the resource-constrained regime where communication, computation, or annotation cost is the limiting factor, not an incidental metric.",
        },
        "benchmark-driven-claim-needs-baseline-fairness": {
            "story_move": "把 benchmark 贡献从“更多结果”改写为“协议、失败模式和对照公平性”的证据系统。",
            "paper_snippet": "The evaluation is designed to isolate the protocol-level question: which assumptions change the observed advantage, and which baselines remain competitive under matched conditions.",
        },
        "federated-setting-evidence-boundary": {
            "story_move": "强调异质性、通信、隐私或客户端约束带来的问题形态，不把集中式方法迁移包装成完整新算法。",
            "paper_snippet": "The key contribution is the formulation of the federated constraint and its effect on optimization/evaluation, with the algorithm serving that constraint rather than replacing it.",
        },
        "label-scarcity-method-under-novelty-scrutiny": {
            "story_move": "把半监督贡献从 pseudo-label 技巧转成噪声控制、选择偏差、置信传播或标注预算边界的机制。",
            "paper_snippet": "The method is motivated by a label-scarcity failure mode: naive pseudo supervision amplifies bias, while the proposed design controls when and how unlabeled evidence is trusted.",
        },
        "delta-sized-accepted-paper-pattern": {
            "story_move": "把小改动放入明确问题压力、可检验证据链和边界化 claims 中。",
            "paper_snippet": "The contribution is deliberately scoped: it addresses a narrow but recurring failure case and provides evidence for that scope.",
        },
    }
    return enrich_reframe_template(label, templates.get(label, templates["delta-sized-accepted-paper-pattern"]))


def enrich_reframe_template(label: str, template: dict[str, str]) -> dict[str, str]:
    enriched: dict[str, dict[str, str]] = {
        "incremental-gain-with-ablation-pressure": {
            "story_move": "把“提升幅度”改写为“在受约束设定下稳定消除特定失败模式”，并把 ablation 组织成机制排除表。",
            "raw_weakness": "工作容易被读成小幅性能提升或单点替换。",
            "effective_packaging": "先命名失败模式，再把模块写成 targeted intervention，并用 ablation 支撑必要性。",
            "borrowable_move": "用于 strong packaging diagnosis、mechanism rebuttal、Tier 0 ablation discussion rewrite。",
            "risk_boundary": "不要把 ablation 写成完整机制证明；只能说 supports the mechanism 或 rules out simpler explanations。",
            "story_route_use": "failure-mode / mechanism-evidence route",
            "best_report_sections": "Option 1, Option 4, Reviewer Attack Preplay, Rebuttal Mechanism",
        },
        "combination-method-needs-mechanism-claim": {
            "story_move": "承认组件来自已有谱系，但把贡献定位为组合后的机制闭环、接口约束或目标冲突解决。",
            "raw_weakness": "工作容易被攻击为 known components assembly 或 A+B/C。",
            "effective_packaging": "把每个组件映射到受约束场景中的一个压力，证明耦合是由场景需求驱动的。",
            "borrowable_move": "用于 Story Option Board 的主线、method overview、Figure 1 caption、A+B/C rebuttal。",
            "risk_boundary": "不要说每个 primitive 都全新；防守的是 constraint-driven coupling。",
            "story_route_use": "surrogate / coupling / interface route",
            "best_report_sections": "Option 1, Option 3, Rebuttal A+B/C",
        },
        "light-transfer-with-scope-generalization-risk": {
            "story_move": "避免宣称通用迁移；明确源任务和目标任务之间的结构同构，再用边界条件解释为什么轻量适配成立。",
            "raw_weakness": "迁移或适配工作容易被认为 novelty 不足或 scope 过窄。",
            "effective_packaging": "把贡献限制在共享结构瓶颈下的可验证适配，而不是泛化到所有场景。",
            "borrowable_move": "用于 related-work boundary、scope/generalization rebuttal、residual risk。",
            "risk_boundary": "不要宣称 universal transfer；只说 evaluated regime 或 shared structural bottleneck。",
            "story_route_use": "scope-boundary / transfer route",
            "best_report_sections": "Option 2, Option 6, Residual Risk",
        },
        "efficiency-system-claim-under-cost-scrutiny": {
            "story_move": "把系统/效率贡献写成资源约束下的可部署性，而不是仅展示更快或更省。",
            "raw_weakness": "系统工作容易被要求更多成本、通信、规模和复现细节。",
            "effective_packaging": "主动定义 quality-cost tradeoff 和 resource contract，把成本边界放进 limitation 或 discussion。",
            "borrowable_move": "用于 cost/scalability attack、Tier 1 log reuse、limitation paragraph。",
            "risk_boundary": "没有 runtime、communication 或 resource schedule 时，不要写 negligible overhead。",
            "story_route_use": "quality-cost / deployment-boundary route",
            "best_report_sections": "Option 5, Tier 1, Rebuttal Cost",
        },
        "benchmark-driven-claim-needs-baseline-fairness": {
            "story_move": "把 benchmark 贡献从“更多结果”改写为“协议、失败模式和对照公平性”的证据系统。",
            "raw_weakness": "实验多但组织松散时，审稿人会质疑 baseline fairness、coverage 或 cherry-picking。",
            "effective_packaging": "先定义 comparison contract，再把主实验、消融、robustness 和 appendix 组织成回答审稿疑问的证据系统。",
            "borrowable_move": "用于 experiment roadmap、baseline fairness rebuttal、appendix pointer。",
            "risk_boundary": "不要把资源不等价的 baseline 直接说成 incomparable；要说明 same-contract 与 diagnostic comparison。",
            "story_route_use": "evidence-system / baseline-contract route",
            "best_report_sections": "Option 2, Option 4, Rebuttal Baseline",
        },
        "federated-setting-evidence-boundary": {
            "story_move": "强调异质性、通信、隐私或客户端约束带来的问题形态，不把集中式方法迁移包装成完整新算法。",
            "raw_weakness": "联邦/去中心化工作容易被读成把集中式方法换个部署环境。",
            "effective_packaging": "先写清不可用资源和协议边界，再防守算法服务于这些约束。",
            "borrowable_move": "用于 problem contract、baseline contract、privacy/scope boundary。",
            "risk_boundary": "不要把 no raw-data sharing 等同于 formal privacy guarantee。",
            "story_route_use": "problem-contract / federated-boundary route",
            "best_report_sections": "Option 2, Reviewer Attack Preplay, Residual Risk",
        },
        "label-scarcity-method-under-novelty-scrutiny": {
            "story_move": "把半监督贡献从 pseudo-label 技巧转成噪声控制、选择偏差、置信传播或标注预算边界的机制。",
            "raw_weakness": "半监督工作容易被认为只是换了伪标签或增强策略。",
            "effective_packaging": "先命名 label-scarcity failure mode，再把模块写成控制未标注证据何时可信的机制。",
            "borrowable_move": "用于 novelty defense、mechanism evidence、method overview。",
            "risk_boundary": "没有直接噪声诊断时，不要声称 fully resolves confirmation bias。",
            "story_route_use": "label-scarcity / trust-control route",
            "best_report_sections": "Option 1, Option 3, Rebuttal Mechanism",
        },
        "baseline-contract-fairness-defense": {
            "story_move": "先定义 same-contract baseline，再解释哪些对照满足相同资源约束，哪些只是 broader-regime diagnostic。",
            "raw_weakness": "baseline 资源边界不清会被读成回避强对照。",
            "effective_packaging": "在实验前加入 comparison contract，把服务器、共享数据、共享验证集、标注预算、通信预算等条件显式化。",
            "borrowable_move": "用于 related work boundary、experiment setup、baseline fairness rebuttal。",
            "risk_boundary": "不要简单说 baseline 不可比；要说明 resource mismatch 和 diagnostic value。",
            "story_route_use": "baseline-contract route",
            "best_report_sections": "Option 2, Reviewer Attack Preplay, Rebuttal Baseline",
            "paper_snippet": "We clarify the comparison contract by distinguishing same-resource baselines from diagnostic baselines that rely on additional coordination or supervision.",
        },
        "evidence-system-coverage-defense": {
            "story_move": "把现有实验重排成回答审稿疑问的证据系统，而不是按数据集或表格顺序堆结果。",
            "raw_weakness": "实验结果存在但没有说明每个结果防守哪个 reviewer concern。",
            "effective_packaging": "把 performance、label scarcity、non-IID、topology、ablation、runtime 或 appendix 证据逐一映射到攻击点。",
            "borrowable_move": "用于 Option 4、Tier 0 experiment-roadmap rewrite、appendix pointer。",
            "risk_boundary": "证据系统只能支撑 evaluated regime，不能自动支撑 universal generalization。",
            "story_route_use": "evidence-system route",
            "best_report_sections": "Option 4, Manuscript Trigger Localization, Tier 0",
            "paper_snippet": "We organize the evaluation around the main failure modes: end-to-end performance, robustness to the constrained regime, and component-level evidence for the proposed mechanism.",
        },
        "scope-generalization-boundary-defense": {
            "story_move": "把适用范围前置，主动限定 evaluated regime，避免被审稿人用更大场景攻击。",
            "raw_weakness": "claims 如果写得过满，审稿人会要求更多数据集、规模、拓扑或真实部署。",
            "effective_packaging": "把当前证据覆盖的范围写清，把更大泛化放入 limitation 或 future work。",
            "borrowable_move": "用于 residual risk、discussion、scope rebuttal。",
            "risk_boundary": "不要写 universal claim；写 evaluated settings 或 initial evidence。",
            "story_route_use": "scope-boundary route",
            "best_report_sections": "Option 6, Rebuttal Scope, Residual Risk",
            "paper_snippet": "We keep the claim focused on the evaluated regime and treat broader deployment conditions as an important direction for future validation.",
        },
        "delta-sized-accepted-paper-pattern": {
            "story_move": "把小改动放入明确问题压力、可检验证据链和边界化 claims 中。",
            "raw_weakness": "贡献小但没有被放进清晰问题压力时，容易被直接判为 incremental。",
            "effective_packaging": "以问题压力、证据链和边界化 claims 组织贡献。",
            "borrowable_move": "用于 strong packaging diagnosis 和 report fallback。",
            "risk_boundary": "不要夸大成 broad framework；防守 narrow but recurring failure case。",
            "story_route_use": "fallback delta-packaging route",
            "best_report_sections": "Strong Packaging Diagnosis, Residual Risk",
        },
    }
    out = dict(template)
    out.update(enriched.get(label, enriched["delta-sized-accepted-paper-pattern"]))
    return out


def synthesize(run_dir: Path, fallback_years: list[str]) -> dict[str, Any]:
    manifest_path = run_dir / "analysis" / "per_paper_analysis_manifest.jsonl"
    manifest = load_jsonl(manifest_path)
    validate_manifest_alignment(manifest, manifest_path)
    rows = load_csv(run_dir / "index" / "screened_incremental_candidates.csv")
    if not rows:
        rows = load_csv(run_dir / "index" / "incremental_high_risk_candidates.csv")
    row_by_key = {row.get("paper_key", ""): row for row in rows}

    category_counts: Counter[str] = Counter()
    year_counts: Counter[str] = Counter()
    risk_counts: Counter[str] = Counter()
    mode_counts: Counter[str] = Counter()
    attack_counts: Counter[str] = Counter()
    reply_counts: Counter[str] = Counter()
    status_counts: dict[str, Counter[str]] = {
        "pdf": Counter(),
        "review": Counter(),
        "reply": Counter(),
        "llm_deep_read": Counter(),
    }
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    all_examples: list[dict[str, Any]] = []

    for record in manifest:
        key = str(record.get("paper_key", ""))
        row = row_by_key.get(key, {})
        categories = split_semicolon(row.get("categories")) or ["Other"]
        year = row.get("year") or infer_year(key) or (fallback_years[0] if fallback_years else "")
        risk = row.get("risk_tier") or "unknown"
        modes = present_modes(record)
        attacks = present_review_attacks(record)
        replies = present_reply_moves(record)
        category_counts.update(categories)
        if year:
            year_counts[year] += 1
        risk_counts[risk] += 1
        mode_counts.update(modes)
        attack_counts.update(attacks)
        reply_counts.update(replies)
        status_counts["pdf"][record.get("pdf_status", "unknown")] += 1
        status_counts["review"][record.get("review_status", "unknown")] += 1
        status_counts["reply"][record.get("reply_status", "unknown")] += 1
        status_counts["llm_deep_read"][(record.get("llm_deep_reading") or {}).get("status", "not_run")] += 1
        example = {"categories": categories, "year": year, "risk": risk, "modes": modes, "attacks": attacks, "replies": replies}
        all_examples.append(example)
        grouped[label_for_card(categories, modes, attacks)].append(example)

    cards: list[dict[str, Any]] = []
    for idx, (label, examples) in enumerate(sorted(grouped.items(), key=lambda item: len(item[1]), reverse=True), 1):
        cat_counter: Counter[str] = Counter()
        mode_counter: Counter[str] = Counter()
        attack_counter: Counter[str] = Counter()
        reply_counter: Counter[str] = Counter()
        year_counter: Counter[str] = Counter()
        for example in examples:
            cat_counter.update(example["categories"])
            mode_counter.update(example["modes"])
            attack_counter.update(example["attacks"])
            reply_counter.update(example["replies"])
            if example["year"]:
                year_counter[example["year"]] += 1
        template = make_reframe_template(label)
        cards.append(
            {
                "schema_version": "1.0",
                "case_id": f"anonymous-delta-case-{idx:03d}",
                "case_label": label,
                "source": "anonymous aggregate from initialized paper corpus",
                "evidence_label": "latent-but-supported",
                "example_count": len(examples),
                "domain_labels": [name for name, _count in cat_counter.most_common()],
                "years": dict(year_counter),
                "common_incremental_modes": [name for name, _count in mode_counter.most_common(5)],
                "common_review_attacks": [name for name, _count in attack_counter.most_common(5)],
                "common_reply_moves": [name for name, _count in reply_counter.most_common(5)],
                "story_route_use": template["story_route_use"],
                "reframing_move": template["story_move"],
                "raw_weakness_pattern": template["raw_weakness"],
                "effective_packaging_pattern": template["effective_packaging"],
                "borrowable_move": template["borrowable_move"],
                "risk_boundary": template["risk_boundary"],
                "best_report_sections": template["best_report_sections"],
                "manuscript_facing_snippet": template["paper_snippet"],
                "anonymization": "No titles, authors, forum ids, URLs, exact method names, or unique benchmark bundles retained.",
            }
        )

    def append_lens_card(label: str, examples: list[dict[str, Any]]) -> None:
        if not examples:
            return
        if any(card["case_label"] == label for card in cards):
            return
        cat_counter: Counter[str] = Counter()
        mode_counter: Counter[str] = Counter()
        attack_counter: Counter[str] = Counter()
        reply_counter: Counter[str] = Counter()
        year_counter: Counter[str] = Counter()
        for example in examples:
            cat_counter.update(example["categories"])
            mode_counter.update(example["modes"])
            attack_counter.update(example["attacks"])
            reply_counter.update(example["replies"])
            if example["year"]:
                year_counter[example["year"]] += 1
        template = make_reframe_template(label)
        idx = len(cards) + 1
        cards.append(
            {
                "schema_version": "1.0",
                "case_id": f"anonymous-delta-case-{idx:03d}",
                "case_label": label,
                "source": "anonymous aggregate lens from initialized paper corpus",
                "evidence_label": "latent-but-supported",
                "example_count": len(examples),
                "domain_labels": [name for name, _count in cat_counter.most_common()],
                "years": dict(year_counter),
                "common_incremental_modes": [name for name, _count in mode_counter.most_common(5)],
                "common_review_attacks": [name for name, _count in attack_counter.most_common(5)],
                "common_reply_moves": [name for name, _count in reply_counter.most_common(5)],
                "story_route_use": template["story_route_use"],
                "reframing_move": template["story_move"],
                "raw_weakness_pattern": template["raw_weakness"],
                "effective_packaging_pattern": template["effective_packaging"],
                "borrowable_move": template["borrowable_move"],
                "risk_boundary": template["risk_boundary"],
                "best_report_sections": template["best_report_sections"],
                "manuscript_facing_snippet": template["paper_snippet"],
                "anonymization": "No titles, authors, forum ids, URLs, exact method names, or unique benchmark bundles retained.",
            }
        )

    append_lens_card("baseline-contract-fairness-defense", [ex for ex in all_examples if "baseline_fairness" in ex["attacks"]])
    append_lens_card(
        "evidence-system-coverage-defense",
        [ex for ex in all_examples if "experiment_scope" in ex["attacks"] or "ablation_evidence" in ex["attacks"]],
    )
    append_lens_card(
        "efficiency-system-claim-under-cost-scrutiny",
        [ex for ex in all_examples if "cost_efficiency" in ex["attacks"] or "engineering_or_efficiency" in ex["modes"]],
    )
    append_lens_card(
        "scope-generalization-boundary-defense",
        [ex for ex in all_examples if "experiment_scope" in ex["attacks"] or "reproducibility" in ex["attacks"]],
    )

    return {
        "paper_count": len(manifest),
        "categories": dict(category_counts),
        "years": dict(year_counts),
        "risk_tiers": dict(risk_counts),
        "incremental_modes": dict(mode_counts),
        "review_attacks": dict(attack_counts),
        "reply_moves": dict(reply_counts),
        "status": {name: dict(counter) for name, counter in status_counts.items()},
        "cards": cards,
    }


def markdown_table(counter: dict[str, int], left: str, right: str = "Count") -> list[str]:
    lines = [f"| {left} | {right} |", "|---|---:|"]
    for key, count in sorted(counter.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| `{key}` | {count} |")
    return lines


def write_reports(
    summary: dict[str, Any],
    focus_domains: list[str],
    years: list[str],
    source_kind: str,
    domain_scope: str,
    references_dir: Path,
) -> list[str]:
    now = dt.datetime.now().isoformat(timespec="seconds")
    focus_domains = [repair_text(domain) for domain in focus_domains]
    profile_name = f"domain_profile_{profile_slug([*focus_domains, *years])}.md"
    focus_text = ", ".join(f"`{domain}`" for domain in focus_domains) or "`unspecified`"
    year_text = ", ".join(f"`{year}`" for year in years) or "`unspecified`"
    overview = [
        "# Delta Contribution Knowledge Base Overview",
        "",
        f"- Updated at: {now}",
        f"- Source kind: `{source_kind}`",
        f"- Domain scope: `{domain_scope}`",
        f"- Focus domains: {focus_text}",
        f"- Years: {year_text}",
        f"- Paper count: {summary['paper_count']}",
        "- Evidence coverage: see `.delta-contribution-reframer/state/per_paper_analysis_state.json`; reusable knowledge is stored as anonymous project-local resources.",
        "",
        "## Category Counts",
        "",
        *markdown_table(summary["categories"], "Category"),
        "",
        "## Incremental Modes",
        "",
        *markdown_table(summary["incremental_modes"], "Mode"),
        "",
        "## Review Attack Patterns",
        "",
        *markdown_table(summary["review_attacks"], "Attack"),
        "",
        "## Reply Move Patterns",
        "",
        *markdown_table(summary["reply_moves"], "Reply move"),
        "",
        "## LLM Deep-Read Coverage",
        "",
        *markdown_table(summary["status"].get("llm_deep_read", {}), "LLM status"),
        "",
        "## Reusable Anonymous Case Labels",
        "",
        "| Case label | Examples | Route use | Dominant domains | Common attacks |",
        "|---|---:|---|---|---|",
    ]
    for card in summary["cards"]:
        overview.append(
            "| `{}` | {} | {} | {} | {} |".format(
                card["case_label"],
                card["example_count"],
                card.get("story_route_use", ""),
                ", ".join(f"`{x}`" for x in card["domain_labels"][:3]),
                ", ".join(f"`{x}`" for x in card["common_review_attacks"][:3]),
            )
        )
    overview.extend(
        [
            "",
            "## Evidence Rules",
            "",
            "All reusable cases are anonymous aggregates. Use `simulated-review` only when applying these patterns to a new target paper without real reviews.",
        ]
    )
    references_dir.mkdir(parents=True, exist_ok=True)
    (references_dir / profile_name).write_text(
        "\n".join(overview).replace("# Delta Contribution Knowledge Base Overview", "# Initialized Delta Contribution Domain Profile") + "\n",
        encoding="utf-8",
    )

    synthesis = [
        "# Reusable Delta-Contribution Synthesis",
        "",
        f"Scope: {source_kind} corpus, focused on {', '.join(focus_domains) or 'unspecified domains'}, years {', '.join(years) or 'unspecified'}.",
        "",
        "## What The Initialized Corpus Supports",
        "",
        "- Low-novelty defense should be built around explicit failure modes, not around claiming a larger algorithmic leap.",
        "- Accepted delta-sized work often survives by narrowing the setting, clarifying the mechanism, and making the evidence chain auditable.",
        "- Rebuttal patterns frequently combine existing-evidence resurfacing, claim clarification, and boundary defense; new experiments appear in real author replies but should not be invented for future use.",
        "- Use domain-specific constraints as the contribution anchor: heterogeneity, label scarcity, communication/cost, benchmark protocol, or deployment limits.",
        "",
        "## Reusable Case Cards",
        "",
    ]
    for card in summary["cards"]:
        synthesis.extend(
            [
                f"### {card['case_id']}: {card['case_label']}",
                "",
                f"- Examples: {card['example_count']}",
                f"- Domains: {', '.join(card['domain_labels'])}",
                f"- Modes: {', '.join(card['common_incremental_modes'])}",
                f"- Review attacks: {', '.join(card['common_review_attacks'])}",
                f"- Reply moves: {', '.join(card['common_reply_moves'])}",
                f"- Route use: {card.get('story_route_use', '')}",
                f"- Raw weakness pattern: {card.get('raw_weakness_pattern', '')}",
                f"- Effective packaging pattern: {card.get('effective_packaging_pattern', '')}",
                f"- Reframing: {card['reframing_move']}",
                f"- Borrowable move: {card.get('borrowable_move', '')}",
                f"- Risk boundary: {card.get('risk_boundary', '')}",
                f"- Best report sections: {card.get('best_report_sections', '')}",
                "",
                "English manuscript-facing snippet:",
                "",
                f"> {card['manuscript_facing_snippet']}",
                "",
            ]
        )
    (references_dir / "per_pdf_report_synthesis.md").write_text("\n".join(synthesis).strip() + "\n", encoding="utf-8")

    llm_synthesis = [
        "# LLM Deep-Read Corpus Synthesis",
        "",
        f"Scope: {source_kind} corpus, focused on {', '.join(focus_domains) or 'unspecified domains'}, years {', '.join(years) or 'unspecified'}.",
        "",
        "## Coverage Contract",
        "",
        f"- Paper count: {summary['paper_count']}",
        f"- Complete LLM deep reads: {summary['status'].get('llm_deep_read', {}).get('complete', 0)}",
        "- The generated skill packages only anonymous synthesis. Per-paper LLM reports, prompts, PDFs, and raw review material remain in the external project run.",
        "",
        "## What The LLM-Read Corpus Adds Beyond Rule Matching",
        "",
        "- Full-paper reading grounds delta reframing in method mechanics, assumptions, experiment design, figure/table evidence, and reproducibility gaps rather than keyword hits alone.",
        "- Reviewer defense should preserve the evidence boundary: supported claims can be strengthened, weak broad claims should be narrowed, and missing details must stay marked as not reported.",
        "- Story options should be selected from paper-level failure modes and claim-support structure, then checked against review/reply evidence when available.",
        "",
        "## Anonymous Reuse Priorities",
        "",
    ]
    for card in summary["cards"]:
        llm_synthesis.extend(
            [
                f"### {card['case_label']}",
                "",
                f"- Route use: {card.get('story_route_use', '')}",
                f"- Effective packaging pattern: {card.get('effective_packaging_pattern', '')}",
                f"- Risk boundary: {card.get('risk_boundary', '')}",
                f"- Borrowable move: {card.get('borrowable_move', '')}",
                "",
            ]
        )
    (references_dir / "llm_deep_read_synthesis.md").write_text("\n".join(llm_synthesis).strip() + "\n", encoding="utf-8")
    write_jsonl(references_dir / "anonymous_casebook.jsonl", summary["cards"])
    return [
        "references/anonymous_casebook.jsonl",
        "references/per_pdf_report_synthesis.md",
        "references/llm_deep_read_synthesis.md",
        f"references/{profile_name}",
    ]


def update_state(
    summary: dict[str, Any],
    focus_domains: list[str],
    years: list[str],
    source_kind: str,
    domain_scope: str,
    resources: list[str],
    state_dir: Path,
) -> None:
    now = dt.datetime.now().isoformat(timespec="seconds")
    focus_domains = [repair_text(domain) for domain in focus_domains]
    per_paper = {
        "schema_version": "1.0",
        "updated_at": now,
        "paper_count": summary["paper_count"],
        "report_coverage_complete": True,
        "all_pdfs_text_extracted": summary["status"]["pdf"].get("ok", 0) == summary["paper_count"],
        "all_llm_deep_reads_complete": summary["status"].get("llm_deep_read", {}).get("complete", 0) == summary["paper_count"],
        "complete_count": summary["paper_count"],
        "partial_count": 0,
        "pdf_status_counts": summary["status"]["pdf"],
        "llm_deep_read_status_counts": summary["status"].get("llm_deep_read", {}),
        "manifest": None,
        "index": None,
        "packaged_manifest_policy": "Per-paper manifests remain in the external project run; reusable project state keeps only anonymous aggregates.",
    }
    resource_records = [{"path": resource, "kind": Path(resource).stem, "status": "available"} for resource in resources]
    init_state = {
        "schema_version": "1.0",
        "initialized": True,
        "status": "ready",
        "reason": "Knowledge initialized from an evidence corpus and synthesized into project-local anonymous resources.",
        "source_kind": source_kind,
        "domain_scope": domain_scope,
        "focus_domains": focus_domains,
        "years": years,
        "corpus_source": "external project corpus consumed during initialization",
        "project_run_dir": None,
        "per_paper_analysis_required": True,
        "llm_deep_read_required": True,
        "per_paper_analysis_complete": True,
        "llm_deep_read_complete": True,
        "self_contained_reusable_knowledge": True,
        "original_pdfs_required_for_reuse": False,
        "per_paper_analysis_state": per_paper,
        "updated_at": now,
    }
    knowledge_state = {
        "schema_version": "1.0",
        "knowledge_available": True,
        "source_kind": source_kind,
        "domain_scope": domain_scope,
        "focus_domains": focus_domains,
        "years": years,
        "paper_count": summary["paper_count"],
        "summary": {
            "categories": summary["categories"],
            "risk_tiers": summary["risk_tiers"],
            "incremental_modes": summary["incremental_modes"],
            "review_attacks": summary["review_attacks"],
            "reply_moves": summary["reply_moves"],
            "llm_deep_read_status": summary["status"].get("llm_deep_read", {}),
            "anonymous_case_count": len(summary["cards"]),
        },
        "self_contained_reusable_knowledge": True,
        "original_pdfs_required_for_reuse": False,
        "original_pdfs_required_for_new_evidence_grounded_analysis": True,
        "per_paper_analysis": per_paper,
        "resources": resource_records,
        "updated_at": now,
    }
    skill_state = {
        "schema_version": "1.0",
        "skill_name": "delta-contribution-reframer",
        "status": "ready",
        "startup_gate_enabled": True,
        "default_source_kind": "iclr-openreview",
        "default_domain_scope": "computer-science",
        "corpus_source": "project-local anonymous resources",
        "required_initialization_inputs": ["focus_domains", "years", "corpus_source"],
        "last_startup_check": now,
        "last_requires_initialization": False,
    }
    evolution_state_path = state_dir / "evolution_state.json"
    if not evolution_state_path.exists():
        write_json(
            evolution_state_path,
            {
                "schema_version": "1.0",
                "status": "idle",
                "evolving": False,
                "evolving_case_count": 0,
                "last_case_id": None,
                "updated_at": None,
            },
        )
    write_json(state_dir / "per_paper_analysis_state.json", per_paper)
    write_json(state_dir / "initialization_state.json", init_state)
    write_json(state_dir / "knowledge_state.json", knowledge_state)
    write_json(state_dir / "skill_state.json", skill_state)


def read_config(path: Path | None) -> dict[str, Any]:
    if not path:
        return {}
    payload = json.loads(path.expanduser().resolve().read_text(encoding="utf-8-sig", errors="replace"))
    if not isinstance(payload, dict):
        raise SystemExit(f"--config-file must contain one JSON object: {path}")
    return payload


def config_value(config: dict[str, Any], field: str) -> Any:
    if field in config:
        return config[field]
    dashed = field.replace("_", "-")
    if dashed in config:
        return config[dashed]
    return None


def apply_config(args: argparse.Namespace) -> argparse.Namespace:
    config = read_config(args.config_file)
    if not config:
        return args
    for field in ["run_dir", "state_dir", "references_dir"]:
        if getattr(args, field) is None and config_value(config, field) is not None:
            setattr(args, field, Path(str(config_value(config, field))))
    for field in ["focus_domains", "years"]:
        if not getattr(args, field) and config_value(config, field) is not None:
            value = config_value(config, field)
            setattr(args, field, [str(item) for item in value] if isinstance(value, list) else [str(value)])
    for field, default in [("source_kind", "project-corpus"), ("domain_scope", "computer-science")]:
        if getattr(args, field) is None:
            setattr(args, field, str(config_value(config, field) or default))
    return args


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Synthesize anonymous project-local resources from completed per-paper analysis.")
    parser.add_argument("--config-file", type=Path, default=None, help="JSON synthesis configuration. Prefer this for long domain/year lists.")
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--focus-domains", nargs="*", default=[])
    parser.add_argument("--years", nargs="*", default=[])
    parser.add_argument("--source-kind", default=None)
    parser.add_argument("--domain-scope", default=None)
    parser.add_argument("--state-dir", type=Path, default=None)
    parser.add_argument("--references-dir", type=Path, default=None)
    args = apply_config(parser.parse_args())
    if args.run_dir is None:
        raise SystemExit("--run-dir is required through CLI or --config-file")
    if args.state_dir is None:
        args.state_dir = default_state_dir()
    if args.references_dir is None:
        args.references_dir = default_references_dir()
    if args.source_kind is None:
        args.source_kind = "project-corpus"
    if args.domain_scope is None:
        args.domain_scope = "computer-science"
    return args


def main() -> None:
    args = parse_args()
    run_dir = args.run_dir.resolve()
    if not (run_dir / "analysis" / "per_paper_analysis_manifest.jsonl").exists():
        raise SystemExit(f"Missing per-paper analysis manifest under run dir: {run_dir}")
    summary = synthesize(run_dir, [str(year) for year in args.years])
    resources = write_reports(
        summary,
        args.focus_domains,
        [str(year) for year in args.years],
        args.source_kind,
        args.domain_scope,
        args.references_dir.resolve(),
    )
    update_state(
        summary,
        args.focus_domains,
        [str(year) for year in args.years],
        args.source_kind,
        args.domain_scope,
        resources,
        args.state_dir.resolve(),
    )
    print(json.dumps({"paper_count": summary["paper_count"], "anonymous_case_count": len(summary["cards"]), "resources": resources}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
