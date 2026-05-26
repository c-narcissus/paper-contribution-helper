# Current-Assistant Local Deep-Read Workflow

Use this module when project-run files already exist and the current Codex desktop assistant should read local PDF artifacts directly instead of relying on `OPENAI_API_KEY`, `acpx`, or another automated callback backend.

This workflow is a file protocol between the assistant and the project run. Scripts prepare packets and validate/import records; the assistant performs the semantic reading and writes the JSON records.

## When To Use

- The corpus has already been downloaded or standardized as a `project-run`.
- `analysis/per_paper/<paper_key>/pdf_text.txt` exists after `analyze_extracted_papers.py --llm-provider off`.
- Automated LLM backends are missing, blocked, or intentionally not used.
- The user explicitly asks the current assistant to orchestrate local file reading and writing.

Do not use this workflow to skip full-paper reading. It is an alternative reading route, not a lighter quality gate.

## Module Boundary

The module has three mechanical scripts:

1. `scripts/engine/prepare_assistant_deep_read_packets.py`
   - reads `analysis/per_paper_analysis_manifest.jsonl`;
   - splits each `pdf_text.txt` into ordered chunk files;
   - writes `analysis/assistant_deep_read_packets/<paper_key>/packet.md`;
   - writes a queue file for the current assistant.
2. `scripts/engine/validate_assistant_deep_read_records.py`
   - validates assistant-written JSONL records against the deep-read contract.
3. `scripts/engine/import_assistant_deep_read_records.py`
   - validates the JSONL;
   - imports it through `analyze_extracted_papers.py --llm-provider jsonl`;
   - refreshes `llm_deep_read_record.json`, `llm_deep_read_status.json`, and the manifest.

The assistant-owned step is deliberately not hidden in a Python callback. The assistant reads packet files and chunk files from disk, writes one JSON object per paper, and only then runs the import script.

## Commands

First create extraction and rule pre-pass artifacts:

```bash
python scripts/engine/validate_project_corpus.py --run-dir <run-dir>
python scripts/engine/analyze_extracted_papers.py \
  --out-dir <run-dir> \
  --state-dir <state-dir> \
  --llm-deep-read-mode optional \
  --llm-provider off
```

Prepare assistant-readable packets:

```bash
python scripts/engine/prepare_assistant_deep_read_packets.py \
  --run-dir <run-dir> \
  --chunk-chars 45000 \
  --overlap-chars 1200
```

The current assistant then reads:

```text
<run-dir>/analysis/assistant_deep_read_packets/queue.jsonl
<run-dir>/analysis/assistant_deep_read_packets/<paper_key>/packet.md
<run-dir>/analysis/assistant_deep_read_packets/<paper_key>/chunks/chunk_*.txt
```

For every paper, the assistant writes one record to:

```text
<run-dir>/analysis/assistant_deep_read_records.jsonl
```

Validate and import the assistant-written records:

```bash
python scripts/engine/import_assistant_deep_read_records.py \
  --run-dir <run-dir> \
  --records-jsonl <run-dir>/analysis/assistant_deep_read_records.jsonl \
  --require-all
```

Continue synthesis and packaging only after the refreshed manifest reports every selected paper as:

```text
llm_deep_reading.status="complete"
deep_read_workflow_alignment="llm-full-paper-deep-read"
```

## Assistant Record Contract

Each JSONL line must be one JSON object with:

- `workflow_alignment="llm-full-paper-deep-read"`;
- `reading_status="complete"`;
- `paper_key`;
- `source_grounding_summary`;
- `authoritative_report_markdown`;
- `paper_identity`;
- `scientific_problem_and_positioning`;
- `method_deep_read`;
- `formulas_algorithms_and_assumptions`;
- `figure_table_and_experiment_analysis`;
- `claim_support_matrix`;
- `delta_reframing`;
- `story_option_board`;
- `reviewer_attack_preplay`;
- `review_reply_coverage`;
- `reproducibility_gaps`;
- `limitations_and_scope_boundaries`;
- `no_new_experiment_reuse_priorities`;
- `reusable_anonymous_patterns`;
- `uncertainty_notes`.

The validation script rejects missing keys, wrong workflow alignment, incomplete status, empty reports, empty claim-support matrices, empty story boards, and records not present in the run manifest when `--run-dir` is supplied.

## Evidence Rules

- Packet chunks are project files, not chat paste requirements.
- The assistant may load one paper or one bounded set of chunk files at a time.
- Raw paper text, prompts, per-paper reports, and JSON records stay in the project run.
- Generated reusable skills package only anonymous synthesis.
- If a record is produced from rule pre-pass alone, mark it incomplete; do not import it as a complete full-paper deep read.
