import collections
import itertools
import logging
import pytz
import requests
import vobject

from datetime import date, time, datetime, timedelta
from rangeset import RangeSet, NEGATIVE_INFINITY, INFINITY

from six.moves import StringIO

log = logging.getLogger(__name__)


class ICal(object):
    @classmethod
    def from_fp(cls, fp):
        for calendar in vobject.readComponents(fp):
            return cls(calendar)
        else:
            log.info("nothing there...")
            return None

    def __init__(self, calendar):
        self.calendar = calendar

    def __string_prop(self, prop):
        try:
            return self.calendar.contents[prop][0].value
        except KeyError | IndexError:
            return None

    @property
    def name(self):
        return self.__string_prop('x-wr-calname')

    @property
    def colour(self):
        return self.__string_prop('x-apple-calendar-color')

    def __getitem__(self, key):
        if isinstance(key, slice):
            return self.slice(key.start, key.stop)

        return super(ICal, self).__getitem__(key)

    def slice(self, start, end):
        vtimezone = self.calendar.contents['vtimezone'][0]
        tzid = vtimezone.contents['tzid'][0]
        tz = pytz.timezone(tzid.value)

        start_midnight = tz.localize(datetime.combine(start, time.min)
                                     if start is not None else
                                     datetime.min + timedelta(days=1))
        end_midnight   = tz.localize(datetime.combine(end,   time.max)
                                     if end is not None else
                                     datetime.max - timedelta(days=1))

        # TODO: ignore all-day events (?)
        # TODO: recurring events
        vevents = []
        for vevent in self.calendar.contents['vevent']:
            try:
                if start_midnight <= vevent.dtstart.value <= end_midnight:
                    vevents.append(vevent)
            except TypeError:
                log.error("%s <= %s <= %s from %s", start_midnight, vevent.dtstart.value,
                          end_midnight, vevent, exc_info=True)
        vevents.sort(key=lambda vevent: (vevent.dtstart.value, vevent.dtend.value))
        return vevents


EMPTY_RANGE = ~RangeSet(NEGATIVE_INFINITY, INFINITY)


class Summary(collections.namedtuple('Summary', 'timeline tasks')):
    pass


def summarise(vevents):
    timeline = EMPTY_RANGE
    tasks = set()

    for ve in vevents:
        timeline |= (ve.dtstart.value, ve.dtend.value)
        tasks.update(ve.summary.value.split('; '))

    return Summary(timeline, tasks)


def summarise_daily(vevents):
    vevents = sorted(vevents, key=lambda vevent: vevent.dtstart.value)
    return collections.OrderedDict([
        (date, summarise(day_events))
        for date, day_events in itertools.groupby(
            vevents, lambda ve: ve.dtstart.value.date())
    ])


def scrape_ical(url, start, end):
    log.info('fetching %s', url)
    response = requests.get(url, timeout=5)

    log.info('parsing and slicing %s', url)
    return slice_ical(StringIO(response.text), start, end)

    # TOdO: x-wr-calname, x-apple-calendar-color, vtimezone?
    return slice_ical(calendar, start, end)
