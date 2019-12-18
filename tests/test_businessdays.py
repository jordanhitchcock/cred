import pytest

from datetime import datetime
from pandas.tseries.holiday import USFederalHolidayCalendar

from cred.businessdays import is_observed_holiday, previous_business_day, following_business_day, modified_following


@pytest.mark.parametrize(
    'date,calendar,expected',
    [
        (datetime(2015, 1, 1), USFederalHolidayCalendar, True),  # falls on weekday, observed on weekday
        (datetime(2015, 7, 3), USFederalHolidayCalendar, True),  # observed for holiday that falls on weekend, observed on weekday
        (datetime(2015, 7, 4), USFederalHolidayCalendar, False),  # actual for holiday that falls on weekend, observed on weekday
        (datetime(2011, 7, 5), USFederalHolidayCalendar, False),  # weekday
        (datetime(2011, 7, 6), USFederalHolidayCalendar, False)  # weekend
    ]
)
def test_is_observed_holiday(date, calendar, expected):
    assert is_observed_holiday(date, calendar) == expected


@pytest.mark.parametrize(
    'date,calendar,expected',
    [
        (datetime(2015, 1, 2), USFederalHolidayCalendar, datetime(2015, 1, 2)),  # holiday
        (datetime(2015, 6, 27), USFederalHolidayCalendar, datetime(2015, 6, 26)),  # Saturday
        (datetime(2015, 6, 28), USFederalHolidayCalendar, datetime(2015, 6, 26)),  # Sunday
        (datetime(2015, 7, 5), USFederalHolidayCalendar, datetime(2015, 7, 2)),  # weekend holiday
        (datetime(2015, 9, 7), USFederalHolidayCalendar, datetime(2015, 9, 4)),  # Monday holiday
        (datetime(2015, 11, 11), USFederalHolidayCalendar, datetime(2015, 11, 10)),  # Wednesday holiday
        (datetime(2015, 12, 25), USFederalHolidayCalendar, datetime(2015, 12, 24))  # Friday holiday
    ]
)
def test_previous_business_day(date, calendar, expected):
    assert previous_business_day(date, calendar) == expected


@pytest.mark.parametrize(
    'date,calendar,expected',
    [
        (datetime(2015, 1, 2), USFederalHolidayCalendar, datetime(2015, 1, 2)),  # holiday
        (datetime(2015, 6, 27), USFederalHolidayCalendar, datetime(2015, 6, 29)),  # Saturday
        (datetime(2015, 6, 28), USFederalHolidayCalendar, datetime(2015, 6, 29)),  # Sunday
        (datetime(2015, 7, 5), USFederalHolidayCalendar, datetime(2015, 7, 6)),  # weekend holiday
        (datetime(2015, 9, 7), USFederalHolidayCalendar, datetime(2015, 9, 8)),  # Monday holiday
        (datetime(2015, 11, 11), USFederalHolidayCalendar, datetime(2015, 11, 12)),  # Wednesday holiday
        (datetime(2015, 12, 25), USFederalHolidayCalendar, datetime(2015, 12, 28))  # Friday holiday
    ]
)
def test_following_business_day(date, calendar, expected):
    assert following_business_day(date, calendar) == expected


@pytest.mark.parametrize(
    'date,calendar,expected',
    [
        (datetime(2015, 1, 17), USFederalHolidayCalendar, datetime(2015, 1, 20)),  # weekend in middle of month
        (datetime(2015, 1, 31), USFederalHolidayCalendar, datetime(2015, 1, 30)),  # last day of month is weekend
        (datetime(2015, 3, 31), USFederalHolidayCalendar, datetime(2015, 3, 31))  # last day of month is weekday

    ]
)
def test_modified_following(date, calendar, expected):
    assert modified_following(date, calendar) == expected
