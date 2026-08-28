import pytest
from celery import Celery
import tasks


def test_celery_app_initialization():
    """Verify Celery app is properly initialized and configured."""
    assert isinstance(tasks.celery_app, Celery)
    assert tasks.celery_app.main == "doc2sdk"
    # Verify CLI discovery aliases
    assert tasks.app is tasks.celery_app
    assert tasks.celery is tasks.celery_app


def test_celery_task_registration():
    """Verify background tasks are registered on the Celery application."""
    registered = tasks.celery_app.tasks
    assert "process_project_task" in registered
    assert callable(tasks.process_project_task)
