# Workflow: Startup Initialization

Use this workflow before building reusable knowledge.

State is project-local. Run `scripts/startup_check.py` from the target project/workspace; it checks `.delta-contribution-reframer/state/` and `.delta-contribution-reframer/references/` in that project. Do not decide initialization status from the global Codex skill installation directory.

## Steps

1. Run `scripts/startup_check.py`.
2. If `knowledge_available=false`, ask for:
   - either a target paper PDF for domain inference, or explicit focus domains;
   - years;
   - corpus source.
   Default assumptions are `source_kind=iclr-openreview` and `domain_scope=computer-science`; still require a concrete local corpus source or download target from the user. Do not force the user to name domains when they can upload the paper they want to reframe.
3. Before starting any download, discovery, or PDF standardization, show an initialization confirmation note:
   - default analysis cap: `100` selected/analyzed papers per year total unless the user changes it;
   - if no focus domains are provided, first deep-read the target paper and infer 1-3 searchable domains/subfields;
   - if multiple focus domains are provided or inferred, selection should be balanced across domains before final evidence-risk sorting;
   - default project run directory: `runs/<source_kind>_<domain_slug>_<years>` under the current project/workspace unless the user gives another location;
   - downloaded PDFs will be placed under `<project_run_dir>/materials/_by_paper/<paper_key>/paper.pdf`;
   - per-paper analysis reports will be placed under `<project_run_dir>/analysis/per_paper/<paper_key>/analysis.md`;
   - indexes and summaries will be placed under `<project_run_dir>/index/` and `<project_run_dir>/reports/`;
   - reusable anonymous skill knowledge will be copied into `.delta-contribution-reframer/references/` after initialization;
   - ask whether the user wants to change the run directory, per-year cap, or balancing policy.
4. Route by source mode:
   - local PDF or PDF folder: use `workflow_local_pdf_intake.md`;
   - existing project corpus run: validate with `contract_project_corpus.md`, then run `initialize_from_project_corpus.py`;
   - OpenReview/export zip root: continue with `scan_corpus_catalog.py` and `workflow_knowledge_base_build.md`;
   - no local source: use `workflow_project_discovery.md` and ask for a project download/run directory.
5. If the user provides an OpenReview/export corpus source, run `scripts/scan_corpus_catalog.py --corpus-source <path>`.
6. Show available fields/years/keywords from `state/corpus_catalog.md`.
7. Run `scripts/configure_initialization.py --corpus-source <path> --focus-domains ... --years ... --source-kind iclr-openreview --domain-scope computer-science`, using either user-supplied domains or the domains inferred from the target paper.
8. Continue with `workflow_knowledge_base_build.md`.
9. Do not mark initialization complete until extraction/synthesis produces non-empty knowledge resources and per-paper analysis coverage.

## Required Build Command Shape

After the user confirms the domains and years, or after target-paper domain inference produces the domains, run the builder with an explicit corpus source and explicit years:

```bash
python scripts/build_incremental_knowledge_base.py \
  --corpus-source <corpus_source> \
  --source-kind iclr-openreview \
  --domain-scope computer-science \
  --year <year> \
  --focus-domains <domain_or_keyword> ... \
  --material-tier high \
  --material-tier medium
```

Repeat `--year` for multiple years. This command must run per-paper analysis by default. Use `--no-extract` or `--skip-per-paper-analysis` only for a dry run or catalog-only smoke test; it must not be treated as a completed reusable knowledge-base initialization.

## Required Message When Not Initialized

```text
当前模板 skill 还没有本地论文提取知识库，必须先初始化。

请提供：
1. 目标论文 PDF（我会先精读并推断 1-3 个领域/子领域），或直接给关注领域：
2. 初始化参考年份：
3. 论文来源：

默认设置：每年最多分析 100 篇；多个领域会尽量均衡抽样；PDF 会放在 `<project_run_dir>/materials/_by_paper/`，逐篇分析报告会放在 `<project_run_dir>/analysis/per_paper/`。
如果需要，我可以在下载/分析前修改项目 run 目录、每年篇数上限或领域配额策略。
```
