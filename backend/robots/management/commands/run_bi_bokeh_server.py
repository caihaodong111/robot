import os

from bokeh.server.server import Server
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run BI Bokeh Server (Digitaltwin_timefree.py style)."

    def add_arguments(self, parser):
        parser.add_argument("--port", type=int, default=int(os.getenv("BI_BOKEH_PORT", "5008")))
        parser.add_argument("--address", type=str, default=os.getenv("BI_BOKEH_ADDRESS", "0.0.0.0"))
        parser.add_argument(
            "--allow-origin",
            action="append",
            dest="allow_origins",
            default=[],
            help="Allowed websocket origin, e.g. localhost:8000 (repeatable).",
        )

    def handle(self, *args, **options):
        from robots.bi_bokeh_app import bkapp

        port = options["port"]
        address = options["address"]

        allow_origins = options["allow_origins"] or []
        env_origins = (os.getenv("BI_BOKEH_ALLOW_ORIGINS") or "").strip()
        if env_origins:
            allow_origins.extend([v.strip() for v in env_origins.split(",") if v.strip()])
        if not allow_origins:
            # sensible defaults for local dev
            allow_origins = ["localhost:8000", "127.0.0.1:8000", "localhost:8080", "127.0.0.1:8080"]

        server = Server({"/": bkapp}, port=port, address=address, allow_websocket_origin=allow_origins)
        server.start()
        self.stdout.write(self.style.SUCCESS(f"BI Bokeh Server running on http://{address}:{port}/"))
        self.stdout.write(self.style.SUCCESS(f"allow_websocket_origin={allow_origins}"))
        server.io_loop.start()

