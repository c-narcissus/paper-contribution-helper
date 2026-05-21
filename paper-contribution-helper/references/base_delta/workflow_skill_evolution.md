# Workflow: Skill Evolution

Use when adding a new paper example to the current project's future knowledge base.

1. Run `scripts/evolve_from_paper.py --paper-pdf <pdf> [--reviews <file>] [--replies <file>] [--metadata <json>]`.
2. The script must create a standard material folder and then call `analyze_extracted_papers.py`.
3. Confirm the evolution output contains:
   - `analysis/per_paper/<case_id>/analysis.md`;
   - `analysis/per_paper/<case_id>/analysis_record.json`;
   - `analysis/per_paper/<case_id>/claim_delta_matrix.json`;
   - `analysis/per_paper_analysis_manifest.jsonl`;
   - `evolution_decision.json`.
4. Decide `include`, `manual-review`, or `exclude` from the saved analysis, not from filename/title alone.
5. If reviews are missing, mark attacks as `simulated-review`.
6. If included, append only an anonymized card to `.delta-contribution-reframer/references/evolving_casebook.md/jsonl`.
7. Update broader methodology resources only after repeated reusable patterns appear.

Default source kind is `iclr-openreview`; default domain scope is `computer-science`. Override only when the new sample is explicitly from another venue or field.
