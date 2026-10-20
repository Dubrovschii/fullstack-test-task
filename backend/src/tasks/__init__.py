"""Celery entry point: ``celery -A src.tasks.celery_app worker`` (unchanged).

``celery_app`` must be an attribute of this package (not a submodule) because
that is how the existing ``-A src.tasks.celery_app`` command resolves it.
Importing ``processing`` registers the tasks on the app.
"""

from src.core.celery_app import celery_app
from src.tasks import processing  # noqa: F401  (registers tasks)

__all__ = ["celery_app"]
