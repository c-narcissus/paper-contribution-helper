# Workflow: Knowledge Base Build

Use this workflow after startup inputs are known. It matches the effective initialization process: index the corpus, identify delta-sized/incremental candidates, extract evidence materials, generate reports, and update state.

Use this workflow for OpenReview/export zip roots or compatible local corpora. For a standardized project corpus run, use `contract_project_corpus.md` plus `initialize_from_project_corpus.py`. For raw local PDFs, use `workflow_local_pdf_intake.md` first.

## Inputs

Required:

- `corpus_source`: user-provided local directory containing accepted-paper zip exports or another compatible corpus source.
- `years`: one or more initialization years.
- `focus_domains`: one or more user-selected domains, categories, or keywords.

Optional:

- `source_kind`: defaults to `iclr-openreview`.
- `domain_scope`: defaults to `computer-science`.
- `material_tiers`: defaults to `high` and `medium`.
- `material_limit`: optional cap for a small first pass.
- `out_dir`: optional output directory; default is `outputs/delta_contribution_knowledge_base` relative to the execution directory.
- `state_dir`: optional state directory for testing or external integration; default is the current project's `.delta-contribution-reframer/state/` directory.

## Build Command

```bash
python scripts/build_incremental_knowledge_base.py \
  --corpus-source <corpus_source> \
  --source-kind iclr-openreview \
  --domain-scope computer-science \
  --year <year> \
  --focus-domains <focus_domain> ... \
  --material-tier high \
  --material-tier medium
```

For multiple years, repeat `--year`:

```bash
python scripts/build_incremental_knowledge_base.py \
  --corpus-source <corpus_source> \
  --source-kind iclr-openreview \
  --domain-scope computer-science \
  --year <year_a> \
  --year <year_b> \
  --focus-domains <focus_domain> ...
```

The builder calls `analyze_extracted_papers.py` by default after extracting selected materials. Do not pass `--skip-per-paper-analysis` for real initialization.

After per-paper analysis exists, synthesize reusable project-local resources:

```bash
python scripts/synthesize_initialized_resources.py \
  --run-dir <out_dir> \
  --focus-domains <focus_domain> ... \
  --years <year> ... \
  --source-kind iclr-openreview \
  --domain-scope computer-science
```

This step writes anonymous reusable knowledge under `.delta-contribution-reframer/references/` and updates project-local state so future skill use in this project does not depend on absolute project paths or the original downloaded PDFs.

## Output Contract

The builder must create these reusable artifacts:

- `index/incremental_all_index.csv`
- `index/incremental_all_index.jsonl`
- `index/incremental_low_novelty_candidates.csv`
- `index/incremental_core_candidates.csv`
- `index/incremental_high_risk_candidates.csv`
- `index/incremental_category_summary.csv`
- `index/incremental_category_type_matrix.csv`
- `materials/_by_paper/` for selected material tiers
- `materials/by_category/<category>/`
- `analysis/per_paper/<paper_key>/analysis.md`
- `analysis/per_paper/<paper_key>/pdf_text.txt`
- `analysis/per_paper/<paper_key>/source_ledger.json`
- `analysis/per_paper/<paper_key>/paper_sections.json`
- `analysis/per_paper/<paper_key>/review_reply_ledger.json`
- `analysis/per_paper/<paper_key>/claim_delta_matrix.json`
- `analysis/per_paper/<paper_key>/analysis_record.json`
- `analysis/per_paper_analysis_manifest.jsonl`
- `reports/per_paper_analysis_index.md`
- `reports/overview.md`
- `reports/category_reports/`
- `reports/type_reports/`
- `.delta-contribution-reframer/references/anonymous_casebook.jsonl`
- `.delta-contribution-reframer/references/per_pdf_report_synthesis.md`
- `.delta-contribution-reframer/references/domain_profile_<scope>.md`
- `.delta-contribution-reframer/state/knowledge_state.json`
- `.delta-contribution-reframer/state/initialization_state.json`

## Risk Labels

The builder assigns heuristic labels. Treat them as triage labels, not final judgments:

- `high`: explicit reviewer novelty/incrementality concern, strong A+B/C or minor-delta signal, or weak contribution/rating evidence.
- `medium`: plausible incremental or engineering/transfer/composition risk without severe explicit attack.
- `low`: no strong signal in the available metadata and reviews.

## Incremental Type Labels

Use these labels as reusable methodology hooks:

- `低创新性被明确质疑`
- `显式增量式工作`
- `A+B/C 组合式方法`
- `已有方法轻改/迁移`
- `工程优化`

The labels can overlap. A paper can be useful as a case even when only one label is present.

## Validation

After the build:

1. Confirm the command exited successfully.
2. Confirm `indexed_papers` is non-zero.
3. Confirm `.delta-contribution-reframer/state/knowledge_state.json` says `knowledge_available=true`.
4. Confirm at least one index file and `reports/overview.md` exist.
5. If extraction was requested, confirm selected material folders exist.
6. Confirm `analysis/per_paper_analysis_manifest.jsonl` has one row for each extracted folder under `materials/_by_paper/`.
7. Confirm `reports/per_paper_analysis_index.md` exists and lists every paper.
8. Confirm `.delta-contribution-reframer/references/anonymous_casebook.jsonl` and `.delta-contribution-reframer/references/per_pdf_report_synthesis.md` are non-empty.
9. Confirm state files do not contain machine-specific absolute paths as runtime resource dependencies.
10. Report missing PDFs, unreadable PDFs, missing reviews, and missing replies as coverage gaps instead of pretending the evidence exists.

## Privacy And Reuse

The build artifacts may contain paper titles, forum URLs, and review text for local evidence tracing. Do not expose those details in reusable casebooks or user-facing methodology examples unless the user explicitly asks for non-anonymous source inspection. Public-facing examples must be anonymized.

## Runtime Dependency Boundary

The initialized skill should run from the current project's `.delta-contribution-reframer/references/` and `.delta-contribution-reframer/state/` files for generic reframing and reviewer-defense work. Original PDFs are required only for:

- initializing or evolving the knowledge base;
- re-checking provenance;
- analyzing a new target paper with source-grounded claims.
