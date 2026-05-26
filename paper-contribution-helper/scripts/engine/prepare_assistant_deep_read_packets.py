#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from common import clean, read_json, write_json


REQUIRED_RECORD_KEYS = [
    "schema_version",
    "workflow_alignment",
    "reading_status",
    "paper_key",
    "source_grounding_summary",
    "authoritative_report_markdown",
    "paper_identity",
    "scientific_problem_and_positioning",
    "method_deep_read",
    "formulas_algorithms_and_assumptions",
    "figure_table_and_experiment_analysis",
    "claim_support_matrix",
    "delta_reframing",
    "story_option_board",
    "reviewer_attack_preplay",
    "review_reply_coverage",
    "reproducibility_gaps",
    "limitations_and_scope_boundaries",
    "no_new_experiment_reuse_priorities",
    "reusable_anonymous_patterns",
    "uncertainty_notes",
]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def chunk_text(text: str, chunk_chars: int, overlap_chars: int) -> list[str]:
    text = clean(text)
    if not text:
        return []
    if len(text) <= chunk_chars:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_chars)
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = max(end - overlap_chars, start + 1)
    return chunks


def summarize_list(value: Any, limit: int = 5) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        text = re.sub(r"\s+", " ", str(item)).strip()
        if text:
            out.append(text[:600])
        if len(out) >= limit:
            break
    return out


