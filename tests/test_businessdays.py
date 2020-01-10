from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytest
from pandas.tseries.holiday import USFederalHolidayCalendar

from cred.businessdays import is_observed_holiday, previous_business_day, following_business_day, \
    modified_following, unadjusted_schedule



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
    'start,end,frequency,expected',
    [
        (datetime(2019, 1, 1), datetime(2020, 3, 1), relativedelta(months=1),
         [
             (datetime(2019, 1, 1), datetime(2019, 2, 1)),
             (datetime(2019, 2, 1), datetime(2019, 3, 1)),
             (datetime(2019, 3, 1), datetime(2019, 4, 1)),
             (datetime(2019, 4, 1), datetime(2019, 5, 1)),
             (datetime(2019, 5, 1), datetime(2019, 6, 1)),
             (datetime(2019, 6, 1), datetime(2019, 7, 1)),
             (datetime(2019, 7, 1), datetime(2019, 8, 1)),
             (datetime(2019, 8, 1), datetime(2019, 9, 1)),
             (datetime(2019, 9, 1), datetime(2019, 10, 1)),
             (datetime(2019, 10, 1), datetime(2019, 11, 1)),
             (datetime(2019, 11, 1), datetime(2019, 12, 1)),
             (datetime(2019, 12, 1), datetime(2020, 1, 1)),
             (datetime(2020, 1, 1), datetime(2020, 2, 1)),
             (datetime(2020, 2, 1), datetime(2020, 3, 1))
         ]),
        (datetime(2019, 1, 1), datetime(2020, 4, 1), relativedelta(months=3),
         [
             (datetime(2019, 1, 1), datetime(2019, 4, 1)),
             (datetime(2019, 4, 1), datetime(2019, 7, 1)),
             (datetime(2019, 7, 1), datetime(2019, 10, 1)),
             (datetime(2019, 10, 1), datetime(2020, 1, 1)),
             (datetime(2020, 1, 1), datetime(2020, 4, 1))
         ]),
        (datetime(2019, 1, 1), datetime(2021, 7, 1), relativedelta(months=6),
         [
             (datetime(2019, 1, 1), datetime(2019, 7, 1)),
             (datetime(2019, 7, 1), datetime(2020, 1, 1)),
             (datetime(2020, 1, 1), datetime(2020, 7, 1)),
             (datetime(2020, 7, 1), datetime(2021, 1, 1)),
             (datetime(2021, 1, 1), datetime(2021, 7, 1))
         ])
    ]
)
def test_unadjusted_schedule(start, end, frequency, expected):
    assert unadjusted_schedule(start, end, frequency) == expected


