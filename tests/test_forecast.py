"""Series accessors, tested directly against a synthetic grid."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from custom_components.pvnode.forecast import energy_between, peak, value_at

UTC = timezone.utc


def _series(*, start: datetime, count: int, power) -> dict[datetime, dict]:
    """A 15-minute grid of `count` rows starting at `start`, one `pv_power` per slot."""
    return {
        start + timedelta(minutes=15 * i): {"pv_power": power(i)}
        for i in range(count)
    }


def test_value_at_uses_the_slot_ending_at_or_after_the_query_point() -> None:
    """A row's timestamp is the end of the period its value describes."""
    series = _series(start=datetime(2026, 1, 1, 7, 0, tzinfo=UTC), count=3, power=lambda i: i)

    assert value_at(series, "pv_power", datetime(2026, 1, 1, 6, 50, tzinfo=UTC)) == 0
    assert value_at(series, "pv_power", datetime(2026, 1, 1, 7, 0, tzinfo=UTC)) == 0
    assert value_at(series, "pv_power", datetime(2026, 1, 1, 7, 1, tzinfo=UTC)) == 1
    assert value_at(series, "pv_power", datetime(2026, 1, 1, 7, 30, tzinfo=UTC)) == 2


def test_energy_between_attributes_a_slot_to_the_period_it_closes() -> None:
    """A day's 96 slots are the ones ending after midnight, up to and including the next."""
    midnight = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    series = _series(start=midnight + timedelta(minutes=15), count=96, power=lambda i: 4)

    day1 = energy_between(series, midnight, midnight + timedelta(days=1))
    day2 = energy_between(
        series, midnight + timedelta(days=1), midnight + timedelta(days=2)
    )

    assert day1 == 96 * 4 * 0.25  # 96 slots, 4 W each, 15 min -> 96 Wh
    assert day2 is None  # nothing beyond the first day in this series


def test_peak_reports_the_end_of_the_winning_slot() -> None:
    """Same (start, end] windowing as energy_between, not the slot's start."""
    midnight = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    series = _series(start=midnight + timedelta(minutes=15), count=96, power=lambda i: i)

    when, value = peak(series, midnight, midnight + timedelta(days=1))

    assert value == 95
    assert when == midnight + timedelta(days=1)
