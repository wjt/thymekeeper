import requests
from celery.utils.log import get_task_logger

from thymekeeper import app, db, Calendar, celery

logger = get_task_logger(__name__)


@celery.task
def update_cached_calendar(calendar_id):
    cal = Calendar.query.get_or_404(calendar_id)

    logger.debug('fetching %s', cal.url)
    response = requests.get(cal.url, timeout=60)
    response.raise_for_status()

    logger.debug('caching response for %s', cal.url)
    cal.cached = response.text
    db.session.add(cal)
    db.session.commit()
