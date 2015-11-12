import requests
from celery.utils.log import get_task_logger

from thymekeeper import app, db, Calendar, celery

logger = get_task_logger(__name__)


def completed(task):
    return task.successful() or task.failed()


@celery.task
def update_cached_calendar(calendar_id):
    cal = Calendar.query.get_or_404(calendar_id)

    logger.debug('fetching %s', cal.url)
    response = requests.get(cal.url, timeout=60)
    response.raise_for_status()

    logger.debug('caching response for %s', cal.url)
    cal.cached = response.text
    cal.task_id = None
    db.session.add(cal)
    db.session.commit()


def is_updating(calendar):
    if calendar.task_id is not None:
        task = update_cached_calendar.AsyncResult(calendar.task_id)
        if not completed(task):
            return True

    return False

Calendar.is_updating = is_updating

def ensure_update_cached_calendar(calendar):
    if is_updating(calendar):
        return

    task = update_cached_calendar.delay(calendar.id)
    calendar.task_id = task.id
    db.session.add(calendar)
    db.session.commit()
