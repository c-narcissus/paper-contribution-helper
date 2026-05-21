#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from common import default_state_dir, read_json, write_json
from scan_corpus_catalog import build_catalog, write_md


SKILL_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Configure mandatory initialization inputs for delta-contribution-reframer.")
    parser.add_argument("--corpus-source", type=Path, required=True)
    parser.add_argument("--focus-domains", nargs="+", required=True)
    parser.add_argument("--years", nargs="+", required=True)
    parser.add_argument("--source-kind", default="iclr-openreview")
    parser.add_argument("--domain-scope", default="computer-science")
    parser.add_argument("--state-dir", type=Path, default=default_state_dir())
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = args.corpus_source.expanduser()
    if not source.exists():
        raise SystemExit(f"Corpus source does not exist: {source}")

    state_dir = args.state_dir.resolve()
    init_state_path = state_dir / "initialization_state.json"
    selection_json = state_dir / "initialization_selection.json"
    selection_md = state_dir / "initialization_selection.md"
    catalog_json = state_dir / "corpus_catalog.json"
    catalog_md = state_dir / "corpus_catalog.md"

    catalog = read_json(catalog_json)
    if not catalog.get("available"):
        catalog = build_catalog(source)
        write_json(catalog_json, catalog)
        write_md(catalog, catalog_md)

    now = dt.datetime.now().isoformat(timespec="seconds")
    selection = {
        "schema_version": "1.0",
        "configured_at": now,
        "corpus_source": "user-provided corpus source",
        "source_kind": args.source_kind,
        "domain_scope": args.domain_scope,
        "focus_domains": args.focus_domains,
        "years": args.years,
        "catalog_submission_count": catalog.get("submission_count", 0),
        "next_step": "Run extraction and synthesis for the configured focus domains and years. This configuration alone does not complete initialization.",
    }
    init_state = {
        "schema_version": "1.0",
        "initialized": False,
        "status": "configured",
        "reason": "Mandatory inputs are configured, but no extracted paper knowledge has been saved yet.",
        "focus_domains": args.focus_domains,
        "years": args.years,
        "source_kind": args.source_kind,
        "domain_scope": args.domain_scope,
        "corpus_source": "user-provided corpus source",
        "requires_user_input_when_empty": ["focus_domains", "years", "corpus_source"],
        "updated_at": now,
    }
    write_json(selection_json, selection)
    write_json(init_state_path, init_state)
    selection_md.parent.mkdir(parents=True, exist_ok=True)
    selection_md.write_text(
        "\n".join(
            [
                "# Initialization Selection",
                "",
                f"- Configured at: {now}",
                f"- Corpus source: user-provided corpus source",
                f"- Source kind: {args.source_kind}",
                f"- Domain scope: {args.domain_scope}",
                f"- Focus domains: {', '.join(args.focus_domains)}",
                f"- Years: {', '.join(args.years)}",
                f"- Catalog submission count: {catalog.get('submission_count', 0)}",
                "",
                "## Next Step",
                "",
                str(selection["next_step"]),
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"selection_json": str(selection_json), "selection_md": str(selection_md), **selection}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
