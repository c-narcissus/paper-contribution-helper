# Workflow: Target-Paper Domain Inference

Use when initialization or specialized reusable skill generation needs focus domains but the user prefers to upload the paper they want to reframe.

In this workflow, that PDF is a domain seed only. It is not a request to produce contribution packaging, story routes, reviewer attacks, rebuttal text, or manuscript edits.

## Goal

Infer the most useful search/filter labels from the target paper before corpus discovery. Return at least 1 and at most 3 focus domains or subfields.

## Steps

1. Extract the whole target PDF text.
2. Read the paper with a domain-identification lens, including method, setting, assumptions, experiments, keywords, related-work positioning, and claimed contribution.
3. Produce 1-3 concise labels suitable for corpus filtering, preferably with subfields.
4. For each label, record paper-grounded evidence and useful query terms.
5. Ask the user to approve or adjust the labels before long downloads or large corpus analysis when the cost is nontrivial.
6. Use the approved/inferred labels anywhere the initialization workflow asks for `--focus-domains`.

## Output Contract

```json
{
  "schema_version": "1.0",
  "inferred_focus_domains": ["<domain or subfield>", "<optional domain>", "<optional domain>"],
  "domain_rationale": [
    {
      "focus_domain": "<label>",
      "why_it_matches": "<short paper-grounded reason>",
      "evidence": ["<paper evidence anchor>"],
      "useful_query_terms": ["<term>"]
    }
  ],
  "rejected_or_too_broad_domains": [],
  "uncertainty_notes": []
}
```

## Boundary

The inferred domains are routing metadata only. They are not evidence for claims about novelty, contribution, or reviewer risk. Target-paper reports must still ground those claims in the target PDF and any user-supplied reviews/replies.
