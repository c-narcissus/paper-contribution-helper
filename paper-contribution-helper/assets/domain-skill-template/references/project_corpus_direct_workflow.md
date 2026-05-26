# Project Corpus Direct Workflow

Use this as the primary path when the user already has downloaded PDFs, metadata, reviews, replies, or an existing project corpus run.

## Principle

Treat the downloaded corpus as project files. Do not paste full PDFs or extracted full text into the chat context. The pipeline should read files from disk, chunk each paper, save intermediate artifacts, and synthesize from machine-readable manifests.

## Hard Rule: Project-Internal Files

In initialization mode, once reference PDFs, reviews, replies, metadata, or an existing corpus run are downloaded, provided, or standardized, they are project-internal files for the current workspace.

Do not treat them as external context, do not ask the user to paste them into chat, and do not stop merely because final packaging is blocked. Continue with project-file analysis until the run has validation, extraction, per-paper analysis folders, manifests, and explicit LLM status artifacts.

Missing API keys or LLM backends may block only automated batch execution. They must not block current-assistant local-file corpus validation, PDF extraction, review/reply file reading, rule pre-pass reports, per-paper folders, manifest rows, full-paper deep-read records, or explicit `not_run`/`failed` LLM status.

## Script Gate Is Not Workflow Gate

Backend-oriented script flags are automation controls, not workflow permissions. If a script writes `llm_deep_reading.status="not_run"` because no automated provider is configured, continue with `references/assistant_local_deep_read_workflow.md` whenever the assistant can read the extracted files. Do not stop and tell the user to set an API key or install ACP/acpx as though that were the only path.

When continuing locally, process one paper or bounded chunks at a time through assistant-readable packets, save the deep-read report/status/record under `analysis/per_paper/<paper_key>/`, and update `analysis/per_paper_analysis_manifest.jsonl`.

Do not report `project-run validated` as completion. It means only `corpus_acquired` is complete.

## Stage Contract

Use these stage names in status reports:

1. `corpus_acquired`: PDFs/reviews/replies are present or standardized into a run.
2. `project_internal_analysis_started`: validation, extraction, rule pre-pass, per-paper folders, and manifest generation are running or complete.
3. `llm_deep_read_complete`: every selected reference paper has `llm_deep_reading.status="complete"`.
4. `reusable_skill_packaged`: anonymous synthesis and final skill packaging are complete.

Only stage 4 is the final product. Stage 1 is not enough. Stage 2 is still valuable and should be produced even when automated stage 3 is blocked. If current-assistant local-file processing is available, continue into stage 3 instead of stopping at backend absence.

## Supported Inputs

### Existing Project Run

Use this when the corpus is already organized as:

```text
<run-dir>/
  materials/_by_paper/<paper_key>/paper.pdf
  materials/_by_paper/<paper_key>/submission.json
  materials/_by_paper/<paper_key>/source_status.json
```

Optional but useful files may include:

```text
official_reviews.json
official_reviews.md
author_replies.json
author_replies.md
meta_review.json
decision.json
```

Command shape:

```bash
python scripts/engine/validate_project_corpus.py --run-dir <run-dir>
python scripts/engine/analyze_extracted_papers.py \
  --out-dir <run-dir> \
  --state-dir <state-dir> \
  --llm-deep-read-mode required \
  --llm-provider <openai-responses|openai-chat|command|jsonl>
python scripts/engine/synthesize_initialized_resources.py \
  --run-dir <run-dir> \
  --focus-domains <domain> ... \
  --years <year> ... \
  --source-kind <source-kind> \
  --state-dir <state-dir> \
  --references-dir <references-dir>
```

Use `--reuse-llm` when rerunning after partial completion.

If no LLM backend is available, run project-internal analysis without pretending the final reusable skill is ready:

```bash
python scripts/engine/validate_project_corpus.py --run-dir <run-dir>
python scripts/engine/analyze_extracted_papers.py \
  --out-dir <run-dir> \
  --state-dir <state-dir> \
  --llm-deep-read-mode optional \
  --llm-provider off
```

This creates extraction, rule pre-pass, per-paper reports, manifest rows, and explicit `not_run` LLM status. If the current assistant can read the project files, continue by producing local-file full-paper deep-read records and updating the manifest. Stop before `synthesize_initialized_resources.py` only until local-file deep reads, a live LLM backend, or complete JSONL deep-read records satisfy the manifest contract.

Then prepare packets for the current assistant:

```bash
python scripts/engine/prepare_assistant_deep_read_packets.py \
  --run-dir <run-dir> \
  --chunk-chars 45000 \
  --overlap-chars 1200
```

After the assistant writes `<run-dir>/analysis/assistant_deep_read_records.jsonl`, import it:

```bash
python scripts/engine/import_assistant_deep_read_records.py \
  --run-dir <run-dir> \
  --records-jsonl <run-dir>/analysis/assistant_deep_read_records.jsonl \
  --require-all
```

### Local PDF Folder

Use this when the user has a directory of PDFs that has not yet been normalized into a corpus run.

Command shape:

```bash
python scripts/engine/standardize_local_pdf_intake.py \
  --run-dir <run-dir> \
  --source-kind local-pdf \
  --domain-scope computer-science \
  --pdf-dir <pdf-folder> \
  --reviews-dir <optional-review-folder> \
  --replies-dir <optional-reply-folder> \
  --metadata-dir <optional-metadata-folder>
```

After standardization, follow the same validation, deep-reading, synthesis, and packaging stages as `project-run`.

## Context-Limit Handling

Context limits are expected. The solution is file-based processing, not larger chat context.

- Extract PDF text in scripts.
- Chunk each paper with `--llm-chunk-chars`.
- Deep-read chunks one at a time.
- Save per-paper outputs under `analysis/per_paper/`.
- Save machine records in `analysis/per_paper_analysis_manifest.jsonl`.
- Resume with `--reuse-llm` instead of recomputing complete papers.
- Synthesize only after all selected reference papers report `llm_deep_reading.status="complete"`.

Never load a full corpus into the assistant context. Load only indexes, manifests, summaries, or the specific failed paper artifacts needed for debugging.

## LLM Backend Priority

Preferred order after corpus files are local:

1. Current-assistant local-file processing when the user expects the assistant to process downloaded/local materials directly.
2. Precomputed backend: `jsonl` when complete deep-read records already exist.
3. Direct API backend: `openai-responses` or `openai-chat` when an API key is configured and the user wants automated batch processing.
4. Local command backend: `command` when the user has a local LLM wrapper that accepts JSON on stdin.
5. ACP command-file fallback: use `references/acp_command_file_workflow.md` only when local assistant processing is not the chosen path and ACP/acpx is available.

Do not use rule-only analysis for final reusable knowledge.

Rule-only or LLM-pending project-internal analysis is allowed as an intermediate artifact. Label it clearly and do not package it as final reusable knowledge. Do not phrase this status as "cannot analyze"; phrase it as "stage 2 complete; stage 3 local deep reading remains and should continue from disk."

## Completion Gate

Reusable helper knowledge may be written only after every selected reference PDF has:

- `workflow_alignment="delta-contribution-reframer"`
- `deep_read_workflow_alignment="llm-full-paper-deep-read"`
- `llm_deep_reading.status="complete"`
- source ledger, evidence boundary, claim-support matrix, story option board, and workflow coverage in the per-paper manifest.

If this gate is not met, stop and report the missing/partial papers instead of treating the corpus as initialized.
