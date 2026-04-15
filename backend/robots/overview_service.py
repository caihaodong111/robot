from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import pymysql
from django.conf import settings
from django.utils import timezone

DEFAULT_WAM_FILE = settings.BASE_DIR.parent / "设备状态.xlsx"
DEFAULT_FILLING_FILE = settings.BASE_DIR.parent / "MRA1_filling_status.xlsx"
DEFAULT_LENZE_FILE = settings.BASE_DIR.parent / "temperature_min_max_results.xlsx"
DEFAULT_SNAPSHOT_FILE = settings.BASE_DIR / "exports" / "portal_overview_snapshot.json"
GROUP_DISTRIBUTION_LIMIT = 8
EXCLUDED_GROUP_KEYS = ['', '(空)', '未分配']

GROUP_DISTRIBUTION_SQL = """
SELECT
    COALESCE(NULLIF(g.name, ''), NULLIF(g.`key`, ''), 'UNKNOWN') AS group_name,
    COUNT(*) AS component_count
FROM robot_components rc
LEFT JOIN robot_groups g ON g.id = rc.group_id
GROUP BY COALESCE(NULLIF(g.name, ''), NULLIF(g.`key`, ''), 'UNKNOWN')
ORDER BY component_count DESC, group_name ASC
LIMIT %s
"""


def _now_iso() -> str:
    return timezone.now().isoformat()


def _datetime_to_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.get_current_timezone())
    return value.isoformat()


def _path_from_env(env_key: str, default_path: Path) -> Path:
    raw_value = (os.getenv(env_key) or "").strip()
    path = Path(raw_value).expanduser() if raw_value else default_path
    if not path.exists():
        raise FileNotFoundError(f"{env_key} 指向的文件不存在: {path}")
    return path


def _resolve_latest_csv_in_dir(dir_path: Path, env_key: str) -> Path:
    candidate_files = [
        path
        for path in dir_path.iterdir()
        if path.is_file()
        and path.suffix.lower() in {".csv", ".xlsx", ".xls"}
        and not path.name.startswith(".")
        and not path.name.startswith("~$")
    ]
    if not candidate_files:
        raise FileNotFoundError(f"{env_key} 指向的目录下未找到 CSV/XLSX 文件: {dir_path}")
    return max(candidate_files, key=lambda path: path.stat().st_mtime)


def _table_source_from_env(env_key: str, default_path: Path) -> Path:
    path = _path_from_env(env_key, default_path)
    if path.is_dir():
        return _resolve_latest_csv_in_dir(path, env_key)
    return path


def get_wam_file_path() -> Path:
    return _table_source_from_env("PORTAL_WAM_FILE", DEFAULT_WAM_FILE)


def get_filling_file_path() -> Path:
    return _table_source_from_env("PORTAL_FILLING_FILE", DEFAULT_FILLING_FILE)


def get_lenze_file_path() -> Path:
    return _table_source_from_env("PORTAL_LENZE_FILE", DEFAULT_LENZE_FILE)


def get_snapshot_file_path() -> Path:
    raw_value = (os.getenv("PORTAL_OVERVIEW_SNAPSHOT_FILE") or "").strip()
    return Path(raw_value).expanduser() if raw_value else DEFAULT_SNAPSHOT_FILE


def read_table_file(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    raise ValueError(f"不支持的文件类型: {path}")


def _normalize_status(value: Any) -> str:
    text = str(value).strip()
    upper_text = text.upper()
    if upper_text == "OK":
        return "OK"
    if upper_text == "NOK":
        return "NOK"
    if upper_text == "WARNING":
        return "Warning"
    if upper_text == "ALARM":
        return "Alarm"
    if not text:
        return "UNKNOWN"
    return text


def _value_counts(series: pd.Series) -> dict[str, int]:
    if series is None:
        return {}
    counts = (
        series.fillna("UNKNOWN")
        .map(_normalize_status)
        .value_counts()
        .to_dict()
    )
    return {str(key): int(value) for key, value in counts.items()}


def _file_mtime_iso(path: Path) -> str:
    modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.get_current_timezone())
    return modified_at.isoformat()


