# Source Strategy: arXiv / Web Fallback

Use this strategy when papers do not have accessible OpenReview-style reviews or replies.

## When To Use

- The user asks for a broad conference/journal area but no review data exists.
- OpenReview metadata is unavailable or incomplete.
- The source is arXiv, publisher pages, project pages, Semantic Scholar-style metadata, or ordinary web search.

## Required Discipline

No real review evidence exists in this mode. All reviewer concerns must be labeled `simulated-review`.

## Search And Screening

Project-local search tools should:

1. search by domain keywords and incremental-risk terms;
2. inspect title and abstract before downloading;
3. download PDF only for plausible candidates;
4. extract PDF text and inspect intro/method/experiments;
5. classify candidates by visible signals:
   - combines existing components;
   - extends a known method to a new setting;
   - adapts a method with small changes;
   - engineering or efficiency optimization;
   - benchmark/evaluation contribution;
   - empirical improvement without clear mechanism.

## Required Status

Each paper's `source_status.json` must set:

```json
{
  "source_kind": "arxiv-web",
  "reviews_missing": true,
  "replies_missing": true,
  "review_attack_mode": "simulated-review-only"
}
```

## Handoff

After the project run is created, validate and initialize it like any other project corpus.
