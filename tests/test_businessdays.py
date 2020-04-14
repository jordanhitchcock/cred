from datetime import date
from dateutil.relativedelta import relativedelta
import pytest
from pandas.tseries.holiday import USFederalHolidayCalendar, AbstractHolidayCalendar, Holiday

from cred.businessdays import is_observed_holiday, preceeding, following, \
    modified_following, unadjusted, is_month_end, Monthly


@pytest.fixture
def holiday_calendar():
    class Hol_Cal(AbstractHolidayCalendar):
        rules = [
            Holiday('hol1', month=1, day=9),
            Holiday('hol2', month=1, day=24),
            Holiday('hol3', month=1, day=20),
            Holiday('hol3', month=3, day=31),
            Holiday('hol4', month=8, day=31)
        ]

    return Hol_Cal()


@pytest.mark.parametrize(
    'dt,calendar,expected',
    [
        (date(2015, 1, 1), USFederalHolidayCalendar(), True),  # falls on weekday, observed on weekday
        (date(2015, 7, 3), USFederalHolidayCalendar(), True),  # observed for holiday that falls on weekend, observed on weekday
        (date(2015, 7, 4), USFederalHolidayCalendar(), False),  # actual for holiday that falls on weekend, observed on weekday
        (date(2011, 7, 5), USFederalHolidayCalendar(), False),  # weekday
        (date(2011, 7, 6), USFederalHolidayCalendar(), False),  # weekend
        (date(2020, 12, 31), None, False)  # calendar is None
    ]
)
def test_is_observed_holiday(dt, calendar, expected):
    assert is_observed_holiday(dt, calendar) == expected


@pytest.mark.parametrize(
    'dt,calendar,expected',
    [
        (date(2015, 1, 2), USFederalHolidayCalendar(), date(2015, 1, 2)),  # holiday
        (date(2015, 6, 27), USFederalHolidayCalendar(), date(2015, 6, 26)),  # Saturday
        (date(2015, 6, 28), USFederalHolidayCalendar(), date(2015, 6, 26)),  # Sunday
        (date(2015, 7, 5), USFederalHolidayCalendar(), date(2015, 7, 2)),  # weekend holiday
        (date(2015, 9, 7), USFederalHolidayCalendar(), date(2015, 9, 4)),  # Monday holiday
        (date(2015, 11, 11), USFederalHolidayCalendar(), date(2015, 11, 10)),  # Wednesday holiday
        (date(2015, 12, 25), USFederalHolidayCalendar(), date(2015, 12, 24))  # Friday holiday
    ]
)
def test_preceeding(dt, calendar, expected):
    assert preceeding(dt, calendar) == expected


@pytest.mark.parametrize(
    'dt,calendar,expected',
    [
        (date(2015, 1, 2), USFederalHolidayCalendar(), date(2015, 1, 2)),  # holiday
        (date(2015, 6, 27), USFederalHolidayCalendar(), date(2015, 6, 29)),  # Saturday
        (date(2015, 6, 28), USFederalHolidayCalendar(), date(2015, 6, 29)),  # Sunday
        (date(2015, 7, 5), USFederalHolidayCalendar(), date(2015, 7, 6)),  # weekend holiday
        (date(2015, 9, 7), USFederalHolidayCalendar(), date(2015, 9, 8)),  # Monday holiday
        (date(2015, 11, 11), USFederalHolidayCalendar(), date(2015, 11, 12)),  # Wednesday holiday
        (date(2015, 12, 25), USFederalHolidayCalendar(), date(2015, 12, 28))  # Friday holiday
    ]
)
def test_following(dt, calendar, expected):
    assert following(dt, calendar) == expected


