# Usage Workflows

## PDF Mode Selection

If the user provides a PDF without saying how to use it, ask whether they want:

1. Direct target-paper analysis: contribution packaging, novelty risk, story routes, reviewer attacks, and revision/rebuttal help.
2. Domain-seed initialization: use the PDF only to infer fields/subfields, then screen reference materials and generate specialized reusable skill knowledge.

Do not run extraction, target-paper reporting, or corpus analysis until this choice is clear.

## Reframe A New Paper

Follow `references/base_delta/workflow_target_paper_reframing.md` and `references/base_delta/contract_target_report_quality.md`. `scripts/analyze_new_pdf.py` is only an extraction and pattern-detection pre-pass; do not treat its output as the final analysis.

The pre-pass writes evidence artifacts under the project-local hidden overlay and also reports a `public_report` path in the current workspace. Save the human-facing final report to that public path. When replying to the user, link to the public report path with forward slashes as an absolute Markdown file link; do not use the hidden overlay path as the primary link.

Required final report sections:

1. State language and evidence labels.
2. State readability labels: plain-language explanation first, then technical thesis, example/analogy, evidence anchor, and boundary.
3. Build a deep evidence base from the target PDF.
4. Diagnose the weak surface delta and stronger actual delta.
5. Build claim-support matrix.
6. Mine latent but evidence-supported contributions with labels: `paper-explicit`, `latent-but-supported`, `story-level reframing`, and `future-boundary hook`.
7. Produce top-conference story reconstruction: problem equation, contribution ladder, abstract rewrite, intro framing, contribution bullets, related-work boundary, method overview rewrite, and figure/caption direction.
8. Produce six ranked story-route slots by default plus a comparison table. If fewer than six are defensible, keep unsupported slots visible and explain why.
9. Expand the main routes with plain-language meaning, construction reason, core thesis, concrete example/analogy, rewrite targets, usable evidence, risk boundary, anonymous analogy if available, and ready-to-paste English snippet when safe.
10. Provide a recommended route combination and a minimum Tier 0 combination under page pressure.
11. Simulate reviewer attacks with `simulated-review` labels unless real reviews are supplied. Include why the reviewer will ask, manuscript trigger, strong defense posture, and no-new-experiment repair.
12. Localize manuscript triggers that cause each attack.
13. Produce Tier 0 / Tier 1 / Tier 2 revision priorities with action, manuscript location, evidence reused or needed, reviewer-defense purpose, and ready-to-paste English if applicable.
14. Draft English manuscript-facing and rebuttal snippets, plus risky wording to avoid.
15. Add an anonymous case appendix with borrowing path and boundary.
16. Add residual risks with safe/unsafe claim boundaries.
17. Separate target-paper evidence from base-corpus analogies.

Use `references/per_pdf_report_synthesis.md`, `references/llm_deep_read_synthesis.md`, and `references/anonymous_casebook.jsonl` only as anonymous analogy resources, not as evidence about the new target paper.

## Initialize A New Corpus

This workflow is for generating or refreshing specialized reusable knowledge, not for producing a report about one uploaded PDF. If the user supplies a target PDF here, treat it as a domain seed only.

When the user has downloaded PDFs, metadata, reviews, replies, or an existing run, use `references/project_corpus_direct_workflow.md` as the primary route. If no automated callback backend is available and the current assistant should do the reading, use `references/assistant_local_deep_read_workflow.md`. Do not paste full PDFs or extracted full text into chat context; use project files, chunking, per-paper intermediate artifacts, and manifests.

Once a corpus exists as `project-run` or standardized `local-pdf`, it is project-internal. If no API key/local command/ACP/JSONL backend is available, continue through validation, extraction, rule pre-pass, per-paper folders, manifest rows, and explicit `not_run` or `failed` LLM status. If the current assistant can read the project files, continue into local-file full-paper deep reading and update the manifest. Stop only before anonymous synthesis and final skill packaging when the manifest completion contract is still unsatisfied.

Do not report missing automation as a reason the project-internal corpus cannot be analyzed. Missing automation can explain only why automated batch execution is unavailable.

Use the embedded engine in this order:

1. Standardize or discover a project corpus. Prefer `project-run` for an existing normalized corpus and `local-pdf` for a downloaded PDF folder.
2. Run `validate_project_corpus.py`.
3. Run `analyze_extracted_papers.py` with `--llm-deep-read-mode required`.
4. Use `openai-responses`, `openai-chat`, `command`, or `jsonl` as the normal LLM provider. Use `command-file` with `scripts/acp_command_file_bridge.py` only when no API key/local command backend exists but ACP/acpx is available.
5. If the current assistant writes the deep-read records, prepare packets with `prepare_assistant_deep_read_packets.py`, validate/import them with `import_assistant_deep_read_records.py`, then confirm every selected paper has `llm_deep_reading.status=complete` in `analysis/per_paper_analysis_manifest.jsonl`.
6. Run `synthesize_initialized_resources.py`.

Do not package a new initialized skill if any selected PDF is only rule-analyzed. The required corpus analysis is PDF text extraction plus full-paper LLM deep-reading plus delta-contribution reframing.

## Simulate Reviewer Attacks

Use `simulated-review` unless real reviews are supplied. Focus on novelty, mechanism, baseline fairness, ablation, scope, cost, and reproducibility.

## Rebuttal Planning

Ground rebuttal points in real reviewer comments when available. If comments are absent, provide pre-submission defense rather than pretending rebuttal evidence exists.
