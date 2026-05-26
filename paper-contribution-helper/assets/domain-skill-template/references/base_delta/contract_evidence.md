# Contract: Evidence And Anonymization

Use these labels:

- `paper-explicit`
- `latent-but-supported`
- `story-level reframing`
- `simulated-review`
- `future-boundary hook`
- `missing / not reported`
- `not inspected`

Rules:

- Do not fabricate experiments, numbers, proofs, citations, baselines, reviewer comments, author replies, decisions, or meta-review logic.
- Do not present simulated review concerns as real reviews.
- Do not turn future possibilities into completed contributions.
- Keep reusable cases anonymous: no paper titles, authors, forum ids, URLs, repository URLs, exact method names, or unique benchmark bundles.
- During initialization and evolution, every extracted/input paper must have a saved per-paper analysis report plus machine-readable intermediate artifacts.
- If official reviews, meta-reviews, decisions, or author replies exist, they must be analyzed and linked in the per-paper record.
- If any source is missing or unreadable, mark it as `missing / not reported` or `not inspected`; never infer that it was inspected.
- For project discovery or arXiv/web fallback, preserve search/download ledgers in the project run. The skill may consume them but must not pretend web-screened papers had real peer reviews.
- For local PDFs without supplied reviews/replies, set `review_attack_mode=simulated-review-only`.