@pytest.mark.parametrize(
    'pmt_date,expected',
    [
        (date(2020, 1, 8), date(2020, 1, 8)),  # good bd
        (date(2020, 1, 9), date(2020, 1, 10)),  # holiday with good bd after
        (date(2020, 1, 24), date(2020, 1, 27)),  # holiday with bad bd after
        (date(2020, 1, 4), date(2020, 1, 6)),  # saturday
        (date(2020, 1, 19), date(2020, 1, 21)),  # sunday with holiday after
        (date(2020, 1, 31), date(2020, 1, 31)),  # eom good bd
        (date(2020, 3, 31), date(2020, 3, 30)),  # eom holiday with good bd before
        (date(2020, 8, 31), date(2020, 8, 28)),  # eom holiday with weekend before
        (date(2021, 7, 31), date(2021, 7, 30)),  # eom saturday
        (date(2020, 5, 31), date(2020, 5, 29)),  # eom sunday
        (date(2024, 2, 29), date(2024, 2, 29)),  # eom feb 29 good bd
    ]
)
def test_modified_following(pmt_date, expected, holiday_calendar):
    assert modified_following(pmt_date, holiday_calendar) == expected


@pytest.mark.parametrize(
    'dt,expected',
    [
        (date(2019, 1, 1), date(2019, 1, 1)),
        (date(2020, 1, 31), date(2020, 1, 31)),
        (date(2020, 2, 29), date(2020, 2, 29))
    ]
)
def test_unadjusted(dt, expected):
    assert unadjusted(dt) == expected
    assert unadjusted(dt, calendar=9) == expected


@pytest.mark.parametrize(
    'dt,expected',
    [
        (date(2020, 1, 1), False),
        (date(2020, 1, 15), False),
        (date(2020, 1, 31), True),
        (date(2020, 2, 28), False),
        (date(2019, 2, 28), True),
        (date(2020, 2, 29), True)
    ]
)
def test_is_month_end(dt, expected):
    assert is_month_end(dt) == expected


@pytest.mark.parametrize(
    'months,dt,expected',
    [
        (0, date(2020, 1, 1), date(2020, 1, 1)),
        (1, date(2020, 1, 1), date(2020, 2, 1)),
        (2, date(2020, 1, 1), date(2020, 3, 1)),
        (-1, date(2020, 1, 1), date(2019, 12, 1)),
        (-1, date(2020, 1, 30), date(2019, 12, 30)),
        (-2, date(2020, 2, 29), date(2019, 12, 31)),
        (1, date(2020, 1, 30), date(2020, 2, 29)),
        (5, date(2020, 1, 30), date(2020, 6, 30)),
        (1, date(2020, 1, 31), date(2020, 2, 29)),
        (2, date(2020, 1, 31), date(2020, 3, 31)),
        (5, date(2020, 1, 31), date(2020, 6, 30)),
        (1, date(2020, 2, 28), date(2020, 3, 28)),
        (4, date(2020, 2, 28), date(2020, 6, 28)),
        (1, date(2020, 2, 29), date(2020, 3, 31)),
        (4, date(2020, 2, 29), date(2020, 6, 30)),
        (1, date(2020, 6, 30), date(2020, 7, 31))
    ]
)
def test_monthly_add(months, dt, expected):
    m = Monthly(months)
    assert (m + dt) == expected
    assert (dt + m) == expected


@pytest.mark.parametrize(
    'months,multiplier,dt,expected',
    [
        (1, 0, date(2020, 1, 1), date(2020, 1, 1)),
        (1, 3, date(2020, 1, 30), date(2020, 4, 30)),
        (1, 5, date(2020, 1, 31), date(2020, 6, 30)),
        (1, 13, date(2020, 1, 1), date(2021, 2, 1)),
        (1, -4, date(2020, 1, 30), date(2019, 9, 30)),
        (1, -4, date(2020, 2, 29), date(2019, 10, 31)),
        (1, -4, date(2020, 1, 31), date(2019, 9, 30)),
        (1, -4, date(2020, 1, 1), date(2019, 9, 1)),
        (23, 2, date(2020, 1, 1), date(2023, 11, 1)),
    ]
)
def test_monthly_multiply(months, multiplier, dt, expected):
    m = Monthly(months)
    assert (m * multiplier + dt) == expected
    assert (multiplier * m + dt) == expected


def test_monthly_repr():
    assert Monthly().__repr__() == 'Months: 1'
    assert Monthly(4).__repr__() == 'Months: 4'
