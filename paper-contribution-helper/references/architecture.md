# Architecture

## Design Goals

- Keep `SKILL.md` as a small router.
- Split workflows into high-cohesion reference modules.
- Couple modules through command-line arguments and stable file contracts.
- Keep the package portable with no hardcoded machine paths.
- Package anonymous reusable knowledge, not raw source material.

## Boundaries

| Boundary | Owns | Must Not Own |
|---|---|---|
| Source adapters | Discovering or standardizing papers into a corpus run | LLM synthesis, final target-paper claims |
| Corpus validator | Checking corpus layout and required files | Downloading papers, editing reports |
| Deep-read engine | PDF extraction, per-paper LLM chunks, per-paper manifests | Packaged anonymous resources |
| Synthesis engine | Anonymous pattern extraction and resource writing | Raw PDFs, raw review dumps, target-paper evidence |
| Packager | Rendering `assets/domain-skill-template/` into a portable skill | Project-run caches or user local paths |
| Target-paper workflow | User-facing contribution diagnosis and reviewer defense | Updating frozen base knowledge by default |
| Evolution overlay | Project-local casebook updates | Mutating packaged anonymous base resources unless explicitly requested |

## Data Flow

```text
user input
  -> optional target-domain inference
  -> existing project run or local PDF folder as primary source when available
  -> source adapter only when discovery/download is requested
  -> corpus validation
  -> full-paper LLM deep read per selected reference paper
  -> anonymous synthesis
  -> package rendering
  -> portable generated skill
```

## Coupling Rules

- Scripts expose CLI arguments; do not rely on hidden global workspace paths.
- Inter-module data travels as JSON, JSONL, Markdown, or the project corpus directory contract.
- Optional dependencies are imported inside the functions that need them.
- Long prompts and full-paper records stay in project-run analysis folders, not in `SKILL.md`.
- Full PDFs and complete extracted texts are never loaded into assistant chat context for corpus builds; scripts read project files, chunk papers, and save intermediate artifacts.
- Generated skills carry enough scripts and references to work without this package.

## Packaging Rules

- Exclude `__pycache__`, `.pyc`, `.pyo`, temporary build folders, source caches, old PDFs, and raw forum dumps.
- Store packaged resource paths relative to the generated skill root.
- Run `scripts/validate_modularity.py` before distributing this package.
