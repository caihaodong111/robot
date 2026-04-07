from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .config import OVERVIEW_OUTPUT_FILE
from .readers import build_overview_snapshot
from .storage import write_overview_snapshot, write_run_meta

HOST = "127.0.0.1"
PORT = 8765


def build_and_persist_snapshot() -> dict:
    snapshot = build_overview_snapshot()
    write_overview_snapshot(snapshot)
    write_run_meta(
        {
            "status": "success",
            "mode": "manual-refresh",
            "output_file": str(OVERVIEW_OUTPUT_FILE),
            "block_count": len(snapshot.get("blocks", [])),
            "generated_at": snapshot.get("generated_at"),
        }
    )
    return snapshot


def load_existing_snapshot() -> dict | None:
    if not OVERVIEW_OUTPUT_FILE.exists():
        return None
    return json.loads(OVERVIEW_OUTPUT_FILE.read_text(encoding="utf-8"))


class DevApiHandler(BaseHTTPRequestHandler):
    server_version = "StandaloneDataService/0.1"

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send_json({"status": "ok", "service": "standalone_data_service"})
            return

        if self.path == "/snapshot":
            snapshot = load_existing_snapshot()
            if snapshot is None:
                self._send_json(
                    {
                        "status": "empty",
                        "message": "No snapshot file found. Trigger POST /refresh first.",
                    },
                    status=404,
                )
                return
            self._send_json({"status": "ok", "snapshot": snapshot})
            return

        self._send_json({"status": "not_found", "path": self.path}, status=404)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/refresh":
            self._send_json({"status": "not_found", "path": self.path}, status=404)
            return

        try:
            snapshot = build_and_persist_snapshot()
            self._send_json({"status": "ok", "snapshot": snapshot})
        except Exception as exc:  # pragma: no cover
            self._send_json({"status": "error", "message": str(exc)}, status=500)


def run() -> None:
    server = ThreadingHTTPServer((HOST, PORT), DevApiHandler)
    print(f"Standalone data dev API running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run()
