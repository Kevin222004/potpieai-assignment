from app.tasks.celery_app import celery_app
from app.tasks.review import analyze_pr_task

__all__ = ['celery_app', 'analyze_pr_task']