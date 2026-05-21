# Workflow: Project Discovery And Download

Use when no suitable local corpus exists and the user wants automatic search/download before skill initialization.

## Rule

Do not store downloader implementation inside this skill. Create or use project-local tools under the user's workspace, then validate their output against `contract_project_corpus.md`.

## Default Discovery Target

- Source kind: `iclr-openreview`
- Domain scope: `computer-science`
- Preferred paper set: accepted papers with public OpenReview metadata, official reviews, meta-review/decision, author replies when available.

## User Inputs

Ask for:

- focus domains, e.g. `LLM`, `CV`, `NLP`, `RL`, `FL`, `VLM`, `VLA`, `Agent`, `Semi-supervised`;
- years;
- source preference, default `ICLR OpenReview`;
- project run directory or download target;
- desired candidate count per domain or total cap.

If the user does not specify a cap, state the default before running discovery:

- default cap: `100` selected/analyzed papers per year total;
- default run directory: `runs/<source_kind>_<domain_slug>_<years>` in the current project/workspace;
- downloaded PDFs: `<project_run_dir>/materials/_by_paper/<paper_key>/paper.pdf`;
- source metadata/reviews/replies: the same paper folder under `materials/_by_paper/<paper_key>/`;
- per-paper analysis reports: `<project_run_dir>/analysis/per_paper/<paper_key>/analysis.md`;
- index and summary reports: `<project_run_dir>/index/` and `<project_run_dir>/reports/`;
- reusable anonymous project-local resources after initialization: `.delta-contribution-reframer/references/anonymous_casebook.jsonl`, `.delta-contribution-reframer/references/per_pdf_report_synthesis.md`, and `.delta-contribution-reframer/references/domain_profile_*.md`.

Ask whether the user wants to change the run directory, the per-year cap, or the domain-balancing policy before starting downloads.

## Multi-Domain Balancing

When multiple focus domains are provided, do not let one high-recall domain consume nearly all selected papers by default. Use a balanced target unless the user requests pure score ranking:

1. set `max_candidates_per_year=100` unless the user changes it;
2. compute a target quota of roughly `max_candidates_per_year / number_of_focus_domains` for each domain;
3. allow overlap papers to count toward every matched domain but store/download them only once;
4. first fill under-represented domains with the highest evidence-risk candidates in that domain;
5. after each domain reaches its target or exhausts candidates, fill remaining slots by global evidence-risk score;
6. report final per-domain counts and overlap counts after selection.

If a domain has too few candidates, reallocate its unused quota to the other domains and state that in the summary.

## Project Tool Contract

A project downloader/indexer should:

1. discover papers from the selected source;
2. save raw API/search logs under `discovery/`;
3. create `index/all_candidates.csv`;
4. screen by abstract, keywords, primary area, and review/meta-review concern text;
5. assign `categories`, `risk_tier`, and `incremental_types`;
6. download selected PDFs and available review/reply materials into `materials/_by_paper/<paper_key>/`;
7. write `source_status.json` for every paper;
8. write `download_manifest.jsonl` and `failures.jsonl`.

## Reusable Project-Local Pattern

The following pattern is reusable across domains and years, but the implementation belongs in the project workspace, not in this skill directory:

1. fetch accepted submissions by source-specific venue or corpus id;
2. screen broadly using title, abstract, keywords, primary area, and any already visible decision/review text;
3. preselect more papers than the final cap, then fetch forum/review bundles for the preselected set;
4. re-rank by domain score plus explicit novelty/contribution/ablation/baseline/scope concerns;
5. enforce the user-requested cap after re-ranking, e.g. `max_candidates_per_year=100`, using balanced domain quotas when multiple focus domains are present;
6. download PDFs and write one material folder per paper following `contract_project_corpus.md`;
7. log rate-limit retries and download failures, but keep the final material set valid: every selected paper must have `paper.pdf`, `submission.json`, and `source_status.json`;
8. run skill validation and initialization only after the project run is complete.

For OpenReview-style sources, practical implementation notes from the working initialization:

- public accepted papers can usually be discovered through a venue/content id such as `content.venueid`;
- official reviews, meta-reviews, decisions, author replies, reviewer follow-ups, and public comments should be stored as separate JSON/Markdown files when available;
- API rate limits are normal; use bounded workers, retry on 429, and record retry logs in `discovery/source_api_logs.jsonl`;
- keep the downloader resumable or at least append-only in logs so an interrupted run can be audited;
- do not mark a project corpus valid if a selected paper is missing its PDF unless the missing PDF is explicitly represented as partial evidence and accepted by the downstream contract.

## Screening Priority

Prefer papers with real reviewer evidence:

1. explicit novelty or contribution concerns in reviews/meta-review;
2. explicit incremental/minor-extension wording;
3. A+B/C combination concerns;
4. method transfer/light adaptation signals;
5. engineering/system/efficiency optimization signals;
6. benchmark/evaluation-protocol driven contributions;
7. accepted despite low contribution or novelty dispute.

If reviews are unavailable, screen by abstract and PDF text. Mark the paper as `simulated-review-only`.

## Handoff To Skill

After project tools finish, run:

```bash
python scripts/validate_project_corpus.py --run-dir <project_run_dir>
python scripts/initialize_from_project_corpus.py --run-dir <project_run_dir> --focus-domains <domain> ... --years <year> ...
```

The skill then performs per-paper PDF/review/reply analysis and reframing synthesis. `initialize_from_project_corpus.py` calls `synthesize_initialized_resources.py` so reusable knowledge is copied into project-local anonymous resources under `.delta-contribution-reframer/` and state does not depend on the project run path.
