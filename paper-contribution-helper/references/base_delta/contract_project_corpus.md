# Contract: Project Corpus Run

Use this contract for any corpus created outside the skill, including automatic OpenReview discovery, arXiv/web fallback, local PDF intake, or mixed user-provided materials.

## Boundary

Downloader/search logic belongs in the project workspace, not inside this skill. The skill consumes a completed project corpus run, validates it, and then performs per-paper analysis and reframing synthesis.

## Required Layout

```text
<project_run_dir>/
  config.json
  discovery/
    search_queries.jsonl
    discovered_papers.jsonl
    source_api_logs.jsonl
  index/
    all_candidates.csv
    screened_incremental_candidates.csv
    high_risk_candidates.csv
    category_summary.csv
  materials/
    _by_paper/<paper_key>/
      paper.pdf
      submission.json
      source_status.json
      official_reviews.json        # optional
      official_reviews.md          # optional
      meta_review.json             # optional
      meta_review.md               # optional
      decision.json                # optional
      decision.md                  # optional
      author_replies.json          # optional
      author_replies.md            # optional
      reviewer_followups.json      # optional
      public_comments.json         # optional
  logs/
    download_manifest.jsonl
    failures.jsonl
```

For local PDF intake, `discovery/`, `index/`, and `logs/` may be partial or missing, but `materials/_by_paper/<paper_key>/paper.pdf`, `submission.json`, and `source_status.json` are still required.

## Required `source_status.json`

Each paper folder must include:

```json
{
  "schema_version": "1.0",
  "source_kind": "iclr-openreview | openreview | arxiv-web | local-pdf | mixed",
  "domain_scope": "computer-science",
  "source_url": "",
  "pdf_available": true,
  "reviews_missing": false,
  "replies_missing": false,
  "review_attack_mode": "real-review | simulated-review-only",
  "download_status": "ok | partial | failed",
  "notes": []
}
```

If reviews or replies are absent, set `reviews_missing=true` or `replies_missing=true`. Do not omit the fields.

## Candidate Index Fields

Recommended index fields:

- `paper_key`
- `title`
- `year`
- `venue`
- `source_kind`
- `source_url`
- `categories`
- `risk_tier`
- `incremental_types`
- `screening_reason`
- `evidence_snippets`
- `pdf_available`
- `review_available`
- `reply_available`
- `material_dir`

## Validation

Run:

```bash
python scripts/validate_project_corpus.py --run-dir <project_run_dir>
```

Then initialize from the validated project run:

```bash
python scripts/initialize_from_project_corpus.py \
  --run-dir <project_run_dir> \
  --focus-domains <domain> ... \
  --years <year> ... \
  --source-kind <source_kind> \
  --domain-scope computer-science
```

Initialization is incomplete until `analysis/per_paper_analysis_manifest.jsonl` has one record per paper folder.
