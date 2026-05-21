# Generated Skill Contract

## Required Layout

```text
<generated-skill>/
  SKILL.md
  agents/openai.yaml
  references/
    knowledge_manifest.json
    anonymous_casebook.jsonl
    per_pdf_report_synthesis.md
    llm_deep_read_synthesis.md
    domain_profile_*.md
    evidence_policy.md
    evolution_policy.md
    usage_workflows.md
    llm_deep_reading_workflow.md
  scripts/
    startup_check.py
    analyze_new_pdf.py
    evolve_casebook.py
    validate_skill_package.py
    engine/                         # full blank delta initializer engine
  references/
    base_delta/                     # full blank delta workflows/contracts
```

## Portability Requirements

- `knowledge_manifest.json` stores package-relative paths.
- `anonymous_casebook.jsonl`, `per_pdf_report_synthesis.md`, and `llm_deep_read_synthesis.md` are non-empty for initialized real-corpus packages.
- No old PDFs, raw review dumps, forum IDs, URLs, authors, or paper titles are bundled.
- No full-paper LLM prompts, chunk outputs, or per-paper LLM reports are bundled.
- Startup must not require project-local initialization.
- Evolution from new papers writes a local overlay by default.
- If packaged base knowledge is absent, the generated skill must still expose the same initialization workflows and scripts as the blank `delta-contribution-reframer`.

## Delta Reframer Parity Requirements

Generated skills must stay behaviorally aligned with `delta-contribution-reframer`.

- Target-paper analysis must follow `references/base_delta/workflow_target_paper_reframing.md`.
- `scripts/analyze_new_pdf.py` is only an extraction and pattern-detection pre-pass; it must mark `prepass_only=true`, save target evidence artifacts, and create a full-report scaffold.
- A final target-paper report must include source ledger, evidence boundary, target regime, broken assumptions, surface-vs-stronger delta, claim-support matrix, ranked story options, review attacks, revision priorities, and manuscript/rebuttal snippets.
- Corpus/reference-paper analysis must use the same full reframing structure for every selected paper, not only pattern matching.
- Corpus/reference-paper analysis must run a full-paper LLM deep-read for every selected PDF before synthesis. Chunking is allowed; selective reading is not.
- `analysis/per_paper/<paper_key>/analysis.md` must include source ledger, evidence boundary, reference regime/failure modes, surface-vs-stronger delta, claim-support matrix, story option board, review attack analysis, reply move analysis, and reuse priorities.
- `analysis/per_paper/<paper_key>/analysis_record.json` and `analysis/per_paper_analysis_manifest.jsonl` must declare `workflow_alignment="delta-contribution-reframer"` and `deep_read_workflow_alignment="llm-full-paper-deep-read"`, have `llm_deep_reading.status="complete"`, and include `llm_deep_read_record`, `source_ledger`, `evidence_boundary`, `target_regime_summary`, `broken_assumptions_or_failure_modes`, `surface_delta`, `stronger_delta`, `claim_support_matrix`, `story_option_board`, and `workflow_coverage`.
- Generated packages must include `references/base_delta/workflow_target_paper_reframing.md` and `references/base_delta/contract_story_options.md`.
- Synthesis and packaging must fail if the per-paper manifest is missing, empty, malformed, not line-safe JSONL, lacks any required parity field, or shows incomplete LLM deep-reading.
