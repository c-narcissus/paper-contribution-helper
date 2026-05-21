# Workflow: Local PDF Intake

Use for local PDFs, with or without review/rebuttal files. Local PDFs must not bypass per-paper analysis.

## Inputs

- one PDF via `--pdf`, or a folder via `--pdf-dir`;
- optional review folder;
- optional reply/rebuttal folder;
- optional metadata folder;
- project run directory.

## Standardize

Run:

```bash
python scripts/standardize_local_pdf_intake.py \
  --pdf <paper.pdf> \
  --run-dir <project_run_dir> \
  --source-kind local-pdf \
  --domain-scope computer-science
```

For a folder:

```bash
python scripts/standardize_local_pdf_intake.py \
  --pdf-dir <pdf_folder> \
  --reviews-dir <optional_review_folder> \
  --replies-dir <optional_reply_folder> \
  --metadata-dir <optional_metadata_folder> \
  --run-dir <project_run_dir>
```

The script creates `materials/_by_paper/<paper_key>/` folders with `paper.pdf`, `submission.json`, and `source_status.json`. If reviews/replies are absent, it records `reviews_missing=true` and `replies_missing=true`.

## Analyze And Initialize

Run:

```bash
python scripts/validate_project_corpus.py --run-dir <project_run_dir>
python scripts/initialize_from_project_corpus.py \
  --run-dir <project_run_dir> \
  --source-kind local-pdf \
  --domain-scope computer-science
```

If no real review files are supplied, reviewer attacks in the final skill output must be labeled `simulated-review`.

## Pairing Convention

For a PDF named `paper_a.pdf`, optional files may be paired as:

- `paper_a.json`
- `paper_a.md`
- `paper_a.reviews.json`
- `paper_a_official_reviews.md`
- `paper_a.replies.json`
- `paper_a_author_replies.md`
- `paper_a.rebuttal.md`

If pairing fails, keep the PDF and mark missing review/reply coverage explicitly.
