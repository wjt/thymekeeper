#!/usr/bin/env python
# encoding: utf-8
from __future__ import division, print_function

import argh
from datetime import datetime
import ConfigParser
import logging
import requests

from thymekeeper.ical import ICal, summarise_daily
from six.moves import StringIO

log = logging.getLogger(__name__)


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

def load_accounts(filename):
    config = ConfigParser.SafeConfigParser()
    config.read(filename)

    return {
        section: config.get(section, 'url')
        for section in config.sections()
    }


def isodate(s):
    return datetime.strptime(s, '%Y-%m-%d').date()


@argh.arg('--config', metavar="FILENAME")
@argh.arg('--account')
@argh.arg('--start', metavar="YYYY-MM-DD", type=isodate, help='(inclusive)')
@argh.arg('--end',   metavar="YYYY-MM-DD", type=isodate, help='(inclusive)')
@argh.arg('--debug')
def main(config='thymekeeper.ini', account=None, start=None, end=None, debug=False):
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)

    accounts = load_accounts(config)
    if account:
        url = accounts[account]
    elif len(accounts) == 1:
        for url in accounts.itervalues():
            break
    else:
        raise ValueError("which do you want? " + ' or '.join(accounts.keys()))

    log.info('fetching %s', url)
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    cal = ICal.from_fp(StringIO(response.text))
    daily = summarise_daily(cal[start:end])

    for date, summary in daily.days.iteritems():
        print(u"{}: {}".format(date, format_duration(summary.timeline.measure())))
        for task in summary.tasks:
            print(u'          : {}'.format(task))

    print('\n')
    print('{} days'.format(format_days(daily.total.timeline.measure())))


if __name__ == '__main__':
    argh.dispatch_command(main)
