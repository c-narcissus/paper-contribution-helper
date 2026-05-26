# Workflow: Target Paper Reframing

Use after initialization, or for a single user-provided paper that should be analyzed without updating the reusable knowledge base. The quality bar is defined in `contract_target_report_quality.md`; follow it unless the user explicitly asks for a short answer.

## Pre-Pass

1. Build a source ledger for the PDF, supplied reviews/replies, metadata, and unread sources.
2. Extract and inspect the PDF text first. Save intermediate artifacts when a writable output directory is available.
3. Run `scripts/analyze_new_pdf.py` when available, but treat it as a pre-pass only. Its pattern hits and scaffold are inputs to the final report, not the final report itself.
4. Load `references/anonymous_casebook.jsonl` and `references/per_pdf_report_synthesis.md` only as anonymous analogy resources. Do not use them as evidence about the target paper.

## Final Report

1. State language and evidence rules.
2. State readability rules: explain abstract packaging logic in plain Chinese first, then give the technical thesis, example/analogy, evidence anchor, and boundary.
3. Build a deep evidence base from the target PDF: target regime, broken assumptions, modules, tables/figures/appendix anchors, and claim boundaries.
4. Diagnose the weak surface delta and the stronger actual delta. Explain why the weak framing invites novelty, A+B/C, mechanism, baseline, or cost attacks.
5. Build a claim-support matrix that maps claims to PDF evidence, risks, and revision actions.
6. Mine latent but evidence-supported contributions. Label each as `paper-explicit`, `latent-but-supported`, `story-level reframing`, or `future-boundary hook`.
7. Produce top-conference story reconstruction outputs: problem equation, contribution ladder, abstract rewrite, intro framing, contribution bullets, related-work boundary, method overview rewrite, and figure/caption direction.
8. Produce a ranked Story Option Board with six route slots by default. If fewer than six routes are safe, mark the unsupported slots and explain the evidence limitation.
9. Include a route comparison table over novelty defense, evidence fit, A+B/C resistance, baseline control, mechanism control, cost/reproducibility control, rewrite cost, new-experiment pressure, and best use.
10. Expand the main routes. For each route, state plain-language meaning, construction reason, core thesis, concrete example/analogy, rewrite targets, usable evidence, risk boundary, anonymous analogy if available, and one ready-to-paste English snippet when safe.
11. Provide a recommended route combination: default main thesis, method/Figure route, related-work/baseline route, experiment-organization route, limitation/discussion route, and minimum Tier 0 combination under page pressure.
12. Simulate reviewer attacks with `simulated-review` labels unless real reviews are supplied. For every attack, include why the reviewer will ask, manuscript trigger, strong defense posture, and no-new-experiment repair.
13. Localize manuscript triggers: current claims, phrases, missing diagnostics, unclear comparison contracts, weak ablation framing, unsupported privacy/safety or cost claims, or evidence gaps that cause each attack.
14. Produce Tier 0 / Tier 1 / Tier 2 revision priorities. Each item needs manuscript location, evidence reused or needed, reviewer-defense purpose, and ready-to-paste English if applicable.
15. Draft English manuscript-facing and rebuttal snippets. Keep them evidence-bounded and include risky wording to avoid.
16. Add anonymous case analogies with original weak pattern, effective packaging move, borrowing path, and boundary.
17. Add residual risks and safe/unsafe claim boundaries for mechanism, privacy/safety, cost, scope/generalization, and reproducibility.

Do not ship a generic target report that merely follows section names. The final report must make paper-specific packaging decisions and explain the tradeoffs among story routes.