def _build_status_types(df: pd.DataFrame) -> list[str]:
    if "alarm" not in df.columns:
        return []
    raw_values = sorted({str(value).strip() for value in df["alarm"].dropna().tolist() if str(value).strip()})
    if not raw_values:
        return []
    return [chunk.strip() for chunk in raw_values[0].split("/") if chunk.strip()]


def _normalize_wam_alarm(value: Any) -> str:
    text = str(value).strip()
    if not text:
        return "UNKNOWN"

    upper_text = text.upper()
    if upper_text == "OK":
        return "OK"
    if upper_text == "WARNING":
        return "Warning"
    if upper_text == "FAULT":
        return "Fault"
    return text


def _build_wam_alarm_counts(df: pd.DataFrame) -> dict[str, int]:
    if "alarm" not in df.columns:
        return {}

    counts = (
        df["alarm"]
        .map(_normalize_wam_alarm)
        .value_counts()
        .to_dict()
    )
    return {str(key): int(value) for key, value in counts.items() if str(key).strip()}


@dataclass
class SnapshotBlock:
    key: str
    title: str
    updated_at: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "title": self.title,
            "updated_at": self.updated_at,
            "payload": self.payload,
        }


def build_wam_snapshot() -> SnapshotBlock:
    wam_file = get_wam_file_path()
    df = read_table_file(wam_file)
    status_counts = _build_wam_alarm_counts(df)

    categories = []
    if "Category" in df.columns:
        categories = sorted(df["Category"].dropna().astype(str).unique().tolist())

    device_preview = []
    if "unique_id" in df.columns:
        device_preview = df["unique_id"].dropna().astype(str).head(6).tolist()

    payload = {
        "source_file": str(wam_file),
        "device_count": int(len(df)),
        "status_counts": status_counts,
        "category_count": int(df["Category"].nunique(dropna=True)) if "Category" in df.columns else 0,
        "categories": categories,
        "device_preview": device_preview,
    }
    return SnapshotBlock(key="wam", title="WAM", updated_at=_file_mtime_iso(wam_file), payload=payload)


def build_filling_snapshot() -> SnapshotBlock:
    filling_file = get_filling_file_path()
    df = read_table_file(filling_file)

    status_counts = _value_counts(df["fin_status"]) if "fin_status" in df.columns else {}
    station_breakdown: list[dict[str, Any]] = []

    if {"devicename_process", "fin_status"}.issubset(df.columns):
        stations = (
            df.assign(
                station=df["devicename_process"]
                .astype(str)
                .str.extract(r"(MRA1_Filing\d+)", expand=False)
                .fillna(df["devicename_process"].astype(str))
            )
            .assign(fin_status=df["fin_status"].map(_normalize_status))
            .pivot_table(index="station", columns="fin_status", aggfunc="size", fill_value=0)
            .reset_index()
        )

        for _, row in stations.iterrows():
            ok_count = int(row.get("OK", 0))
            nok_count = int(row.get("NOK", 0))
            total = ok_count + nok_count
            station_breakdown.append(
                {
                    "station": str(row["station"]),
                    "ok": ok_count,
                    "nok": nok_count,
                    "total": total,
                }
            )

    latest_timestamp = None
    if "dtime" in df.columns and not df.empty:
        latest_timestamp = str(df["dtime"].astype(str).max())

    payload = {
        "source_file": str(filling_file),
        "record_count": int(len(df)),
        "status_counts": status_counts,
        "station_breakdown": station_breakdown,
        "latest_timestamp": latest_timestamp,
    }
    return SnapshotBlock(key="filling", title="Filling", updated_at=_file_mtime_iso(filling_file), payload=payload)


