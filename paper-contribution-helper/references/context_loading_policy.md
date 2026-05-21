# Context Loading Policy

The skill is designed for progressive disclosure. The top-level `SKILL.md` should stay small and act only as a router.

## Budget

- Read `SKILL.md` and `references/module_index.md` first.
- Load at most one primary workflow file before acting.
- Add one contract file when quality or validation requirements matter.
- Search with `rg` before opening broad folders.
- Do not open every file under `references/base_delta/`, `references/report_playbook/`, `assets/`, or `scripts/` unless the user explicitly asks for an audit.

## Primary Workflow Choice

- PDF provided without a stated purpose: ask whether it is for direct analysis or for generating a specialized reusable skill; load no analysis module before the answer.
- Direct analysis of one target PDF: `references/base_delta/workflow_target_paper_reframing.md`
- Generate a specialized reusable skill from a target PDF or explicit fields: `references/build_workflow.md`; add `references/target_domain_inference.md` only when the target PDF is a domain seed.
- User has downloaded PDFs, local corpus files, reviews/replies, or an existing run directory: `references/project_corpus_direct_workflow.md`
- Build or package: `references/build_workflow.md`
- API key, local command backend, and ACP/acpx unavailable but project files exist: `references/project_corpus_direct_workflow.md`, then `references/assistant_local_deep_read_workflow.md`; continue with current-assistant local-file processing.
- API key and local command backend unavailable, but ACP/acpx exists and local assistant processing is not the chosen path: `references/acp_command_file_workflow.md`
- Unknown field/domain: `references/target_domain_inference.md`
- Source selection: `references/source_modes.md`
- Initialization: `references/base_delta/workflow_startup_initialization.md`
- Target-paper report: `references/base_delta/workflow_target_paper_reframing.md`
- Reviewer defense: `references/base_delta/workflow_rebuttal_defense.md`
- Evolution: `references/base_delta/workflow_skill_evolution.md`
- Package design/audit: `references/architecture.md` and `references/path_policy.md`

## Stop Conditions

Stop loading more context when you have:

1. The task route.
2. The input/output contract.
3. The script or command to run.
4. The evidence boundary for claims.

If a later command fails, inspect only the failing script or named reference.

## Context-Limit Rule

Never solve corpus builds by loading all PDFs or extracted paper texts into chat context. Use project files, chunked reading, saved per-paper artifacts, JSONL manifests, and `--reuse-llm` for resume. When the current assistant is the deep-reading route, load only one paper or bounded chunks/artifacts at a time and write the result back to disk before moving on.

For a target PDF used only as a domain seed, load or generate only the domain inference artifact unless the user explicitly switches to direct target-paper analysis.

## Project-Internal Corpus Rule

When a corpus exists under the workspace as `project-run` or standardized `local-pdf`, it is already project-internal. Do not downgrade it back to "external input" because automated LLM synthesis is unavailable. Load only the specific workflow/manifest/report files needed, and continue producing project-run artifacts and local-file deep-read records before reporting any final-packaging blocker.

Backend absence is never itself a local-analysis blocker. If scripts mark deep reading as `not_run`, continue with `references/assistant_local_deep_read_workflow.md` from the saved extracted text and per-paper artifacts. Only report a blocker after identifying a concrete file/context problem and after saving partial artifacts that show where to resume.
