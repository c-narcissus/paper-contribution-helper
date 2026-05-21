# Contract: Startup State And Initialization Gate

This skill starts empty. It must not assume local PDFs, accepted-paper zips, extracted reviews, or paper-derived knowledge already exist.

## Project-Local State Files

State is project-local. The default state root is `.delta-contribution-reframer/` under the current project/workspace. Do not use the global Codex skill installation directory as the source of truth for whether a project has been initialized.

- `.delta-contribution-reframer/state/skill_state.json`: top-level status and startup-gate settings.
- `.delta-contribution-reframer/state/initialization_state.json`: whether required initialization inputs have been configured, whether the knowledge builder has run, and whether extraction/synthesis is complete.
- `.delta-contribution-reframer/state/evolution_state.json`: whether knowledge evolution is idle or running.
- `.delta-contribution-reframer/state/knowledge_state.json`: whether local extracted knowledge exists.
- `.delta-contribution-reframer/state/per_paper_analysis_state.json`: coverage of mandatory per-paper PDF/review/reply analysis.
- `.delta-contribution-reframer/state/corpus_catalog.json`: generated catalog for user-provided corpus.
- `.delta-contribution-reframer/state/corpus_catalog.md`: human-readable catalog of available fields/years/keywords.
- `.delta-contribution-reframer/references/anonymous_casebook.jsonl`: project-local anonymous reusable cases.
- `.delta-contribution-reframer/references/per_pdf_report_synthesis.md`: project-local reusable synthesis.

## Path Portability

State files must not create runtime dependencies on machine-specific absolute paths. Prefer project-relative resource paths such as `references/anonymous_casebook.jsonl` inside `.delta-contribution-reframer/`.

Allowed exceptions:

- a user-provided corpus path may be used transiently during the current initialization command;
- project-run paths may appear in project-local reports outside the skill;
- per-paper provenance can remain in the external project run.

After synthesis, project-local state should expose reusable resources from `.delta-contribution-reframer/references/` and set any external project-run pointer to `null` or an explanatory non-path value. The initialized project must remain usable after the original project run or PDFs are moved, as long as the project-local anonymous resources are present.

## Mandatory Initialization Inputs

When local knowledge is missing, ask for all three, but allow the first item to be inferred from a target paper:

```text
目标论文 PDF（用于推断 1-3 个领域/子领域）或关注领域 / target paper PDF or focus domains:
初始化参考年份 / years:
论文来源 / corpus source:
```

`corpus source` may be:

- local PDF or PDF folder;
- project corpus run created by project-local discovery/download tools;
- local directory of PDFs / metadata / reviews;
- local accepted-paper zip root;
- downloaded corpus directory;
- a user-provided manifest.

Default source kind is `iclr-openreview`. Default domain scope is `computer-science`. Do not hardcode any machine-specific path. If an ICLR OpenReview corpus must be downloaded, ask the user to provide the download target/source or run their own downloader before initialization.

## Startup Gate

If `knowledge_available=false`, do not proceed to target-paper packaging except for analyzing a single user-provided paper. For building reusable skill knowledge, initialize first.

## Completion Criteria

Initialization is complete only when all of the following are true:

- the user supplied years and corpus source, plus either explicit focus domains or target-paper-inferred focus domains;
- `scan_corpus_catalog.py` produced a readable corpus catalog;
- `configure_initialization.py` saved the initialization intent;
- `build_incremental_knowledge_base.py` produced non-empty index files under the configured output directory;
- `analyze_extracted_papers.py` produced a manifest row and `analysis.md` report for every extracted paper material folder;
- `reports/overview.md` and at least one category/type report exist;
- `reports/per_paper_analysis_index.md` exists;
- `.delta-contribution-reframer/state/knowledge_state.json` has `knowledge_available=true`;
- `.delta-contribution-reframer/state/initialization_state.json` has `initialized=true` and points to the generated output directory.

Configured-but-not-built is not initialized. Corpus-level indexing without per-paper analysis is not initialized. A dry run with `--no-extract` or `--skip-per-paper-analysis` can validate indexing, but it is not enough for a reusable case/report knowledge base unless the user explicitly asks for an index-only skill.

If a PDF is missing or unreadable, the per-paper report must still exist with `partial` status and an explicit coverage warning. Do not silently skip it.

## Prompt Menu

Show this menu when initialization is missing or the user asks how to use the skill:

- `初始化知识库：目标论文PDF=<...>（自动推断领域）或关注领域=<...>，年份=<...>，论文来源=<...>`
- `扫描我的论文语料目录，列出可选领域和年份：<path>`
- `分析这篇 PDF，并输出可下载报告：<path>`
- `生成 3-6 条顶会故事路线，并排序比较`
- `模拟审稿人攻击，给出不增加实验的修改方案`
- `根据 reviewer comments 写 rebuttal 防守策略`
- `把这篇新论文作为样例摄取，判断是否纳入 skill 知识库`
- `查看初始化状态和 evolving casebook`
