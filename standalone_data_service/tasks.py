from __future__ import annotations

from datetime import datetime, timezone
from traceback import format_exc

from .celery_app import app
from .readers import build_overview_snapshot
from .storage import write_overview_snapshot, write_run_meta


@app.task(name="standalone_data_service.tasks.refresh_overview_snapshot")
def refresh_overview_snapshot() -> dict:
    started_at = datetime.now(timezone.utc).isoformat()
    try:
        snapshot = build_overview_snapshot()
        write_overview_snapshot(snapshot)
        result = {
            "status": "success",
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "block_count": len(snapshot.get("blocks", [])),
            "output_file": "standalone_data_service/output/overview_snapshot.json",
        }
        write_run_meta(result)
        return result
    except Exception as exc:  # pragma: no cover
        result = {
            "status": "error",
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "error": str(exc),
            "traceback": format_exc(),
        }
        write_run_meta(result)
        raise
