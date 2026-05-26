# Build Workflow

## Inputs

Required:

- `--skill-name`
- `--focus-domains` or `--target-paper`
- `--years`
- `--source-mode`
- `--out-dir`

Recommended user-facing fields:

- mode: generate a specialized reusable skill;
- domain seed: target paper PDF for field inference, or explicit fields/subfields;
- years;
- source: `project-run`, `local-pdf`, or `openreview-iclr`;
- quantity/cap when discovery is used;
- output skill name.

Source-specific:

- `project-run`: `--project-run-dir <run_dir>`
- `local-pdf`: `--pdf <paper.pdf>` or `--pdf-dir <folder>`
- `openreview-iclr`: `--cap <n>` and one year for the integrated OpenReview adapter

Preferred source route:

- If the user already has downloaded PDFs, reviews/replies, metadata, or a run directory, use `references/project_corpus_direct_workflow.md` first.
- Prefer `project-run` for an already-normalized corpus.
- Prefer `local-pdf` for a raw folder of downloaded PDFs.
- Use `openreview-iclr` only when the user wants this skill to discover/download the corpus.
- Once a corpus is downloaded or standardized, it is a project-internal file set. Continue local project-file processing from disk. External API/acpx absence is not a stop condition when the current assistant can inspect and synthesize from local files.

Full-paper deep-reading:

- `--llm-deep-read-mode required` is the default for real corpus builds.
- The current assistant's local-file processing route has priority when the user asks to process downloaded/local materials directly. It should read extracted project files from disk, chunk as needed, write per-paper deep-read records, update the manifest, and continue synthesis/package steps if the contract is satisfied.
- Use `references/assistant_local_deep_read_workflow.md` to modularize this route through packet preparation, assistant-written JSONL records, validation, and import.
- `--llm-provider openai-responses` is the default online automation backend, not a required permission gate.
- `--llm-provider openai-chat`, `command`, `command-file`, or `jsonl` may be used when the environment requires a different LLM route.
- `--llm-provider command-file` writes one request JSON file per chunk/synthesis prompt and reads one response JSON file.
- ACP/acpx is a fallback, not the primary corpus-analysis path. When local assistant processing is not being used and no API key/local command backend is available but ACP/acpx is available, load `references/acp_command_file_workflow.md` and use `--llm-provider command-file --llm-command "python scripts/acp_command_file_bridge.py"`.
- `--llm-provider off` is only for debugging and is rejected when deep reading is required.
- `--llm-results-jsonl <file>` imports precomputed deep-read records keyed by `paper_key`.

Target-paper domain inference:

- If `--focus-domains` is omitted, provide `--target-paper <paper.pdf>` as a domain seed.
- The factory extracts and reads the target paper for domain/subfield inference before corpus discovery.
- This is not direct contribution analysis of that PDF; it does not produce story routes, reviewer defense, or manuscript edits.
- The inference step returns 1-3 searchable focus domains or subfields and saves them to `build/<skill-name>/.delta-contribution-reframer/state/target_domain_inference.json`.
- Inference requires a live LLM route: `openai-responses`, `openai-chat`, `command`, or `command-file`. `jsonl` remains for precomputed reference-paper deep reads and is not used for fresh target-domain inference.

## One-Step Build

Existing project corpus run:

```bash
python scripts/build_domain_skill.py \
  --skill-name paper-helper-from-corpus \
  --focus-domains <domain> ... \
  --years <year> ... \
  --source-mode project-run \
  --project-run-dir <run-dir> \
  --llm-provider openai-responses \
  --llm-deep-read-mode required \
  --out-dir dist \
  --overwrite
```

Raw downloaded PDF folder:

```bash
python scripts/build_domain_skill.py \
  --skill-name paper-helper-from-pdfs \
  --focus-domains <domain> ... \
  --years <year> ... \
  --source-mode local-pdf \
  --pdf-dir <pdf-folder> \
  --metadata-dir <optional-metadata-folder> \
  --reviews-dir <optional-review-folder> \
  --replies-dir <optional-reply-folder> \
  --llm-provider openai-responses \
  --llm-deep-read-mode required \
  --out-dir dist \
  --overwrite
```

OpenReview discovery/download:

```bash
python scripts/build_domain_skill.py \
  --skill-name delta-reframer-fl-ssl-iclr2026 \
  --display-name "Delta Reframer FL/SSL ICLR 2026" \
  --focus-domains 联邦学习 半监督学习 \
  --years 2026 \
  --source-mode project-run \
  --project-run-dir runs/iclr-openreview_federated-learning_semisupervised-learning_2026 \
  --llm-provider openai-responses \
  --llm-deep-read-mode required \
  --out-dir dist \
  --overwrite
```

