import operator
import pytest

from datetime import date
from thymekeeper.ical import ICal, summarise, summarise_daily


@pytest.fixture
def cal():
    with open('tests/test-calendar.ics', 'rb') as f:
        return ICal.from_fp(f)


def test_props(cal):
    assert cal.name == 'Test'
    assert cal.colour == '#EF5411'


def test_slice(cal):
    vevents = cal[date(1900, 1, 1):date(2020, 1, 1)]
    assert len(vevents) == 2

    vevents = cal[date(2015, 3, 9):date(2015, 3, 9)]
    assert len(vevents) == 1


def test_summarise(cal):
    vevents = cal[:]

    overall = summarise(vevents)
    assert overall.tasks == {'A meeting', 'A task for most of a day'}

    daily = summarise_daily(vevents)
    assert len(daily) == 2
    assert len(daily[date(2015, 3,  9)].tasks) == 1
    assert len(daily[date(2015, 3, 24)].tasks) == 1

    assert reduce(operator.or_, (s.timeline for s in daily.values())) == overall.timeline
    # TODO: timeline tests, eg overlap
