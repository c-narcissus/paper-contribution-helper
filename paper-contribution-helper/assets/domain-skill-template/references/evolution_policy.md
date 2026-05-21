# Evolution Policy

The bundled base casebook is frozen. Updating from a new PDF creates a project-local overlay by default.

```bash
python scripts/analyze_new_pdf.py --pdf <paper.pdf>
python scripts/evolve_casebook.py --analysis-record <overlay>/reports/<paper>/analysis_record.json
```

Evolution cards are anonymous and additive. They do not revalidate old corpus PDFs and must not imply that old evidence was re-inspected.
