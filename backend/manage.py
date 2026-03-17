#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # Ensure we do not accidentally boot with a different project's settings.
    current_settings = os.environ.get("DJANGO_SETTINGS_MODULE")
    if current_settings and not current_settings.startswith("iot_monitor."):
        sys.stderr.write(
            "Warning: Overriding DJANGO_SETTINGS_MODULE="
            f"{current_settings} with iot_monitor.settings for this project.\n"
        )
    os.environ["DJANGO_SETTINGS_MODULE"] = "iot_monitor.settings"
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
