#!/usr/bin/env python
# encoding: utf-8

import argh
from datetime import date, datetime, timedelta
import caldav
from caldav.elements import dav, cdav
import collections
import ConfigParser
import subprocess
import logging

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


def summarise(events):
    total_duration = timedelta()

    log.info(events)
    for event in events: #sorted(events, key=lambda e: e.instance.vevent.dtstart.value):
        ve = event.instance.vevent
        # ve.prettyPrint()
        duration = ve.dtend.value - ve.dtstart.value
        hours = duration.total_seconds() / (60. * 60.)
        print("{} {:4.2}: {}".format(
            ve.dtstart.value, hours, ve.summary.value))

        total_duration += duration

    print total_duration.total_seconds() / (60. * 60. * 8.)


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
@argh.arg('--start', metavar="YYYY-MM-DD", type=isodate)
@argh.arg('--end',   metavar="YYYY-MM-DD", type=isodate)
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
        events = scrape(account_, between=(start, end))
    except Exception:
        log.error("wtf", exc_info=True)
        raise
    summarise(events)


if __name__ == '__main__':
    argh.dispatch_command(main)
