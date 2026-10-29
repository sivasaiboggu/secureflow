from celery import Celery
from app.config.settings import settings

celery_app = Celery(
    "secureflow",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_soft_time_limit=1740,  # 29 minutes: let the task save a failed state and retry first
    task_time_limit=1800,  # 30 minutes max per scan
    beat_schedule={
        "reap-interrupted-scans": {
            "task": "app.tasks.scan_tasks.reap_interrupted_scans",
            "schedule": 300.0,
        },
    },
)

# Autodiscover tasks in task packages
celery_app.autodiscover_tasks(["app.tasks"])
