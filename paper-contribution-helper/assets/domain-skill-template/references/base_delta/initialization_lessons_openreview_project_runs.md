# Initialization Lessons: OpenReview Project Runs

This note records reusable engineering lessons from a completed ICLR OpenReview initialization. It is intentionally implementation-oriented but does not embed downloader code; download/search implementations belong in the project workspace.

## Effective Pipeline

1. Treat a source label such as `iclr(openview)` as a source preference, not as a corpus path.
2. Create a project-local run directory with the `contract_project_corpus.md` layout.
3. Discover all accepted papers for the requested years before screening.
4. Screen by title, abstract, keywords, primary area, and available review/meta-review language.
5. Fetch forum/review bundles for a larger preselection pool before applying the final cap.
6. Apply the user cap after review-aware re-ranking. In the tested run, `max_candidates_per_year=100` yielded a 200-paper corpus across two years.
7. Download and validate PDFs only for the final selected papers.
8. Run `validate_project_corpus.py`, then `initialize_from_project_corpus.py`.
9. Run `synthesize_initialized_resources.py` or let `initialize_from_project_corpus.py` call it, so reusable skill knowledge becomes project-local and anonymous.

Before step 3, tell the user the default run directory, where PDFs and reports will be written, and the default analysis cap. Ask whether to change those settings.

## Reusable Scoring Signals

Useful high-recall domain signals:

- title, keyword, and primary-area hits get higher weight than abstract hits;
- multiple domain labels should be allowed because FL and semi-supervised papers can overlap;
- preselection should be wider than the final cap to leave room for review-aware sorting.

When the user provides multiple domains, use balanced per-domain targets by default. A high-recall domain should not consume the whole selected set unless the user explicitly asks for pure score ranking. Overlapping papers can count toward several domains but should only be downloaded once.

Useful delta-risk signals:

- explicit reviewer phrases about novelty, contribution, incremental value, ablation, baseline fairness, experiment scope, reproducibility, and mechanism clarity;
- low contribution scores when a source exposes them;
- A+B/C combination wording, light adaptation wording, engineering/efficiency wording, benchmark/protocol wording;
- meta-review text that explains why a paper was accepted despite concerns.

## Rate Limits And Robustness

OpenReview-style APIs may return rate limits during forum-note fetches. Project tools should:

- use bounded concurrency;
- retry 429 responses after the reset interval or with conservative exponential backoff;
- append every retry/failure to `discovery/source_api_logs.jsonl`;
- avoid treating transient retry messages as fatal if the final material folders validate.

## Skill Boundary

Do not store source-specific downloader code, API caches, or large downloaded PDFs inside this skill. The skill should consume a completed project corpus and then store only anonymized reusable synthesis in the current project's `.delta-contribution-reframer/references/`.

The initialized skill is self-contained for future generic reframing after these files are present:

- `.delta-contribution-reframer/references/anonymous_casebook.jsonl`
- `.delta-contribution-reframer/references/per_pdf_report_synthesis.md`
- one or more `.delta-contribution-reframer/references/domain_profile_*.md` files
- `.delta-contribution-reframer/state/knowledge_state.json` with `knowledge_available=true`

The original PDFs remain useful for provenance and re-analysis, but they are not runtime dependencies for generic story, rebuttal, or reviewer-defense guidance.
