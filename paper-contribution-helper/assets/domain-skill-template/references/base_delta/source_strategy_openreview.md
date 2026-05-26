# Source Strategy: OpenReview

Use this strategy for ICLR/OpenReview-style sources.

## Priority

OpenReview is the preferred source when the goal is to learn how incremental work survived review, because it can expose paper metadata, official reviews, meta-review, decision, discussion, and author replies.

## Project Downloader Expectations

The project-local downloader should collect:

- title, abstract, keywords, TL;DR, primary area;
- venue/year and decision;
- paper PDF;
- official reviews;
- meta-review and decision;
- author replies and public discussion when available;
- source ids/URLs in local ledgers only.

## Screening Signals

Use review/meta-review text first:

- novelty is limited / lack of novelty;
- contribution is incremental / minor;
- method is a simple combination;
- mechanism is unclear;
- baseline comparison is incomplete or unfair;
- ablation does not prove necessity;
- engineering/system contribution is useful but not conceptually new.

Use metadata/PDF text only as fallback when review material is missing.

## Output

Save OpenReview results into the project corpus contract. Do not expose paper titles, authors, source ids, or URLs in reusable anonymized casebooks.
