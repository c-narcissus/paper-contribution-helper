# Full-Paper Deep-Reading Workflow

This factory must treat reference-paper analysis as a full-paper semantic reading stage, not as a rule-only text extraction pass. The legacy artifact names still use `llm_deep_read_*`, but the required work may be performed by the current assistant reading local project files directly; external API/acpx backends are optional automation routes.

## Borrowed Methodology

Use these constraints from the local reference skills:

- From paper deep-reading workflows: every paper in a batch must receive one authoritative per-paper report plus a machine-readable intermediate artifact; selective reading is not allowed.
- From teaching/reproducibility overlays: preserve formulas, algorithm steps, experiment logic, figure/table evidence, reproducibility gaps, and source-grounding labels.
- From review-defense workflows: audit novelty, incrementality, baseline fairness, scope/claim mismatch, mechanism evidence, reproducibility, and no-new-experiment repair options.
- From the existing delta-contribution methodology: keep source ledger, evidence boundary, reference regime/failure modes, surface delta, stronger delta, claim-support matrix, Story Option Board, review/reply analysis, and reuse priorities.

## Required Per-Paper Flow

For every selected `materials/_by_paper/<paper_key>/paper.pdf`:

1. Extract text from every PDF page and save `pdf_text.txt` plus `page_index.json`.
2. Split the extracted full text into ordered chunks when it exceeds the configured LLM context budget. Do not drop chunks silently.
3. Run a chunk-reading pass over every chunk. The reader can be the current assistant operating on local project files or an automated backend. Each chunk result must capture:
   - source-grounded claims and evidence anchors;
   - method modules, formulas, algorithm steps, and assumptions;
   - figure/table/experiment observations when visible in text or captions;
   - limitations, scope boundaries, and reproducibility gaps;
   - novelty/incrementality and reviewer-risk signals.
4. Run a synthesis pass over all chunk results plus local review/reply material. The synthesis must produce:
   - an authoritative deep-read Markdown report;
   - a machine-readable `llm_deep_read_record.json`;
   - claim-support and story-option outputs that can update the delta reframing record.
5. Run the existing rule-based delta pre-pass and merge it with the semantic deep-read result. Rule evidence remains useful as an audit layer, but it is not a substitute for full-paper deep reading.

## Required Artifacts

Each per-paper analysis folder must contain:

```text
analysis.md
analysis_record.json
claim_delta_matrix.json
llm_deep_read_report.md
llm_deep_read_record.json
llm_deep_read_status.json
llm_chunk_results.jsonl
llm_deep_read_prompt.md
pdf_text.txt
page_index.json
source_ledger.json
review_reply_ledger.json
```

## Validation Rules

- Builds that initialize a real corpus must fail unless every selected PDF has `llm_deep_reading.status="complete"`.
- The per-paper manifest must include `llm_deep_reading`, `llm_deep_read_record`, and `deep_read_workflow_alignment`.
- `deep_read_workflow_alignment` must be `llm-full-paper-deep-read`.
- A generated package must include `references/llm_deep_read_synthesis.md`, an anonymous synthesis of what the full-paper-read corpus supports.
- Raw PDFs, raw forum dumps, prompts/chunks containing full paper text, and per-paper deep-read reports stay in the project run. The generated skill packages only anonymous reusable synthesis.

## Reading Route Contract

Priority order after corpus files exist locally:

1. Current-assistant local-file processing when the user asks to process downloaded/local materials directly.
2. `jsonl`: import precomputed deep-read results from a JSONL file keyed by `paper_key`.
3. `openai-responses`: call the OpenAI Responses API with `OPENAI_API_KEY` or another configured key environment variable.
4. `openai-chat`: call the OpenAI Chat Completions API for compatible deployments.
5. `command`: call a user-supplied local command that receives one JSON request on stdin and returns one JSON result on stdout.
6. `command-file`: write a JSON request file containing `paper_key`, `stage`, `prompt`, and `response_json`; then either run `--llm-command` or wait for an external ACP/agent watcher to write one JSON object to `response_json`.

When the current assistant is the reading route, load `references/assistant_local_deep_read_workflow.md` and use the same artifact contract: prepare packets, read chunk files from disk, write assistant-owned JSONL records, import them, write `llm_chunk_results.jsonl`, `llm_deep_read_report.md`, `llm_deep_read_record.json`, `llm_deep_read_status.json`, and update the manifest. Set the provider/source label inside the record to show that the record was produced by local project-file assistant processing.

For `command-file`, the command may use `{request_json}`, `{response_json}`, `{paper_key}`, and `{stage}` placeholders, or read `LLM_REQUEST_JSON`, `LLM_RESPONSE_JSON`, `LLM_PAPER_KEY`, and `LLM_STAGE` from the environment. This keeps full paper chunks in files instead of command-line arguments.

If using ACP/acpx as a fallback backend, prefer `scripts/acp_command_file_bridge.py`; see `references/acp_command_file_workflow.md`. The bridge writes the long prompt to a `.prompt.txt` file and calls ACP with file input, avoiding command-line length limits. This does not replace project-file corpus processing; it only supplies automated responses when local assistant processing is not the chosen path.

Use `--llm-deep-read-mode required` by default for real corpus builds. Use `optional` only for debugging pipeline mechanics, and never package optional/rule-only outputs as initialized knowledge.
