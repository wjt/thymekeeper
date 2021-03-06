# vim: fileencoding=utf-8
import collections
import itertools
import logging
import operator
import pytz
import requests
import vobject

from datetime import date, time, datetime, timedelta
from rangeset import RangeSet

from six.moves import StringIO

log = logging.getLogger(__name__)

# ± 1 day to work around a pytz bug…
BIG_BANG = pytz.UTC.localize(datetime.min + timedelta(days=1))
HEAT_DEATH_OF_UNIVERSE = pytz.UTC.localize(datetime.max - timedelta(days=1))

# A bit ugly if printed, but forces the type of measure() to be a timedelta
EMPTY_RANGE = RangeSet(BIG_BANG, BIG_BANG)


class ICal(object):
    @classmethod
    def from_string(cls, string):
        return cls.load(StringIO(string))

    @classmethod
    def load(cls, fp):
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
        # TODO: wrong, use dateutil's support for this
        vtimezone = self.calendar.contents['vtimezone'][0]
        tzid = vtimezone.contents['tzid'][0]
        tz = pytz.timezone(tzid.value)

        start_midnight = tz.localize(datetime.combine(start, time.min)) if start is not None else BIG_BANG
        end_midnight   = tz.localize(datetime.combine(end,   time.max)) if end   is not None else HEAT_DEATH_OF_UNIVERSE

        # TODO: ignore all-day events (?)
        # TODO: only count OPAQUE (ie busy) events, not TRANSPARENT (ie ignore for free/busy
        # purposes)?
        # TODO: recurring events
        vevents = []
        for vevent in self.calendar.contents['vevent']:
            start = vevent.dtstart.value

            # Skip all-day events
            if not isinstance(start, datetime):
                if not isinstance(start, date):
                    log.warning("DTSTART neither datetime nor date: %s", vevent)

                continue

            try:
                if start_midnight <= start <= end_midnight:
                    vevents.append(vevent)
            except TypeError:
                log.error("%s <= %s <= %s from %s",
                          start_midnight, start, end_midnight, vevent,
                          exc_info=True)

        vevents.sort(key=lambda vevent: (vevent.dtstart.value, vevent.dtend.value))
        return vevents


class Summary(collections.namedtuple('Summary', 'timeline tasks')):
    def __or__(self, that):
        return Summary(self.timeline | that.timeline,
                       self.tasks | that.tasks)

    @staticmethod
    def union(summaries):
        return reduce(operator.or_, summaries, Summary(EMPTY_RANGE, set()))


class DailySummary(collections.namedtuple('DailySummary', 'days total')):
    def __new__(cls, days):
        total = Summary.union(days.itervalues())

        return super(DailySummary, cls).__new__(cls, days, total)


def summarise(vevents):
    timeline = EMPTY_RANGE
    tasks = set()

    for ve in vevents:
        timeline |= (ve.dtstart.value, ve.dtend.value)
        if hasattr(ve, 'summary'):
            tasks.update(ve.summary.value.split('; '))
        else:
            tasks.add('unknown')

    return Summary(timeline, tasks)


def summarise_daily(vevents):
    vevents = sorted(vevents, key=lambda vevent: vevent.dtstart.value)
    return DailySummary(collections.OrderedDict([
        (date, summarise(day_events))
        for date, day_events in itertools.groupby(
            vevents, lambda ve: ve.dtstart.value.date())
    ]))
