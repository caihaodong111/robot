from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import OUTPUT_DIR, OVERVIEW_OUTPUT_FILE, RUN_META_OUTPUT_FILE


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_output_dir()
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_overview_snapshot(payload: dict[str, Any]) -> None:
    write_json(OVERVIEW_OUTPUT_FILE, payload)


def write_run_meta(payload: dict[str, Any]) -> None:
    write_json(RUN_META_OUTPUT_FILE, payload)
