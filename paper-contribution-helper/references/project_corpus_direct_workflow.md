# Project Corpus Direct Workflow

Use this as the primary corpus path for generating a specialized reusable skill when the user already has downloaded PDFs, metadata, reviews, replies, or an existing project corpus run.

## Principle

Treat the downloaded corpus as project files. Do not paste full PDFs or extracted full text into the chat context. The pipeline should read files from disk, chunk each paper, save intermediate artifacts, and synthesize from machine-readable manifests.

This workflow is not direct analysis of a single target paper. It consumes reference materials and produces anonymous reusable knowledge packaged into a specialized skill.

## Hard Rule: Project-Internal Files

In mode B, once reference PDFs, reviews, replies, metadata, or an existing corpus run are downloaded, provided, or standardized, they are project-internal files for the current workspace.

Do not treat them as external context, do not ask the user to paste them into chat, and do not stop merely because an external backend is unavailable. Continue with project-file analysis from disk until the run has validation, extraction, per-paper analysis folders, manifests, and explicit deep-reading status artifacts.

`OPENAI_API_KEY`, acpx, or local command-backend absence is not a stop condition when the current assistant can inspect local files. In that case, use current-assistant local-file processing as the primary continuation path: read extracted text, reviews, replies, and existing per-paper artifacts from disk; chunk when needed; write the deep-reading records and updated manifest back to the project run.

Missing automated backends may block only fully automated batch execution. They must not block current-assistant local processing of already-downloaded project files. A backend-missing message is valid only when it is explicitly scoped to automation, for example "automated batch execution is unavailable"; it is invalid as a final answer for why the corpus cannot be analyzed.

## Script Gate Is Not Workflow Gate

Some scripts expose backend-oriented flags such as `--llm-provider`, `--llm-deep-read-mode`, and `--llm-results-jsonl`. These flags are automation controls, not workflow permissions.

If `analyze_extracted_papers.py --llm-provider off` writes rule pre-pass artifacts and `llm_deep_reading.status="not_run"`, the next required step is current-assistant local-file deep reading whenever the assistant can read the extracted project files. Do not stop and tell the user to set `OPENAI_API_KEY` or install `acpx` as though that were the only path.

When continuing locally, load `references/assistant_local_deep_read_workflow.md`. Process one paper or bounded chunks at a time, save `llm_deep_read_record.json`, `llm_deep_read_report.md`, `llm_deep_read_status.json`, and update `analysis/per_paper_analysis_manifest.jsonl` so downstream synthesis can use the same completion contract.

They must not block these project-internal stages:

- validating the `project-run` layout;
- extracting PDF text and page indexes;
- reading review/reply files from disk;
- writing rule pre-pass reports;
- writing `analysis/per_paper/<paper_key>/` artifacts;
- writing `analysis/per_paper_analysis_manifest.jsonl`;
- preparing assistant-readable packets with `prepare_assistant_deep_read_packets.py`;
- validating and importing assistant-written records with `validate_assistant_deep_read_records.py` and `import_assistant_deep_read_records.py`;
- producing local-file full-paper deep-read records when the assistant can process the extracted files;
- continuing to anonymous synthesis and packaging when the manifest satisfies the generated skill contract.

Do not report `project-run validated` as completion. It means only stage 1 is complete.

## Stage Contract

Use these stage names in status reports:

1. `corpus_acquired`: PDFs/reviews/replies are present or standardized into a run.
2. `project_internal_analysis_started`: validation, extraction, rule pre-pass, per-paper folders, and manifest generation are running or complete.
3. `llm_deep_read_complete`: every selected reference paper has a full-paper deep-read record, usually stored under the legacy-compatible `llm_deep_reading.status="complete"` field even when produced by current-assistant local-file processing rather than an external API.
4. `reusable_skill_packaged`: anonymous synthesis and final skill packaging are complete.

