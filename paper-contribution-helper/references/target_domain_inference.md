# Target-Paper Domain Inference

Use this workflow when the user wants to generate a specialized reusable skill but does not know which focus domains or subfields to provide.

The target PDF is a domain seed in this workflow. It is not being directly analyzed for contribution packaging, reviewer defense, or manuscript rewriting. If the user wants those outputs, route to target-paper reframing instead.

## User Entry

The user may provide a target paper PDF instead of explicit `--focus-domains`. The final output of the build is a specialized reusable skill, not a report about that PDF.

```bash
python scripts/build_domain_skill.py \
  --skill-name <new-skill-name> \
  --target-paper <target-paper.pdf> \
  --years <year> ... \
  --source-mode <project-run|local-pdf|openreview-iclr> \
  --llm-provider <openai-responses|openai-chat|command|command-file> \
  --out-dir <skill-output-parent>
```

`--focus-domains` remains supported and takes precedence when supplied.

## Inference Contract

1. Extract the whole target PDF text using the same PDF extraction path as reference-paper analysis.
2. Read every target-paper chunk with a domain-identification lens, not a contribution-diagnosis lens.
3. Synthesize exactly 1-3 focus domains or subfields suitable for search/filtering.
4. Prefer specific labels such as `federated semi-supervised learning`, `vision-language models`, `graph neural networks`, or `multimodal retrieval` over broad labels such as `machine learning`.
5. Save the artifact to `build/<skill-name>/.delta-contribution-reframer/state/target_domain_inference.json`.
6. Use the inferred labels exactly as the focus-domain filters for discovery, local/project corpus screening, balanced domain quotas, and synthesis metadata.

## Evidence Discipline

The inferred domains are routing metadata, not evidence about the target paper's contribution. This workflow must not produce a contribution report, story routes, reviewer attacks, rebuttal text, or manuscript edits for the target PDF. Later target-paper reports must still cite only target-paper evidence for target-paper claims and use packaged casebook knowledge only as anonymous analogy.

If the PDF text cannot be extracted, stop and ask the user for a readable PDF or explicit focus domains. Do not guess domains from the filename alone.
