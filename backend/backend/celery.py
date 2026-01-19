import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = Celery('payouts')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.update(
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    broker_connection_retry_on_startup=True,
    result_backend='redis://localhost:6379/0',
    broker_url='redis://localhost:6379/0',
    accept_content=['json'],
    result_serializer='json',
    task_serializer ='json',
    timezone='Europe/Moscow',
    task_default_queue='celery',
    task_time_limit=30 * 60,
    worker_concurrency=4,
    task_track_started=True,
)

app.autodiscover_tasks()
