# Module Index

Use this file as the routing table. Open only the module needed for the current task.

| Module | Files | Responsibility | Coupling Contract |
|---|---|---|---|
| Skill router | `SKILL.md`, `agents/openai.yaml` | Triggering, short routing, context budget reminders | References modules by relative path only |
| PDF mode disambiguation | `SKILL.md`, `references/context_loading_policy.md` | Separate direct target-paper analysis from target-PDF-as-domain-seed skill generation | If PDF purpose is unspecified, ask before running tools |
| Build orchestration | `scripts/build_domain_skill.py`, `references/build_workflow.md` | End-to-end helper-skill build pipeline | Calls source, engine, and packaging modules through CLI arguments |
| Direct project corpus | `references/project_corpus_direct_workflow.md`, `scripts/engine/standardize_local_pdf_intake.py`, `scripts/engine/validate_project_corpus.py`, `scripts/engine/analyze_extracted_papers.py` | Highest-priority project-internal path for downloaded PDFs, local PDF folders, reviews/replies, or existing corpus runs | Treats corpus files as local project files; continues with current-assistant local-file processing when external backends are absent |
| Current-assistant local deep reading | `references/assistant_local_deep_read_workflow.md`, `scripts/engine/prepare_assistant_deep_read_packets.py`, `scripts/engine/validate_assistant_deep_read_records.py`, `scripts/engine/import_assistant_deep_read_records.py` | Modular file protocol for the current assistant to read extracted PDFs and write full-paper deep-read records without Python calling an LLM backend | Emits assistant packets, validates assistant-written JSONL, imports through the existing JSONL backend |
| ACP command-file bridge | `scripts/acp_command_file_bridge.py`, `references/acp_command_file_workflow.md` | Optional fallback automation backend when local assistant processing is not the chosen path and ACP/acpx exists | Reads `LLM_REQUEST_JSON`; writes `LLM_RESPONSE_JSON`; all long prompts stay in files |
| Target-domain inference | `references/target_domain_inference.md` | Infer 1-3 search fields from a target PDF used as a domain seed | Produces `target_domain_inference.json`; does not produce contribution diagnosis or evidence for contribution claims |
| Source adapters | `references/source_modes.md`, `scripts/discover_iclr_openreview.py`, `scripts/engine/standardize_local_pdf_intake.py` | Convert OpenReview, local PDFs, or project runs into a corpus-run shape | Emits `materials/_by_paper/<paper_key>/` and index files |
| Corpus contracts | `references/base_delta/contract_project_corpus.md`, `scripts/engine/validate_project_corpus.py` | Validate expected corpus-run layout | Rejects missing `paper.pdf`, metadata, or status artifacts when required |
| Deep reading engine | `scripts/engine/analyze_extracted_papers.py`, `references/llm_deep_reading_workflow.md` | Extract PDFs and create per-paper full-read records through local assistant processing or an automated backend | Emits JSONL manifest and Markdown reports under project run analysis paths |
| Anonymous synthesis | `scripts/engine/synthesize_initialized_resources.py`, `references/evidence_and_evolution_policy.md` | Convert per-paper evidence into anonymous reusable patterns | Writes package-local references without raw PDFs or identifiable dumps |
| Packaging | `scripts/package_domain_skill.py`, `references/generated_skill_contract.md`, `assets/domain-skill-template/` | Render a portable generated skill | Copies only template resources and anonymous synthesis |
| Target-paper reporting | `references/base_delta/workflow_target_paper_reframing.md`, `references/base_delta/contract_target_report_quality.md` | Diagnose and package one user's paper | Uses target-paper evidence; packaged cases are analogies |
| Reviewer defense | `references/base_delta/workflow_rebuttal_defense.md`, `references/report_playbook/` | Simulate reviewer attacks and draft defenses | Grounds real rebuttals in user-provided reviews/replies |
| Evolution overlay | `scripts/engine/evolve_from_paper.py`, `references/base_delta/workflow_skill_evolution.md` | Add new local cases without mutating frozen base knowledge | Writes project-local overlay by default |
| Validation | `scripts/validate_modularity.py`, generated `scripts/validate_skill_package.py` | Check modularity, path hygiene, cache exclusion, and generated package completeness | Read-only validation over package files |

## Loading Rule

Start with one row from this table. Load another module only when the current row explicitly points to it or when a validation error names it.
