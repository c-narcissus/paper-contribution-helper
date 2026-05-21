# Release Notes

## v1.0.2

- Added a modular current-assistant local deep-read route for project-run corpora when `OPENAI_API_KEY`, local command backends, or ACP/acpx are unavailable.
- Added assistant packet preparation, assistant-written JSONL validation, and import scripts.
- Added JSON config-file support for build/synthesis stages so long domain/year inputs can move out of CLI arguments.
- Shortened generated domain-profile filenames with a stable hash to avoid Windows long-path failures while preserving full domain metadata in manifests and report content.

## v1.0.0

- Initial `paper-contribution-helper` package.
- Modularized the skill around a small router, on-demand workflow references, explicit module boundaries, context loading policy, and path hygiene validation.
- Added a mandatory first-response opening rule: on first invocation, the skill outputs the fixed opening message only and does not answer substantive questions until the user replies again.
- Added an ACP command-file bridge for environments without `OPENAI_API_KEY`; long full-paper prompts are passed through request/prompt/response files instead of command-line arguments.
- Added target-paper domain inference: users can provide `--target-paper` instead of manually supplying `--focus-domains`.
- The factory deep-reads the whole target PDF, infers 1-3 searchable domains or subfields, records the inference artifact, and uses those labels for corpus screening.
- Documented the more user-friendly startup path and the evidence boundary for inferred routing metadata.
- Made downloaded project corpus files the primary initialization path through `references/project_corpus_direct_workflow.md`, covering both `project-run` and `local-pdf`.
- Clarified that ACP/acpx is only an optional `command-file` fallback when no API key, local command backend, or precomputed JSONL backend is available.
- Added explicit context-limit policy: never paste full PDFs or a complete corpus into chat context; use project files, chunking, intermediate artifacts, manifests, and `--reuse-llm`.
- Split the PDF entrypoint into two explicit modes: direct target-paper analysis, or target-PDF/domain-field input for generating a specialized reusable skill.
- Added the rule that an unspecified PDF upload must trigger a two-choice clarification before any analysis or corpus build starts.
- Reworded the mandatory startup message around clear A/B entrypoints so users can distinguish direct paper analysis from specialized skill generation.
- Locked the mandatory startup message to the exact user-approved text as a highest-priority first-response rule.
- Added a project-internal corpus stage contract: downloaded/provided `project-run` or `local-pdf` materials must continue through validation, extraction, per-paper artifacts, manifests, and explicit LLM status even when final synthesis/packaging is blocked.
- Promoted local project-file processing to the highest operational priority after the first-response rule: downloaded/uploaded/standardized PDFs, reviews, replies, metadata, and corpus runs must be processed from disk first; API/acpx/local command backends are optional automation routes, not permission gates.