Only stage 4 is the final product. Stage 1 is not enough. Stage 2 is still valuable and should be produced even when automated stage 3 is blocked. If local assistant processing is available, continue into stage 3 instead of stopping at backend absence. If stage 3 cannot be completed in the current turn, save partial deep-read artifacts and report the next paper/chunk to process, not an API/acpx blocker.

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
python scripts/build_domain_skill.py \
  --skill-name <new-helper-name> \
  --focus-domains <domain> ... \
  --years <year> ... \
  --source-mode project-run \
  --project-run-dir <run-dir> \
  --llm-provider <openai-responses|openai-chat|command|jsonl> \
  --out-dir <skill-output-parent>
```

Use `--reuse-llm` when rerunning after partial completion.

If no automated LLM backend is available, run project-internal analysis first:

```bash
python scripts/engine/validate_project_corpus.py --run-dir <run-dir>
python scripts/engine/analyze_extracted_papers.py \
  --out-dir <run-dir> \
  --state-dir <state-dir> \
  --llm-deep-read-mode optional \
  --llm-provider off
```

This creates extraction, rule pre-pass, per-paper reports, manifest rows, and explicit pending deep-read status. If the current assistant can read the project files, continue by producing complete local-file deep-read records and updating the manifest, instead of stopping for API/acpx.

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
python scripts/build_domain_skill.py \
  --skill-name <new-helper-name> \
  --focus-domains <domain> ... \
  --years <year> ... \
  --source-mode local-pdf \
  --pdf-dir <pdf-folder> \
  --reviews-dir <optional-review-folder> \
  --replies-dir <optional-reply-folder> \
  --metadata-dir <optional-metadata-folder> \
  --llm-provider <openai-responses|openai-chat|command|jsonl> \
  --out-dir <skill-output-parent>
```

`local-pdf` first standardizes PDFs into a project run, then uses the same validation, deep-reading, synthesis, and packaging stages as `project-run`.

## Context-Limit Handling

Context limits are expected. The solution is file-based processing, not larger chat context.

- Extract PDF text in scripts.
- Chunk each paper with `--llm-chunk-chars`.
- Deep-read chunks one at a time.
- Save per-paper outputs under `analysis/per_paper/`.
- Save machine records in `analysis/per_paper_analysis_manifest.jsonl`.
- Resume with `--reuse-llm` instead of recomputing complete papers.
- Synthesize only after all selected reference papers report `llm_deep_reading.status="complete"`.

Never load 60 full papers into the assistant context. Load only indexes, manifests, summaries, or the specific failed paper artifacts needed for debugging.

## LLM Backend Priority

Preferred order after corpus files are local:

1. Current-assistant local-file processing when the user expects the assistant to process downloaded/local materials directly.
2. Precomputed backend: `jsonl` when complete deep-read records already exist.
3. Direct API backend: `openai-responses` or `openai-chat` when an API key is configured and the user wants automated batch processing.
4. Local command backend: `command` when the user has a local LLM wrapper that accepts JSON on stdin.
5. ACP command-file fallback: use `references/acp_command_file_workflow.md` only when local assistant processing is not the chosen path and ACP/acpx is available.

Do not use rule-only analysis for final reusable knowledge.

Rule-only or deep-read-pending project-internal analysis is allowed as an intermediate artifact. Label it clearly and do not package it as final reusable knowledge unless local-file deep-read records or another complete backend satisfy the contract.

Do not phrase rule-only status as "cannot analyze." Phrase it as "stage 2 complete; stage 3 local deep reading remains and should continue from disk."

## Completion Gate

The final reusable helper skill may be packaged only after every selected reference PDF has:

- `workflow_alignment="delta-contribution-reframer"`
- `deep_read_workflow_alignment="llm-full-paper-deep-read"`
- `llm_deep_reading.status="complete"`
- source ledger, evidence boundary, claim-support matrix, story option board, and workflow coverage in the per-paper manifest.

If this gate is not met, stop and report the missing/partial papers instead of packaging a final reusable skill.
