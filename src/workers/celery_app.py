from celery import Celery
from src.config import get_settings
from celery.schedules import crontab

settings = get_settings()

celery_instance = Celery(
    main="worker_update_default_reports",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["src.workers.tasks"]
)

celery_instance.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

celery_instance.conf.beat_schedule = {
    "sync-reports-nightly": {
        "task": "src.workers.tasks.sync_reports_task",
        "schedule": crontab(minute=49, hour=8),
    },
}
