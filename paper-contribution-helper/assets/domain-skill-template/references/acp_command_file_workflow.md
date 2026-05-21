# ACP Command-File Workflow

Use this only as a fallback when a real corpus build is blocked because no API key such as `OPENAI_API_KEY`, local command backend, or complete precomputed JSONL backend is available, but a local ACP route such as `acpx` can call a Codex-compatible agent.

ACP is not the corpus source path. Downloaded PDFs, reviews, replies, metadata, and existing runs should still be handled as project files through `references/project_corpus_direct_workflow.md`; this bridge only supplies LLM responses for `--llm-provider command-file`.

## Why This Exists

Full-paper deep reading can create very long prompts. Passing those prompts as command-line arguments is fragile and may hit shell limits. The `command-file` provider writes each request to JSON and expects one JSON response file, so the prompt travels through files instead of argv.

## Contract

`analyze_extracted_papers.py` writes a request JSON containing:

- `paper_key`
- `stage`
- `prompt`
- `response_json`

The bridge reads `LLM_REQUEST_JSON`, writes the prompt to a sibling `.prompt.txt` file, calls ACP with `--file`, parses ACP stdout as one JSON object, and writes `LLM_RESPONSE_JSON`.

## Bridge Script

Use:

```bash
python scripts/acp_command_file_bridge.py
```

The script has no machine-specific paths. Configure it with environment variables when needed:

| Variable | Meaning |
|---|---|
| `PAPER_HELPER_ACPX_BIN` | Executable name or path for `acpx`; default `acpx`. |
| `PAPER_HELPER_ACPX_NODE` + `PAPER_HELPER_ACPX_JS` | Optional Node executable and JS entrypoint when `acpx` is not directly on `PATH`. |
| `PAPER_HELPER_NODE_DIR` | Optional folder prepended to `PATH`, useful when `npx` is next to a local Node executable. |
| `PAPER_HELPER_EXTRA_PATH` | Optional extra `PATH` prefix for ACP dependencies. |
| `PAPER_HELPER_ACPX_AGENT` | ACP agent name; default `codex`. |
| `PAPER_HELPER_ACPX_SUBCOMMAND` | ACP subcommand; default `exec`. |
| `PAPER_HELPER_ACPX_FORMAT` | ACP output format; default `quiet`. |
| `PAPER_HELPER_ACP_COMMAND` | Full command template override. Supports `{request_json}`, `{response_json}`, `{prompt_file}`, `{paper_key}`, and `{stage}`. |

## Build Example

Use the direct API, local `command`, or precomputed `jsonl` backend first. Run from the skill root, or pass paths adjusted for the current workspace:

```bash
python scripts/build_domain_skill.py \
  --skill-name <new-helper-name> \
  --target-paper <target-paper.pdf> \
  --years <year> ... \
  --source-mode <project-run|local-pdf|openreview-iclr> \
  --llm-provider command-file \
  --llm-command "python scripts/acp_command_file_bridge.py" \
  --llm-timeout 900 \
  --out-dir <skill-output-parent>
```

For an existing project corpus run:

```bash
python scripts/build_domain_skill.py \
  --skill-name <new-helper-name> \
  --focus-domains <domain> ... \
  --years <year> ... \
  --source-mode project-run \
  --project-run-dir <run-dir> \
  --llm-provider command-file \
  --llm-command "python scripts/acp_command_file_bridge.py" \
  --llm-timeout 900 \
  --out-dir <skill-output-parent>
```

## Required Behavior

- Do not bypass `llm-full-paper-deep-read` for real reusable knowledge.
- Do not synthesize or package final reusable knowledge until every selected reference PDF has `llm_deep_reading.status="complete"`.
- If ACP is unavailable, stop with setup instructions instead of falling back to rule-only analysis.
- Keep all request, prompt, response, and ACP log files inside the run's `analysis/llm_file_exchange/` tree unless the user explicitly provides another request directory.
