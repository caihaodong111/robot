from celery import Celery
from celery.schedules import crontab

from .config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

app = Celery(
    "standalone_data_service",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

app.conf.timezone = "Asia/Shanghai"
app.conf.enable_utc = False
app.conf.task_serializer = "json"
app.conf.result_serializer = "json"
app.conf.accept_content = ["json"]
app.conf.beat_schedule = {
    "refresh-standalone-overview-daily": {
        "task": "standalone_data_service.tasks.refresh_overview_snapshot",
        "schedule": crontab(hour=0, minute=0),
    }
}

app.autodiscover_tasks(["standalone_data_service"])
