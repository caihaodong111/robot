from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, text

from .config import DATABASE_URL, FILLING_FILE, HIGH_RISK_SQL, LENZE_FILE, WAM_FILE


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_table_file(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    raise ValueError(f"Unsupported file type: {path}")


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
    df = read_table_file(WAM_FILE)
    alarm_raw = sorted({str(value).strip() for value in df["alarm"].dropna().tolist()})
    status_types = []
    if alarm_raw:
        status_types = [chunk.strip() for chunk in alarm_raw[0].split("/") if chunk.strip()]

    payload = {
        "source_file": str(WAM_FILE),
        "device_count": int(len(df)),
        "category_count": int(df["Category"].nunique(dropna=True)),
        "categories": sorted(df["Category"].dropna().astype(str).unique().tolist()),
        "status_types": status_types,
        "device_preview": df["unique_id"].head(6).astype(str).tolist(),
        "note": "Current file exposes device list and status types. It does not contain a per-device current OK/NOK value.",
    }
    return SnapshotBlock(key="wam", title="WAM", updated_at=utc_now_iso(), payload=payload)


def build_filling_snapshot() -> SnapshotBlock:
    df = read_table_file(FILLING_FILE)
    status_counts = {
        str(key): int(value)
        for key, value in df["fin_status"].fillna("UNKNOWN").astype(str).value_counts().to_dict().items()
    }

    stations = (
        df.assign(station=df["devicename_process"].astype(str).str.extract(r"(MRA1_Filing\d+)"))
        .pivot_table(index="station", columns="fin_status", aggfunc="size", fill_value=0)
        .reset_index()
    )

    station_breakdown = []
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

    payload = {
        "source_file": str(FILLING_FILE),
        "record_count": int(len(df)),
        "status_counts": status_counts,
        "station_breakdown": station_breakdown,
        "latest_timestamp": str(df["dtime"].astype(str).max()) if not df.empty else None,
    }
    return SnapshotBlock(key="filling", title="Filling", updated_at=utc_now_iso(), payload=payload)


def build_lenze_snapshot() -> SnapshotBlock:
    df = read_table_file(LENZE_FILE)
    status_counts = {
        str(key): int(value)
        for key, value in df["Alarm"].fillna("UNKNOWN").astype(str).value_counts().to_dict().items()
    }

    temp_columns = [
        "device_temp_max",
        "device_temp_min",
        "heatsink_temp_max",
        "heatsink_temp_min",
    ]
    stats = {}
    for column in temp_columns:
        if column in df.columns:
            series = pd.to_numeric(df[column], errors="coerce").dropna()
            if not series.empty:
                stats[column] = {
                    "min": float(series.min()),
                    "avg": float(round(series.mean(), 2)),
                    "max": float(series.max()),
                }

    payload = {
        "source_file": str(LENZE_FILE),
        "record_count": int(len(df)),
        "status_counts": status_counts,
        "temperature_summary": stats,
    }
    return SnapshotBlock(key="lenze", title="Lenze", updated_at=utc_now_iso(), payload=payload)


def build_high_risk_snapshot() -> SnapshotBlock:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
    try:
        with engine.connect() as connection:
            rows = connection.execute(text(HIGH_RISK_SQL)).mappings().all()
    finally:
        engine.dispose()

    groups = []
    total_high_risk = 0
    for row in rows:
        count = int(row["high_risk_count"])
        groups.append({"group": str(row["group_name"]), "high_risk_count": count})
        total_high_risk += count

    payload = {
        "database": "mysql://sg@20.5.234.198:3306/sg",
        "group_count": len(groups),
        "total_high_risk": total_high_risk,
        "groups": groups,
    }
    return SnapshotBlock(
        key="high_risk_distribution",
        title="High-Risk Distribution",
        updated_at=utc_now_iso(),
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
        "generated_at": utc_now_iso(),
        "blocks": [block.to_dict() for block in blocks],
    }
