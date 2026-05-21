#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from common import default_project_dir, default_references_dir, default_state_dir, nonempty, read_json, write_json


SKILL_ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = default_state_dir()
REFERENCES_DIR = default_references_dir()
PROJECT_DIR = default_project_dir()

PROMPT_MENU = [
    "初始化知识库：目标论文PDF=<...>（自动推断 1-3 个领域/子领域）或关注领域=<...>，年份=<...>，论文来源=<local corpus or zip root>",
    "初始化默认设置：每年最多分析 100 篇；多个领域默认均衡抽样；如果未给领域，会先精读目标论文并用推断领域筛选",
    "默认来源：ICLR OpenReview accepted-paper export；默认领域：computer science",
    "把本地 PDF 文件夹标准化为项目语料并逐篇分析：<pdf_folder>",
    "从项目 discovery/download 结果初始化知识库：<project_run_dir>",
    "扫描我的论文语料目录，列出可选领域和年份：<path>",
    "分析这篇 PDF，并输出可下载报告：<path>",
    "生成 3-6 条顶会故事路线，并排序比较",
    "模拟审稿人攻击，给出不增加实验的修改方案",
    "根据 reviewer comments 写 rebuttal 防守策略",
    "把这篇新论文作为样例摄取，判断是否纳入 skill 知识库",
    "把 PDF + 审稿意见 + 作者答复作为 evolution 样例摄取，并保存逐篇分析中间结果",
    "查看初始化状态和 evolving casebook",
]


def knowledge_present() -> tuple[bool, list[dict[str, object]]]:
    candidates = [
        REFERENCES_DIR / "anonymous_casebook.jsonl",
        REFERENCES_DIR / "per_pdf_report_synthesis.md",
        REFERENCES_DIR / "llm_deep_read_synthesis.md",
        REFERENCES_DIR / "evolving_casebook.jsonl",
    ]
    resources = []
    present = False
    for path in candidates:
        ok = nonempty(path)
        present = present or ok
        try:
            display_path = str(path.relative_to(PROJECT_DIR))
        except ValueError:
            display_path = str(path)
        resources.append({"path": display_path, "exists": path.exists(), "nonempty": ok, "bytes": path.stat().st_size if path.exists() else 0})
    init_state = read_json(STATE_DIR / "initialization_state.json")
    present = present or bool(init_state.get("initialized") is True)
    return present, resources


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check delta-contribution-reframer startup state.")
    parser.add_argument("--top-areas", type=int, default=18)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    present, resources = knowledge_present()
    catalog = read_json(STATE_DIR / "corpus_catalog.json")
    init_state = read_json(STATE_DIR / "initialization_state.json")
    evolution_state = read_json(STATE_DIR / "evolution_state.json")
    result = {
        "knowledge_present": present,
        "requires_initialization": not present,
        "mandatory_inputs_if_initializing": ["target_paper_or_focus_domains", "years", "corpus_source"],
        "default_source_kind": "iclr-openreview",
        "default_domain_scope": "computer-science",
        "project_state_dir": str(STATE_DIR),
        "project_references_dir": str(REFERENCES_DIR),
        "initialization_state": init_state,
        "evolution_state": evolution_state,
        "resources": resources,
        "corpus_catalog": {
            "available": bool(catalog.get("available")),
            "submission_count": catalog.get("submission_count"),
            "years": catalog.get("years"),
            "top_areas": (catalog.get("areas") or [])[: args.top_areas],
        },
        "prompt_menu": PROMPT_MENU,
    }
    skill_state_path = STATE_DIR / "skill_state.json"
    skill_state = read_json(skill_state_path)
    if skill_state:
        skill_state["last_startup_check"] = dt.datetime.now().isoformat(timespec="seconds")
        skill_state["last_requires_initialization"] = not present
        write_json(skill_state_path, skill_state)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
