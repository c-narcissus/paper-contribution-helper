# Latent Contribution Mining

Mine contributions that are already supported by the target PDF but not clearly written by the authors. Do not invent new evidence.

## Evidence Labels

- `paper-explicit`: directly stated or shown in the target PDF.
- `latent-but-supported`: not stated as a contribution, but supported by method design, results, ablation, or appendix evidence.
- `story-level reframing`: a safer way to organize existing claims and evidence.
- `future-boundary hook`: an attractive broader implication that must remain motivation, discussion, or future work.

## Mining Questions

1. What old assumption does the paper quietly break?
2. What failure mode does the method implicitly repair?
3. Which modules only make sense together under the target constraint?
4. Which experiments already answer reviewer doubts but are not narrated that way?
5. Which claim sounds too small because it is written at component level instead of problem level?
6. Which broader idea is tempting but not yet fully evidenced?

## Output Requirement

For each mined contribution, provide:

- plain-language explanation;
- evidence label;
- supporting evidence anchor;
- safe paper claim;
- unsafe overclaim to avoid;
- where to use it: abstract, intro, contribution, method, experiment, limitation, discussion, or rebuttal.
