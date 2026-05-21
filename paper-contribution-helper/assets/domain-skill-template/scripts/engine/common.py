from __future__ import annotations

import json
import os
import re
from pathlib import Path


PROJECT_DIR_NAME = ".delta-contribution-reframer"


def default_project_dir() -> Path:
    override = os.environ.get("DELTA_CONTRIBUTION_REFRAMER_HOME")
    if override:
        return Path(override).expanduser().resolve()
    return (Path.cwd() / PROJECT_DIR_NAME).resolve()


def default_state_dir() -> Path:
    return default_project_dir() / "state"


def default_references_dir() -> Path:
    return default_project_dir() / "references"


def clean(text: str) -> str:
    text = re.sub(r"\r\n?", "\n", text or "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def nonempty(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 2


def split_keywords(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        raw = ",".join(str(x) for x in value)
    else:
        raw = str(value)
    out: list[str] = []
    for part in raw.replace(";", ",").split(","):
        part = clean(part)
        if part:
            out.append(part)
    return out
