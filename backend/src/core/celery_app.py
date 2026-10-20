"""The Celery application.  Tasks live in ``src.tasks``."""

from celery import Celery

from src.core.config import get_settings

# No result backend and ``task_ignore_result``: nothing ever reads task results,
# so storing one in Redis for every task was pure overhead.
celery_app = Celery("file_tasks", broker=get_settings().redis_url)
celery_app.conf.update(
    task_ignore_result=True,
    broker_connection_retry_on_startup=True,
)