def packet_markdown(
    run_dir: Path,
    paper_key: str,
    packet_dir: Path,
    record: dict[str, Any],
    chunks: list[Path],
) -> str:
    source = record.get("source_ledger") if isinstance(record.get("source_ledger"), dict) else {}
    regime = record.get("target_regime_summary") if isinstance(record.get("target_regime_summary"), dict) else {}
    surface = record.get("surface_delta") if isinstance(record.get("surface_delta"), dict) else {}
    stronger = record.get("stronger_delta") if isinstance(record.get("stronger_delta"), dict) else {}
    matrix = record.get("claim_support_matrix") if isinstance(record.get("claim_support_matrix"), list) else []
    story = record.get("story_option_board") if isinstance(record.get("story_option_board"), list) else []
    lines = [
        "# Current-Assistant Local Deep-Read Packet",
        "",
        f"- Paper key: `{paper_key}`",
        f"- Title: {source.get('title') or 'not reported'}",
        f"- Venue/year: {source.get('venue') or 'not reported'} / {source.get('year') or 'not reported'}",
        f"- Material dir: `{source.get('material_dir') or 'not reported'}`",
        f"- PDF text chars: {record.get('pdf_text_chars', 0)}",
        f"- Review status: `{record.get('review_status', 'unknown')}`",
        f"- Reply status: `{record.get('reply_status', 'unknown')}`",
        "",
        "## Reading Contract",
        "",
        "Read the chunk files from disk. Produce exactly one JSON object with these required keys:",
        "",
    ]
    lines.extend(f"- `{key}`" for key in REQUIRED_RECORD_KEYS)
    lines.extend(
        [
            "",
            "Required values:",
            "",
            "- `workflow_alignment` must be `llm-full-paper-deep-read`.",
            "- `reading_status` must be `complete` only after every chunk has been read.",
            "- `authoritative_report_markdown` must be a source-grounded full-paper report.",
            "- `reusable_anonymous_patterns` must not include title, author, URL, forum id, or unique benchmark bundles.",
            "",
            "## Source Files",
            "",
            f"- Pre-pass record: `{rel(run_dir / 'analysis' / 'per_paper' / paper_key / 'analysis_record.json', run_dir)}`",
            f"- Source ledger: `{rel(run_dir / 'analysis' / 'per_paper' / paper_key / 'source_ledger.json', run_dir)}`",
            f"- Extracted PDF text: `{rel(run_dir / 'analysis' / 'per_paper' / paper_key / 'pdf_text.txt', run_dir)}`",
            f"- Output JSON record: `{rel(packet_dir / 'assistant_deep_read_record.json', run_dir)}`",
            "",
            "## Chunk Files",
            "",
        ]
    )
    lines.extend(f"- `{rel(path, run_dir)}`" for path in chunks)
    lines.extend(
        [
            "",
            "## Pre-Pass Anchors",
            "",
            f"- Domain/area: {regime.get('domain_or_area') or 'not reported'}",
            f"- Surface delta: {surface.get('summary') or 'not reported'}",
            f"- Stronger delta: {stronger.get('summary') or 'not reported'}",
            "",
            "### Constraint Signals",
            "",
        ]
    )
    signals = summarize_list(regime.get("constraint_signals"), 6)
    lines.extend(f"- {item}" for item in signals) if signals else lines.append("- not reported")
    lines.extend(["", "### Claim-Support Matrix Preview", ""])
    for row in matrix[:5]:
        if isinstance(row, dict):
            lines.append(f"- Claim: {clean(str(row.get('claim') or ''))[:400]}")
            lines.append(f"  Support: {clean(str(row.get('support') or ''))[:400]}")
    if not matrix:
        lines.append("- not reported")
    lines.extend(["", "### Story Options Preview", ""])
    for row in story[:5]:
        if isinstance(row, dict):
            lines.append(f"- {row.get('rank')}: {row.get('option')} -- {row.get('use_when')}")
    if not story:
        lines.append("- not reported")
    lines.extend(
        [
            "",
            "## Completion Steps",
            "",
            "1. Read all chunk files listed above.",
            "2. Use the pre-pass anchors only as audit scaffolding; do not let them replace the PDF reading.",
            "3. Write `assistant_deep_read_record.json` in this packet folder.",
            "4. Append the record to the JSONL file used by `import_assistant_deep_read_records.py`.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def prepare(args: argparse.Namespace) -> dict[str, Any]:
    run_dir = args.run_dir.resolve()
    manifest_path = run_dir / "analysis" / "per_paper_analysis_manifest.jsonl"
    if not manifest_path.exists():
        raise SystemExit(f"Missing per-paper manifest: {manifest_path}")
    out_dir = (args.out_dir or run_dir / "analysis" / "assistant_deep_read_packets").resolve()
    records = load_jsonl(manifest_path)
    if args.paper_key:
        wanted = set(args.paper_key)
        records = [record for record in records if str(record.get("paper_key")) in wanted]
    if args.limit:
        records = records[: args.limit]
    queue: list[dict[str, Any]] = []
    for record in records:
        paper_key = str(record.get("paper_key") or "")
        if not paper_key:
            continue
        paper_dir = run_dir / "analysis" / "per_paper" / paper_key
        pdf_text_path = paper_dir / "pdf_text.txt"
        if not pdf_text_path.exists():
            raise SystemExit(f"Missing extracted PDF text for {paper_key}: {pdf_text_path}")
        packet_dir = out_dir / paper_key
        chunk_dir = packet_dir / "chunks"
        chunk_dir.mkdir(parents=True, exist_ok=True)
        pdf_text = pdf_text_path.read_text(encoding="utf-8", errors="replace")
        chunk_paths: list[Path] = []
        for index, chunk in enumerate(chunk_text(pdf_text, args.chunk_chars, args.overlap_chars), 1):
            chunk_path = chunk_dir / f"chunk_{index:03d}.txt"
            chunk_path.write_text(chunk, encoding="utf-8")
            chunk_paths.append(chunk_path)
        request = {
            "schema_version": "1.0",
            "route": "current-assistant-local-file-deep-read",
            "paper_key": paper_key,
            "required_record_keys": REQUIRED_RECORD_KEYS,
            "source_files": {
                "pdf_text": rel(pdf_text_path, run_dir),
                "analysis_record": rel(paper_dir / "analysis_record.json", run_dir),
                "source_ledger": rel(paper_dir / "source_ledger.json", run_dir),
                "review_reply_ledger": rel(paper_dir / "review_reply_ledger.json", run_dir),
            },
            "chunk_files": [rel(path, run_dir) for path in chunk_paths],
            "output_record": rel(packet_dir / "assistant_deep_read_record.json", run_dir),
        }
        write_json(packet_dir / "request.json", request)
        (packet_dir / "packet.md").write_text(packet_markdown(run_dir, paper_key, packet_dir, record, chunk_paths), encoding="utf-8")
        queue.append(
            {
                "paper_key": paper_key,
                "packet": rel(packet_dir / "packet.md", run_dir),
                "request": rel(packet_dir / "request.json", run_dir),
                "output_record": rel(packet_dir / "assistant_deep_read_record.json", run_dir),
                "chunk_count": len(chunk_paths),
                "status": "waiting_for_current_assistant_read",
            }
        )
    write_jsonl(out_dir / "queue.jsonl", queue)
    write_json(
        out_dir / "index.json",
        {
            "schema_version": "1.0",
            "run_dir": str(run_dir),
            "packet_dir": str(out_dir),
            "paper_count": len(queue),
            "chunk_chars": args.chunk_chars,
            "overlap_chars": args.overlap_chars,
            "queue": queue,
        },
    )
    return {"packet_dir": str(out_dir), "paper_count": len(queue), "queue": str(out_dir / "queue.jsonl")}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare file-based packets for current-assistant local full-paper deep reading.")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--paper-key", nargs="*", default=[])
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--chunk-chars", type=int, default=45000)
    parser.add_argument("--overlap-chars", type=int, default=1200)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(prepare(parse_args()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
