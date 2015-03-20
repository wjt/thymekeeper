#!/usr/bin/env python
# encoding: utf-8
from __future__ import division, print_function

import argh
from datetime import date, datetime, timedelta
import caldav
from caldav.elements import dav, cdav
import collections
import ConfigParser
import subprocess
import logging
import itertools

from rangeset import RangeSet, NEGATIVE_INFINITY, INFINITY

log = logging.getLogger(__name__)


def scrape(account, between=(None, None)):
    client = caldav.DAVClient(account.url, username=account.username,
                              password=account.get_password())
    principal = client.principal()
    calendars = principal.calendars()
    if len(calendars) > 0:
        calendar = calendars[0]
        log.info("Using calendar %s", calendar)

        start, end = between
        if start is not None:
            log.info("Searching for events in [%s, %s]", start, end)
            return calendar.date_search(start, end)
        else:
            log.info("Fetching all events")
            events = calendar.events()
            for event in events[:]:
                try:
                    event.load()
                except StopIteration:
                    # TODO: fix this in the library, it is s-t-u-p-i-d
                    log.warning("event.load() raised StopIteration on %s, ", event, exc_info=True)
                    events.remove(event)

            return events
    else:
        log.info("No calendars")
        return []


def format_duration(duration):
    total_seconds = duration.total_seconds()
    total_minutes = total_seconds / 60.
    minutes = int(total_minutes) % 60

    total_hours = total_minutes / 60.
    hours = int(total_hours)

    return '{:2}h {:02}m'.format(hours, minutes)


def format_days(duration, hours_per_day=8):
    total_seconds = duration.total_seconds()
    total_minutes = total_seconds / 60.
    total_hours   = total_minutes / 60.

    days = total_hours / hours_per_day

    return '{:.2f}'.format(days)


EMPTY_RANGE = ~RangeSet(NEGATIVE_INFINITY, INFINITY)


def summarise(events):
    print('\n')
    timeline = EMPTY_RANGE

    # TODO: mangle recurring events
    # TODO: don't count all-day events at all
    events = sorted(events, key=lambda e: e.instance.vevent.dtstart.value)
    for date, day_events in itertools.groupby(events, lambda e: e.instance.vevent.dtstart.value.date()):
        print(u"{}:".format(date))

        day_timeline = EMPTY_RANGE
        tasks = []

        for event in day_events:
            ve = event.instance.vevent
            # ve.prettyPrint()
            day_timeline |= (ve.dtstart.value, ve.dtend.value)
            tasks += ve.summary.value.split('; ')

        print(u"   {}: {}".format(
            format_duration(day_timeline.measure()),
            u'\n          : '.join(tasks)))

        timeline |= day_timeline

    print('\n')
    print('{} days'.format(format_days(timeline.measure())))


Account = collections.namedtuple('Account', 'url username get_password')


def load_accounts(filename):
    config = ConfigParser.SafeConfigParser()
    config.read(filename)

    accounts = {}
    for section in config.sections():
        url          = config.get(section, 'url')
        username     = config.get(section, 'username')
        password_cmd = config.get(section, 'password-command')

        def get_password():
            return subprocess.check_output(password_cmd, shell=True)

        accounts[section] = Account(url, username, get_password)

    return accounts


def isodate(s):
    return datetime.strptime(s, '%Y-%m-%d').date()


@argh.arg('--config', metavar="FILENAME")
@argh.arg('--account')
@argh.arg('--start', metavar="YYYY-MM-DD", type=isodate, help='(inclusive)')
@argh.arg('--end',   metavar="YYYY-MM-DD", type=isodate, help='(exclusive)')
@argh.arg('--debug')
def main(config='thymekeeper.ini', account=None, start=None, end=None, debug=False):
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)

    accounts = load_accounts(config)
    if account:
        account_ = accounts[account]
    elif len(accounts) == 1:
        for account_ in accounts.itervalues():
            break
    else:
        raise ValueError("which do you want? " + accounts.keys())

    try:
        events = scrape(account_, between=(start, end - timedelta(days=1)))
    except Exception:
        log.error("wtf", exc_info=True)
        raise
    summarise(events)


if __name__ == '__main__':
    argh.dispatch_command(main)
