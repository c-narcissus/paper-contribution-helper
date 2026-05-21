#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

from common import default_state_dir, split_keywords, write_json


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = default_state_dir() / "corpus_catalog.json"
DEFAULT_MD = default_state_dir() / "corpus_catalog.md"


def iter_submission_json(source: Path):
    if source.is_dir():
        for path in source.rglob("submission.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            except Exception as exc:
                yield {"_error": str(exc), "_source": path.name}
                continue
            data["_source"] = path.name
            yield data
        for zip_path in source.rglob("*.zip"):
            yield from iter_zip_submission_json(zip_path)
    elif source.suffix.lower() == ".zip":
        yield from iter_zip_submission_json(source)
    elif source.name.lower().endswith(".json"):
        try:
            data = json.loads(source.read_text(encoding="utf-8", errors="replace"))
        except Exception as exc:
            yield {"_error": str(exc), "_source": source.name}
            return
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    yield item
        elif isinstance(data, dict):
            yield data


def iter_zip_submission_json(zip_path: Path):
    try:
        with zipfile.ZipFile(zip_path) as zf:
            for name in zf.namelist():
                if not name.lower().endswith("submission.json"):
                    continue
                try:
                    data = json.loads(zf.read(name).decode("utf-8", errors="replace"))
                except Exception as exc:
                    yield {"_error": str(exc), "_source": zip_path.name}
                    continue
                data["_source"] = zip_path.name
                yield data
    except Exception as exc:
        yield {"_error": str(exc), "_source": zip_path.name}


def build_catalog(source: Path) -> dict[str, object]:
    year_counts: Counter[str] = Counter()
    area_counts: Counter[str] = Counter()
    area_year_counts: dict[str, Counter[str]] = defaultdict(Counter)
    keyword_counts: Counter[str] = Counter()
    errors = 0
    total = 0

    for item in iter_submission_json(source):
        if item.get("_error"):
            errors += 1
            continue
        total += 1
        year = str(item.get("year") or item.get("venue_year") or "unknown")
        area = str(item.get("primary_area") or item.get("area") or item.get("subject_area") or "unknown").strip() or "unknown"
        year_counts[year] += 1
        area_counts[area] += 1
        area_year_counts[area][year] += 1
        for kw in split_keywords(item.get("keywords")):
            keyword_counts[kw] += 1

    years = sorted(year_counts.keys())
    areas = [
        {"area": area, "total": count, "by_year": {year: area_year_counts[area].get(year, 0) for year in years}}
        for area, count in area_counts.most_common()
    ]
    return {
        "schema_version": "1.0",
        "available": total > 0,
        "source": "user-provided corpus source",
        "submission_count": total,
        "years": {year: year_counts[year] for year in years},
        "areas": areas,
        "top_keywords": [{"keyword": kw, "count": count} for kw, count in keyword_counts.most_common(80)],
        "error_count": errors,
    }


def write_md(catalog: dict[str, object], path: Path) -> None:
    years = list((catalog.get("years") or {}).keys())
    lines = [
        "# Corpus Catalog",
        "",
        f"- Source: {catalog.get('source')}",
        f"- Submission metadata scanned: {catalog.get('submission_count')}",
        f"- Years: {', '.join(years) if years else 'not found'}",
        f"- Metadata extraction errors: {catalog.get('error_count')}",
        "",
        "## Areas",
        "",
    ]
    header = ["Area", "Total", *years]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "|".join("---" for _ in header) + "|")
    for row in catalog.get("areas", []):
        by_year = row.get("by_year", {})
        values = [str(row.get("area", "")), str(row.get("total", 0)), *[str(by_year.get(year, 0)) for year in years]]
        lines.append("| " + " | ".join(values) + " |")
    lines.extend(["", "## Top Keywords", ""])
    for kw in catalog.get("top_keywords", [])[:40]:
        lines.append(f"- {kw.get('keyword')}: {kw.get('count')}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan a user-provided corpus and build a field/year catalog.")
    parser.add_argument("--corpus-source", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_MD)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = args.corpus_source.expanduser()
    if not source.exists():
        raise SystemExit(f"Corpus source does not exist: {source}")
    catalog = build_catalog(source)
    write_json(args.out_json, catalog)
    write_md(catalog, args.out_md)
    print(json.dumps({"catalog_json": str(args.out_json), "catalog_md": str(args.out_md), "submission_count": catalog["submission_count"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
