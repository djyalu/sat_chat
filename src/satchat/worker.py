"""Celery worker configuration"""

import logging
from celery import Celery
from celery.schedules import crontab

from satchat.core.config import settings

logger = logging.getLogger(__name__)

# Create Celery app
app = Celery(
    'satchat',
    broker=settings.redis_url_str,
    backend=settings.redis_url_str,
    include=[
        'satchat.tasks.satellite',
        'satchat.tasks.processing',
        'satchat.tasks.monitoring'
    ]
)

# Celery configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.task_timeout,
    task_soft_time_limit=settings.task_timeout - 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
)

# Celery beat schedule for periodic tasks
app.conf.beat_schedule = {
    'collect-satellite-data-morning': {
        'task': 'satchat.tasks.satellite.collect_all_areas',
        'schedule': crontab(hour=6, minute=0),  # 6 AM KST
        'args': (),
        'kwargs': {'days_back': 1, 'max_cloud': 20}
    },
    'collect-satellite-data-evening': {
        'task': 'satchat.tasks.satellite.collect_all_areas',
        'schedule': crontab(hour=18, minute=0),  # 6 PM KST
        'args': (),
        'kwargs': {'days_back': 1, 'max_cloud': 20}
    },
    'process-pending-images': {
        'task': 'satchat.tasks.processing.process_pending_images',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
    'generate-daily-reports': {
        'task': 'satchat.tasks.monitoring.generate_daily_reports',
        'schedule': crontab(hour=9, minute=0),  # 9 AM KST
    },
    'cleanup-old-data': {
        'task': 'satchat.tasks.maintenance.cleanup_old_data',
        'schedule': crontab(hour=2, minute=0),  # 2 AM KST
        'kwargs': {'days_old': 30}
    },
}

if __name__ == '__main__':
    app.start()