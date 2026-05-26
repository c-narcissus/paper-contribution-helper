# Contract: Target Report Quality

Generated skills must not answer a target-paper PDF request with a generic extraction summary. The final report must behave like an author-side incremental-paper reframing report: it should diagnose why the paper looks incremental, recover a stronger but evidence-bounded contribution, and prepare reviewer defense.

## Minimum Report Shape

A full target-paper report must include these sections unless the user explicitly asks for a shorter diagnostic:

1. Language, evidence, and readability contract.
2. Deep evidence base grounded in the target PDF and supplied reviews/replies.
3. Strong packaging diagnosis: the weak surface delta, the stronger actual delta, and why the surface framing invites reviewer attack.
4. Latent contribution mining: identify paper-explicit, latent-but-supported, story-level reframing, and future-boundary hook contributions without fabricating evidence.
5. Top-conference story reconstruction: problem equation, contribution ladder, abstract/intro/contribution bullets, related-work boundary, method overview, and figure/caption rewrite direction.
6. Story-route candidate board with six ranked route slots by default. If fewer than six are defensible, explicitly mark which routes are unsupported and why. Do not silently shrink the board.
7. Route comparison table over novelty defense, evidence fit, A+B/C resistance, baseline control, mechanism control, cost/reproducibility control, rewrite cost, new-experiment pressure, and best use.
8. Per-route expansion for the high-value routes: plain-language explanation, construction reason, core thesis, rewrite targets, usable evidence, concrete example/analogy, risk boundary, anonymous analogy if available, and ready-to-paste English snippet.
9. Recommended route combination: default main route, method/Figure route, related-work/baseline-defense route, experiment-organization route, limitation/discussion route, and minimum Tier 0 combination under page pressure.
10. Reviewer attack preplay with `simulated-review` labels unless real reviews are supplied. The attack table must include why the reviewer will ask, manuscript trigger, strong defense posture, and no-new-experiment repair.
11. Manuscript trigger localization: which current claims, phrases, missing controls, unclear comparison contracts, missing diagnostics, or evidence gaps cause each attack.
12. Tier 0 / Tier 1 / Tier 2 revision plan. Each tier must name action, manuscript location, evidence reused or needed, reviewer-defense purpose, and ready-to-paste English when applicable.
13. Rebuttal pattern library covering novelty/incrementality, A+B/C combination, baseline fairness, mechanism evidence, cost/scalability, and reproducibility when relevant. Each pattern must include defense posture, submit-ready English, risky wording to avoid, and why it is risky.
14. Anonymous case appendix using packaged casebook entries only as analogies, never as target-paper evidence. Each analogy must state the original weak pattern, effective packaging move, borrowing path for the target paper, and boundary.
15. Residual risk and evidence gaps. Preserve safe claim boundaries for mechanism, privacy/safety, cost, scope/generalization, and reproducibility.

## Quality Bar

- The report must be paper-specific. Name the target regime, broken assumptions, modules, evidence anchors, tables/figures/appendix items, and claim boundaries from the target PDF.
- The report must be reader-friendly without becoming shallower. For every abstract story route or contribution ladder, use the pattern: plain-language version -> technical thesis -> concrete example or analogy -> evidence anchor -> boundary.
- Explain why each story route matters in words an author can immediately understand. Avoid jargon-only route names.
- Do not list modules as the contribution. Explain the interaction, failure mode, interface, or constrained-regime repair that makes the modules necessary together.
- Do not stop at "missing evidence". Convert each gap into a concrete revision action and a reviewer-defense purpose.
- Do not stop at a route list. A route only counts if it has a plain-language explanation, thesis, evidence anchors, rewrite target, boundary, and snippet or explicit reason why no snippet is safe.
- Do not stop at attack names. An attack only counts if it is mapped to a manuscript trigger and a no-new-experiment repair.
- Include concrete output artifacts from the story reconstruction: problem equation, contribution ladder, abstract rewrite, intro framing, contribution bullets, related-work boundary, method overview, and figure/caption direction.
- Include manuscript-facing English snippets only where they can be directly used in the paper or rebuttal.
- Use Chinese for diagnosis, reasoning, ranking, risks, anonymous analogies, and revision planning. Use English only for manuscript-facing and rebuttal-ready snippets.
- If the PDF text extraction is weak, say so and degrade the report to a partial audit rather than inventing evidence.

## Failure Modes To Avoid

- Generic 10-section reports that could fit any paper.
- Reports that are technically complete but hard to read because story routes are only labels or slogans.
- Story sections that omit examples, analogies, or "what this means in plain words" explanations.
- Reports that skip problem equation, contribution ladder, abstract/intro/contribution/related-work/method rewrite outputs.
- A single story route with no alternatives.
- Fewer than six story-route slots without an explicit unsupported-route explanation.
- Story routes without ranking criteria, rewrite targets, boundaries, and route-combination guidance.
- Reviewer attacks without why-asked, trigger, defense posture, and no-new-experiment repair.
- Rebuttal snippets without risky wording to avoid.
- Anonymous case appendices that only list case labels without explaining how to borrow the pattern.
- English snippets that overclaim beyond the evidence boundary.
- Treating anonymous casebook patterns as facts about the target paper.