def build_lenze_snapshot() -> SnapshotBlock:
    lenze_file = get_lenze_file_path()
    df = read_table_file(lenze_file)

    status_counts = _value_counts(df["Alarm"]) if "Alarm" in df.columns else {}
    temp_columns = [
        "device_temp_max",
        "device_temp_min",
        "heatsink_temp_max",
        "heatsink_temp_min",
    ]
    stats: dict[str, dict[str, float]] = {}
    for column in temp_columns:
        if column not in df.columns:
            continue
        series = pd.to_numeric(df[column], errors="coerce").dropna()
        if series.empty:
            continue
        stats[column] = {
            "min": float(series.min()),
            "avg": float(round(series.mean(), 2)),
            "max": float(series.max()),
        }

    payload = {
        "source_file": str(lenze_file),
        "record_count": int(len(df)),
        "status_counts": status_counts,
        "temperature_summary": stats,
    }
    return SnapshotBlock(key="lenze", title="Lenze", updated_at=_file_mtime_iso(lenze_file), payload=payload)


def _get_portal_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "iot_monitor"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def build_high_risk_snapshot() -> SnapshotBlock:
    groups = []
    total_components = 0
    total_high_risk = 0
    placeholders = ', '.join(['%s'] * len(EXCLUDED_GROUP_KEYS))
    stats_sql = f"""
    SELECT
        g.`key` AS group_key,
        COALESCE(NULLIF(g.name, ''), NULLIF(g.`key`, ''), 'UNKNOWN') AS group_name,
        COUNT(rc.id) AS total_count,
        SUM(CASE WHEN rc.level = 'H' THEN 1 ELSE 0 END) AS high_risk_count
    FROM robot_groups g
    LEFT JOIN robot_components rc ON rc.group_id = g.id
    WHERE g.`key` NOT IN ({placeholders})
    GROUP BY g.id, g.`key`, g.name
    ORDER BY total_count DESC, group_name ASC
    """

    with _get_portal_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(stats_sql, EXCLUDED_GROUP_KEYS)
            rows = cursor.fetchall()
            cursor.execute("SELECT MAX(updated_at) AS latest_updated_at FROM robot_components")
            latest_row = cursor.fetchone() or {}

    for row in rows:
        label = str((row or {}).get("group_name") or "UNKNOWN").strip() or "UNKNOWN"
        total_count = int((row or {}).get("total_count") or 0)
        high_risk_count = int((row or {}).get("high_risk_count") or 0)
        total_components += total_count
        total_high_risk += high_risk_count
        groups.append({
            "group": label,
            "count": total_count,
            "high_risk": high_risk_count,
            "key": (row or {}).get("group_key") or "",
        })

    latest_component_update = latest_row.get("latest_updated_at")

    payload = {
        "database": os.getenv("DB_NAME", settings.DATABASES["default"]["NAME"]),
        "group_count": len(groups),
        "total_count": total_components,
        "total_high_risk": total_high_risk,
        "groups": groups[:GROUP_DISTRIBUTION_LIMIT],
        "all_groups": groups,
    }
    return SnapshotBlock(
        key="high_risk_distribution",
        title="High-Risk Distribution",
        updated_at=_datetime_to_iso(latest_component_update) or _now_iso(),
        payload=payload,
    )


def build_overview_snapshot() -> dict[str, Any]:
    blocks = [
        build_wam_snapshot(),
        build_lenze_snapshot(),
        build_filling_snapshot(),
        build_high_risk_snapshot(),
    ]
    return {
        "generated_at": _now_iso(),
        "blocks": [block.to_dict() for block in blocks],
    }


def save_overview_snapshot(snapshot: dict[str, Any]) -> Path:
    output_file = get_snapshot_file_path()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_file


def load_saved_overview_snapshot() -> dict[str, Any] | None:
    snapshot_file = get_snapshot_file_path()
    if not snapshot_file.exists():
        return None
    return json.loads(snapshot_file.read_text(encoding="utf-8"))


def refresh_overview_snapshot() -> tuple[dict[str, Any], Path]:
    snapshot = build_overview_snapshot()
    output_file = save_overview_snapshot(snapshot)
    return snapshot, output_file
