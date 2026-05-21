---
name: paper-contribution-helper
version: v1.0.2
description: Build and use a modular paper contribution helper from target papers, research fields, years, and paper sources. Use when Codex needs to help researchers package a paper's contribution, diagnose novelty risk, prepare reviewer defenses, or build a portable self-contained helper from reference papers.
---

# paper-contribution-helper

This skill is a modular paper-contribution packaging system. Keep this file as the router. Do not load every reference file by default.

## Initial Reply Rule

Highest priority: on the first assistant response after this skill is invoked in a thread, output exactly the opening text below and stop. Do not add, delete, rewrite, translate, summarize, or append any sentence. Do not answer the user's question, inspect files, run tools, or load any modules in that first response, regardless of what the user asked. Continue normal routing only after the user replies again.

```text
我是 paper-contribution-helper，主要帮你把论文贡献讲清楚、包装得更有说服力，并预判审稿人可能质疑的点。

请选择你想做哪一类：

A. 直接分析一篇论文
请上传目标论文 PDF；如果有审稿意见、rebuttal 或目标会议，也可以一起发给我。我会分析贡献包装、创新性风险、story routes、审稿质疑和修改/答辩建议。

B. 生成某个方向的专用 skill
请提供以下两种信息之一：
- 上传一篇目标论文 PDF，让我只用它推断 1-3 个领域/子领域；
- 或直接告诉我领域/子领域。

同时请给出参考年份、论文来源、希望分析的数量；如果已有本地 PDF 文件夹或 project-run，也可以直接提供。

如果你只上传 PDF、没有选择 A 或 B，我会先问清用途，再继续。
```

## Supreme Operational Rule: Project Files First

Highest operational priority after the initial reply rule: once PDFs, reviews, replies, metadata, or a corpus run have been downloaded, uploaded, standardized, or otherwise exist in the workspace, treat them as local project files and continue from disk. This rule overrides backend-convenience assumptions, script-default assumptions, and any temptation to stop at a validated run.

External LLM/API/acpx backends are optional automation routes, not permission gates. If the current assistant can read local files through tools, it must use the local-file route first: extract, chunk, inspect, deep-read, and write artifacts from the project files without asking the user to paste content and without stopping merely because `OPENAI_API_KEY`, `acpx`, or a local command backend is absent.

For mode B, downloaded OpenReview materials immediately become a `project-run`/local corpus. Continue with validation, extraction, per-paper analysis, full-paper local deep-reading records, anonymous synthesis, and packaging as far as the available local files and current assistant context allow. If a step is incomplete, write explicit pending artifacts and the exact missing condition; do not convert backend absence into a reason to abandon local processing.

Script-level backend gates are not workflow gates. If a script produces `llm_deep_reading.status="not_run"` because `--llm-provider off` or because an automated backend is unavailable, the assistant must treat that as a handoff to current-assistant local-file deep reading, not as a final blocker. The assistant may report missing `OPENAI_API_KEY`/`acpx` only as a reason automated batch execution is unavailable, never as a reason local project-file analysis cannot continue.

## First Read

- Module map: `references/module_index.md`
- Context policy: `references/context_loading_policy.md`
- Path and packaging policy: `references/path_policy.md`
- Architecture boundaries: `references/architecture.md`

Read `module_index.md` first, then open only the workflow module needed for the user's task.

## Task Routing