If the user does not know the focus domain labels, use the target-paper-as-domain-seed form:

```bash
python scripts/build_domain_skill.py \
  --skill-name delta-reframer-target-guided-iclr2026 \
  --display-name "Delta Reframer Target-Guided ICLR 2026" \
  --target-paper path/to/target-paper.pdf \
  --years 2026 \
  --source-mode openreview-iclr \
  --llm-provider openai-responses \
  --llm-deep-read-mode required \
  --out-dir dist \
  --overwrite
```

## Pipeline Steps

1. Create a staging home under `build/<skill-name>/.delta-contribution-reframer/`.
2. If no focus domains were supplied, read `--target-paper` for domain inference only, infer 1-3 focus domains/subfields, and store the inference record under the staging home.
3. Obtain a corpus run from the selected source mode, using either supplied or inferred focus domains for screening.
4. Validate the run against the project corpus contract.
5. Extract and analyze every `materials/_by_paper/<paper_key>/` folder.
6. Run the required full-paper deep-reading pass for every selected PDF, chunking only when needed for context limits. This may be current-assistant local-file processing or an automated backend.
7. Merge the deep-read record with the delta-contribution rule pre-pass.
8. Synthesize anonymous resources into the staging home, including `references/llm_deep_read_synthesis.md`.
9. Package a standalone skill from `assets/domain-skill-template/`.
10. Run generated package validation and startup checks.

The final generated skill should be usable even if the staging home and corpus run are removed.

Do not confuse this workflow with direct target-paper analysis. A target PDF in this workflow is used to pick the field and build a specialized reusable skill from reference papers.

## Blocked-Backend Behavior

If a corpus exists but `OPENAI_API_KEY`, local `command`, ACP/acpx, and complete JSONL records are all unavailable, do not stop at `project-run validated` and do not report backend absence as a reason analysis cannot continue.

Continue project-internal analysis with `references/project_corpus_direct_workflow.md`:

- validate the corpus;
- extract each PDF;
- read review/reply files;
- write per-paper rule pre-pass reports;
- write the per-paper manifest;
- record `llm_deep_reading.status="not_run"` or `failed` when automated deep reading did not run.

Then, if the current assistant can read local project files, continue by producing local-file full-paper deep-read records and updating the manifest. This is mandatory for project-internal corpora; it is not optional merely because a script's automated backend path is unavailable. Stop before anonymous synthesis and final skill packaging only if neither local assistant processing nor another complete deep-read source is available, or if a concrete file-level blocker prevents local reading.

Script defaults and CLI errors do not override this workflow. Treat an automated-backend failure as a switch from automated batch mode to current-assistant local-file processing.

## Context-Limit Requirement

Do not paste full PDFs or full extracted paper text into the assistant context. The pipeline must process corpus files from disk, split each paper with `--llm-chunk-chars`, save per-paper records and manifests under the project run, and resume with `--reuse-llm` when needed.

## Alignment Requirement

The per-paper analysis step is not a lightweight index. It must run a full-paper LLM deep-read over every selected PDF and produce `delta-contribution-reframer`-aligned reports for every reference paper, including source ledger, evidence boundary, reference regime/failure modes, surface-vs-stronger delta, claim-support matrix, story options, review/reply analysis, and reuse priorities. The generated skill's target-paper mode must also follow the same base target-paper workflow; `analyze_new_pdf.py` is only a pre-pass.

The build is not acceptable unless the machine-readable per-paper manifest can be parsed as one JSON object per physical line and every record includes:

- `workflow_alignment="delta-contribution-reframer"`;
- `deep_read_workflow_alignment="llm-full-paper-deep-read"`;
- `llm_deep_reading.status="complete"`;
- `llm_deep_read_record`;
- `source_ledger`;
- `evidence_boundary`;
- `target_regime_summary`;
- `broken_assumptions_or_failure_modes`;
- `surface_delta`;
- `stronger_delta`;
- `claim_support_matrix`;
- `story_option_board`;
- `workflow_coverage`.

If any of these are missing, stop before synthesis/package validation. Do not ship a generated skill whose reference-paper analysis is shallower than the target `delta-contribution-reframer` workflow or whose real corpus was only rule-analyzed.
