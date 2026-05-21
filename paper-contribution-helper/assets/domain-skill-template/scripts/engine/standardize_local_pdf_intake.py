#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
from pathlib import Path

from common import read_json, write_json


DEFAULT_RUN_ROOT = Path("corpus_runs")


def slugify(text: str, max_len: int = 90) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    return (text or "paper")[:max_len].strip("_")


def find_pair(folder: Path | None, stem: str, names: list[str]) -> Path | None:
    if folder is None or not folder.exists():
        return None
    candidates: list[Path] = []
    for suffix in [".json", ".md", ".txt"]:
        candidates.append(folder / f"{stem}{suffix}")
    for name in names:
        for suffix in [".json", ".md", ".txt"]:
            candidates.append(folder / f"{stem}.{name}{suffix}")
            candidates.append(folder / f"{stem}_{name}{suffix}")
    for path in candidates:
        if path.exists():
            return path
    return None


def collect_pdfs(pdf: Path | None, pdf_dir: Path | None) -> list[Path]:
    paths: list[Path] = []
    if pdf:
        paths.append(pdf.resolve())
    if pdf_dir:
        paths.extend(sorted(path.resolve() for path in pdf_dir.rglob("*.pdf")))
    seen: set[Path] = set()
    out: list[Path] = []
    for path in paths:
        if path not in seen:
            seen.add(path)
            out.append(path)
    return out


def copy_if_present(src: Path | None, dst: Path) -> bool:
    if src is None:
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def prepare_one(pdf_path: Path, run_dir: Path, reviews_dir: Path | None, replies_dir: Path | None, metadata_dir: Path | None, source_kind: str, domain_scope: str) -> dict[str, object]:
    paper_key = slugify(pdf_path.stem)
    material_dir = run_dir / "materials" / "_by_paper" / paper_key
    material_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(pdf_path, material_dir / "paper.pdf")

    metadata_path = find_pair(metadata_dir, pdf_path.stem, ["submission", "metadata"])
    metadata = read_json(metadata_path) if metadata_path else {}
    if not metadata:
        metadata = {
            "title": pdf_path.stem,
            "venue": "local-pdf",
            "year": None,
            "primary_area": domain_scope,
            "keywords": [],
        }
    metadata.setdefault("source_kind", source_kind)
    metadata.setdefault("domain_scope", domain_scope)
    metadata.setdefault("local_pdf_name", pdf_path.name)
    write_json(material_dir / "submission.json", metadata)

    review_path = find_pair(reviews_dir, pdf_path.stem, ["reviews", "official_reviews"])
    reply_path = find_pair(replies_dir, pdf_path.stem, ["replies", "author_replies", "rebuttal"])
    review_copied = copy_if_present(review_path, material_dir / ("official_reviews.json" if review_path and review_path.suffix.lower() == ".json" else "official_reviews.md"))
    reply_copied = copy_if_present(reply_path, material_dir / ("author_replies.json" if reply_path and reply_path.suffix.lower() == ".json" else "author_replies.md"))

    source_status = {
        "schema_version": "1.0",
        "source_kind": source_kind,
        "domain_scope": domain_scope,
        "source_pdf": pdf_path.as_posix(),
        "pdf_available": True,
        "metadata_available": metadata_path is not None,
        "reviews_missing": not review_copied,
        "replies_missing": not reply_copied,
        "review_attack_mode": "real-review" if review_copied else "simulated-review-only",
        "created_at": dt.datetime.now().isoformat(timespec="seconds"),
    }
    write_json(material_dir / "source_status.json", source_status)
    return {"paper_key": paper_key, "material_dir": material_dir.relative_to(run_dir).as_posix(), "source_status": source_status}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Standardize local PDF(s) into a project corpus run structure.")
    parser.add_argument("--pdf", type=Path, default=None)
    parser.add_argument("--pdf-dir", type=Path, default=None)
    parser.add_argument("--reviews-dir", type=Path, default=None)
    parser.add_argument("--replies-dir", type=Path, default=None)
    parser.add_argument("--metadata-dir", type=Path, default=None)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--source-kind", default="local-pdf")
    parser.add_argument("--domain-scope", default="computer-science")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pdfs = collect_pdfs(args.pdf, args.pdf_dir)
    if not pdfs:
        raise SystemExit("Provide --pdf or --pdf-dir with at least one PDF.")
    run_id = dt.datetime.now().strftime("local_pdf_%Y%m%d_%H%M%S")
    run_dir = (args.run_dir or (DEFAULT_RUN_ROOT / run_id)).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    records = [
        prepare_one(
            pdf_path,
            run_dir,
            args.reviews_dir.resolve() if args.reviews_dir else None,
            args.replies_dir.resolve() if args.replies_dir else None,
            args.metadata_dir.resolve() if args.metadata_dir else None,
            args.source_kind,
            args.domain_scope,
        )
        for pdf_path in pdfs
    ]
    config = {
        "schema_version": "1.0",
        "run_id": run_dir.name,
        "source_kind": args.source_kind,
        "domain_scope": args.domain_scope,
        "paper_count": len(records),
        "records": records,
        "created_at": dt.datetime.now().isoformat(timespec="seconds"),
    }
    write_json(run_dir / "config.json", config)
    print(json.dumps({"run_dir": str(run_dir), "paper_count": len(records)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
