import os

from bokeh.server.server import Server
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run BI Bokeh Server (Digitaltwin_timefree.py style)."

    def _normalize_origin(self, value: str) -> str | None:
        value = (value or "").strip()
        if not value:
            return None
        value = value.replace("http://", "").replace("https://", "")
        return value.strip().strip("/")

    def add_arguments(self, parser):
        parser.add_argument("--port", type=int, default=int(os.getenv("BI_BOKEH_PORT", "5008")))
        parser.add_argument("--address", type=str, default=os.getenv("BI_BOKEH_ADDRESS", "0.0.0.0"))
        parser.add_argument(
            "--log-level",
            type=str,
            default=(os.getenv("BI_BOKEH_LOG_LEVEL") or "INFO"),
            help="Python/Tornado log level (DEBUG/INFO/WARNING/ERROR).",
        )
        parser.add_argument(
            "--log-file",
            type=str,
            default=(os.getenv("BI_BOKEH_LOG_FILE") or "").strip() or None,
            help="Optional extra log file path for this Bokeh server process.",
        )
        parser.add_argument(
            "--access-log",
            action="store_true",
            default=os.getenv("BI_BOKEH_ACCESS_LOG", "1") == "1",
            help="Enable Tornado access log (HTTP requests) in terminal/file.",
        )
        parser.add_argument(
            "--allow-origin",
            action="append",
            dest="allow_origins",
            default=[],
            help="Allowed websocket origin, e.g. localhost:8000 (repeatable).",
        )
        parser.add_argument(
            "--session-token-expiration",
            type=int,
            default=int(os.getenv("BI_BOKEH_SESSION_TOKEN_EXPIRATION", "300")),
            help="Session token expiration time in seconds (default: 300).",
        )

    def handle(self, *args, **options):
        import logging
        import logging.config

        from django.conf import settings

        def _parse_level(value: str) -> int:
            return getattr(logging, (value or "INFO").strip().upper(), logging.INFO)

        # Re-apply Django logging config in case Bokeh changed it at import time.
        # Also ensure something prints to stdout even when no handlers exist (e.g. systemd/no-tty).
        try:
            logging.config.dictConfig(settings.LOGGING)
        except Exception:
            pass
        root_logger = logging.getLogger()
        if not root_logger.handlers:
            logging.basicConfig(
                level=_parse_level(options.get("log_level")),
                format="%(levelname)s %(asctime)s %(name)s %(message)s",
                force=True,
            )

        log_level = _parse_level(options.get("log_level"))
        root_logger.setLevel(log_level)

        extra_log_file = options.get("log_file")
        if extra_log_file:
            file_handler = logging.FileHandler(extra_log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(
                logging.Formatter("%(levelname)s %(asctime)s %(name)s %(process)d %(thread)d %(message)s")
            )
            root_logger.addHandler(file_handler)

        if options.get("access_log"):
            access_logger = logging.getLogger("tornado.access")
            access_logger.setLevel(logging.INFO)
            access_logger.propagate = True

        from robots.bi_bokeh_app import bkapp

        port = options["port"]
        address = options["address"]

        allow_origins = [v for v in (self._normalize_origin(x) for x in (options["allow_origins"] or [])) if v]
        env_origins = (os.getenv("BI_BOKEH_ALLOW_ORIGINS") or "").strip()
        if env_origins:
            allow_origins.extend([v for v in (self._normalize_origin(x) for x in env_origins.split(",")) if v])
        if not allow_origins:
            settings_hosts = getattr(settings, "ALLOWED_HOSTS", []) or []
            extra_hosts = [
                h
                for h in (self._normalize_origin(x) for x in settings_hosts)
                if h and h not in {"*", "localhost", "127.0.0.1", "0.0.0.0"}
            ]
            common_ports = [8001, 8000, 8080, 5173, 5174]
            for host in extra_hosts:
                for p in common_ports:
                    allow_origins.append(f"{host}:{p}")

            # sensible defaults for local dev / common LAN IPs
            allow_origins = [
                # local
                "localhost:8001",
                "127.0.0.1:8001",
                "localhost:5173",
                "127.0.0.1:5173",
                "localhost:5174",
                "127.0.0.1:5174",
                # existing LAN
                "172.20.10.3:8001",
                "172.20.10.3:5173",
                # new LAN
                "172.16.180.26:8001",
                "172.16.180.26:5173",
                # legacy dev ports
                "localhost:8000",
                "127.0.0.1:8000",
                "localhost:8080",
                "127.0.0.1:8080",
            ]

        allow_origins = sorted({v for v in allow_origins if v})
        server = Server(
            {"/": bkapp},
            port=port,
            address=address,
            allow_websocket_origin=allow_origins,
            session_token_expiration=options["session_token_expiration"],
        )
        server.start()
        self.stdout.write(self.style.SUCCESS(f"BI Bokeh Server running on http://{address}:{port}/"))
        self.stdout.write(self.style.SUCCESS(f"allow_websocket_origin={allow_origins}"))
        self.stdout.write(self.style.SUCCESS(f"log_level={options.get('log_level')} access_log={bool(options.get('access_log'))}"))
        try:
            self.stdout.flush()
        except Exception:
            pass
        server.io_loop.start()
