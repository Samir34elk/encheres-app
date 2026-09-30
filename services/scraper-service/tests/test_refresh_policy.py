from datetime import datetime, timedelta

from app.scheduler.refresh_policy import decide_lots_refresh

NOW = datetime(2026, 10, 1, 12, 0)


def decide(status, end_in=None, scraped_ago=None):
    end_date = NOW + end_in if end_in is not None else None
    last = NOW - scraped_ago if scraped_ago is not None else None
    return decide_lots_refresh(status, end_date, last, NOW)


def test_never_scraped_is_due():
    assert decide("active", timedelta(days=3)).due


def test_closed_and_finalized_is_never_rescraped():
    d = decide("closed", end_in=-timedelta(days=30), scraped_ago=timedelta(days=29))
    assert not d.due


def test_closed_gets_one_final_scrape():
    d = decide("closed", end_in=-timedelta(hours=2), scraped_ago=timedelta(hours=3))
    assert d.due


def test_end_date_passed_waits_grace_period():
    d = decide("active", end_in=-timedelta(minutes=5), scraped_ago=timedelta(minutes=20))
    assert not d.due


def test_ending_soon_refreshes_every_15_minutes():
    assert decide("active", timedelta(hours=1), timedelta(minutes=16)).due
    assert not decide("active", timedelta(hours=1), timedelta(minutes=5)).due


def test_ending_today_refreshes_hourly():
    assert not decide("active", timedelta(hours=10), timedelta(minutes=30)).due
    assert decide("active", timedelta(hours=10), timedelta(minutes=61)).due


def test_active_long_sale_refreshes_every_6_hours():
    assert not decide("active", timedelta(days=5), timedelta(hours=2)).due
    assert decide("active", timedelta(days=5), timedelta(hours=6)).due


def test_upcoming_refreshes_every_12_hours():
    assert not decide("upcoming", timedelta(days=10), timedelta(hours=6)).due
    assert decide("upcoming", timedelta(days=10), timedelta(hours=12)).due


def test_ending_soon_has_highest_priority():
    soon = decide("active", timedelta(hours=1), timedelta(hours=1))
    later = decide("active", timedelta(days=5), timedelta(days=1))
    assert soon.priority < later.priority
