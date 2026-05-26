# Source Modes

All source modes may be driven by explicit `--focus-domains` or by `--target-paper` domain inference. When `--target-paper` is used, the factory first deep-reads the target PDF, infers 1-3 searchable focus domains/subfields, and then applies those labels to the selected source mode.

Primary source preference: use downloaded project files directly whenever available. Load `references/project_corpus_direct_workflow.md` before using online discovery.

## `project-run`

Primary path for an already-downloaded, already-normalized corpus.

Consume an existing project corpus run with:

```text
materials/_by_paper/<paper_key>/paper.pdf
materials/_by_paper/<paper_key>/submission.json
materials/_by_paper/<paper_key>/source_status.json
```

Reviews and replies are optional but should be included when available.

The existing run must still pass the factory's analysis stage. If its `analysis/per_paper_analysis_manifest.jsonl` is old or rule-only, rebuild the analysis so every selected PDF receives a full-paper LLM deep-read before synthesis.

## `local-pdf`

Primary path for a downloaded PDF folder that has not yet been normalized.

Standardize one PDF or a PDF folder into a project corpus run using the embedded engine. If reviews/replies are absent, downstream review concerns must be labeled `simulated-review`.

Local PDFs are valid corpus sources only after text extraction and the required LLM deep-reading pass complete for every selected PDF.

## `openreview-iclr`

Use the integrated OpenReview adapter to discover accepted ICLR papers by `venueid`, screen by focus-domain keywords, download selected PDFs and public review/reply materials, then produce the standard project corpus run.

Use this only when no suitable local corpus exists or when the user explicitly wants discovery/download.

When the focus domains came from `--target-paper`, treat them as screening labels only. They should affect candidate retrieval and balancing, but they must not be reused later as evidence about the target paper's contribution.

This source mode requires network access and the `openreview-py` and `requests` Python packages.

All source modes share the same completion rule: no initialized generated skill may be packaged from a real corpus unless every selected paper has `llm_deep_reading.status="complete"` and `deep_read_workflow_alignment="llm-full-paper-deep-read"` in the per-paper manifest.
