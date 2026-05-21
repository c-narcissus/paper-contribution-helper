# Evidence And Evolution Policy

## Evidence

- Do not fabricate experiments, numbers, reviewer comments, author replies, baselines, proofs, citations, or decisions.
- Use packaged base knowledge as anonymous analogy, not evidence for a new target paper.
- Label simulated concerns as `simulated-review`.
- Mark absent sources as `missing / not reported`.
- Mark known-but-unread sources as `not inspected`.
- Do not describe a corpus paper as read unless its PDF text went through the required full-paper LLM deep-reading pass.
- Do not bundle raw PDFs, raw OpenReview dumps, chunk prompts, or per-paper LLM reports into a generated skill; package only anonymous reusable synthesis.

## Evolution

New PDFs can update the generated skill through project-local overlays because old corpus knowledge has already been frozen into anonymous resources.

Default evolution behavior:

1. Analyze the new PDF and any supplied reviews/replies.
2. Run the same full-paper LLM deep-reading workflow when the new PDF is being added as corpus knowledge rather than only target-paper advice.
3. Create an anonymous local evolution card.
4. Preserve bundled base resources unchanged.
5. Package a new skill version only when the user explicitly asks.