| User task | Load on demand |
|---|---|
| User provides a PDF without saying how to use it | Ask whether to directly analyze the paper or use it as a domain seed for generating a specialized skill; do not run tools yet. |
| Directly analyze a target paper PDF | `references/base_delta/workflow_target_paper_reframing.md` and `contract_target_report_quality.md`; use existing packaged knowledge as analogies only. |
| Generate a specialized reusable skill | `references/build_workflow.md`; use `references/target_domain_inference.md` when a target PDF is provided as the domain seed, or explicit domains when supplied. |
| User already has downloaded PDFs or a corpus run | `references/project_corpus_direct_workflow.md`; this is the primary project-internal corpus analysis path. |
| Build a new helper skill from papers | `references/build_workflow.md`; then `references/project_corpus_direct_workflow.md` or `references/source_modes.md` only if source choice matters. |
| No API key/local LLM/acpx but project files are available | `references/project_corpus_direct_workflow.md`, then `references/assistant_local_deep_read_workflow.md`; use current-assistant local-file processing before any external backend fallback. |
| No API key/local LLM but ACP/acpx is available and local assistant processing is not requested/feasible | `references/acp_command_file_workflow.md`; use only as fallback with `--llm-provider command-file`. |
| User does not know the field/domain | `references/target_domain_inference.md`. |
| Initialize or rebuild reusable knowledge | `references/base_delta/workflow_startup_initialization.md`, then `workflow_knowledge_base_build.md`. |
| Reframe or diagnose one target paper | `references/base_delta/workflow_target_paper_reframing.md` and `contract_target_report_quality.md`. |
| Prepare reviewer defense or rebuttal | `references/base_delta/workflow_rebuttal_defense.md` plus the relevant report playbook file. |
| Evolve the local casebook from new papers | `references/evidence_and_evolution_policy.md` and `workflow_skill_evolution.md`. |
| Modify or audit this skill package | `references/architecture.md`, `references/context_loading_policy.md`, and `references/path_policy.md`. |

## Non-Negotiables

- Load the smallest useful module set; normally one workflow plus one contract is enough to start.
- Keep modules high-cohesion: source discovery, corpus normalization, PDF analysis, synthesis, packaging, and target-paper reporting stay separate.
- Keep modules loosely coupled through CLI arguments and JSON/JSONL/Markdown contracts, not shared global state.
- Use package-relative paths, `Path(__file__)` roots, current workspace paths, or explicit user-provided paths. Do not hardcode machine-specific absolute paths.
- Treat downloaded PDFs and corpus folders as project files. Do not paste full PDF text into chat context; scripts must extract, chunk, save intermediate artifacts, and synthesize from manifests.
- In mode B, once reference PDFs/reviews/replies are downloaded, provided, or standardized as `project-run`/`local-pdf`, they are current project-internal files. Missing API keys, acpx, or external LLM backends must not block local corpus validation, PDF extraction, rule pre-pass, per-paper analysis folders, manifests, assistant-readable full-paper deep-reading records, anonymous synthesis, or packaging when the current assistant can process the files from disk.
- When the current assistant is the deep-reading route, use `references/assistant_local_deep_read_workflow.md`: prepare assistant-readable packets, read chunks from disk, write one JSON record per paper, validate/import those records, and then synthesize/package only after the manifest is complete.
- Backend status is not workflow status. `OPENAI_API_KEY`/`acpx` absence means only that an automated backend is unavailable; it does not mean local project-file analysis is unavailable.
- Never tell the user that a project-internal corpus cannot be analyzed merely because API/acpx/local-command automation is missing. Continue locally or name a concrete non-backend blocker, such as unreadable PDFs, missing files, or exhausted context after saved partial artifacts.
- Package anonymous synthesis only. Do not include old PDFs, raw review dumps, source caches, bytecode, temp folders, or project-run artifacts.
- Keep the two PDF modes separate: direct analysis produces a report about the uploaded paper; domain-seed mode only infers fields/subfields and then builds a specialized reusable skill.
- If a user uploads only a PDF with no mode, ask the two-choice clarification and stop before analysis or corpus building.
- For real reusable knowledge, every selected reference PDF needs a complete full-paper LLM deep-read before synthesis.
- Generated or final target-paper reports must ground claims in the target PDF and user-provided reviews/replies; packaged cases are analogies, not evidence.

## Commands

Build with explicit domains:

```bash
python scripts/build_domain_skill.py --skill-name <name> --focus-domains <domain> ... --years <year> ... --source-mode <project-run|local-pdf|openreview-iclr> --out-dir <dir>
```

Build a specialized skill when the user only has a target paper as the domain seed:

```bash
python scripts/build_domain_skill.py --skill-name <name> --target-paper <paper.pdf> --years <year> ... --source-mode <project-run|local-pdf|openreview-iclr> --out-dir <dir>
```

Validate modular packaging:

```bash
python scripts/validate_modularity.py --skill-dir <this-skill-dir>
```
