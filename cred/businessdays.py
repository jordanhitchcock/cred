from pandas.tseries.holiday import *


class FederalReserveHolidays(AbstractHolidayCalendar):

    rules = [
        Holiday("New Years Day", month=1, day=1, observance=sunday_to_monday),
        USMartinLutherKingJr,
        USPresidentsDay,
        Holiday("Memorial Day", start_date=datetime(1970, 1, 1), month=5, day=31, offset=DateOffset(weekday=MO(-1))),
        Holiday("July 4th", month=7, day=4, observance=sunday_to_monday),
        USLaborDay,
        Holiday("Columbus Day", start_date=datetime(1971, 1, 1), month=10, day=1, offset=DateOffset(weekday=MO(2))),
        Holiday("Veterans Day", month=11, day=11, observance=sunday_to_monday),
        USThanksgivingDay,
        Holiday("Christmas", month=12, day=25, observance=sunday_to_monday)
    ]


class LondonBankHolidays(AbstractHolidayCalendar):

    rules = [
        Holiday('New Years Day', month=1, day=1, observance=next_workday),  # Since 1971?
        Holiday('Good Friday', month=1, day=1, offset=[Easter(), Day(-2)]),
        EasterMonday,
        Holiday('Early May Holiday', start_date=datetime(1978, 1, 1), month=5, day=1, offset=DateOffset(weekday=MO(1))),
        Holiday('Spring Holiday', start_date=datetime(1971, 1, 1), month=5, day=31, offset=DateOffset(weekday=MO(-1))),
        Holiday('Summer Holiday', start_date=datetime(1971, 1, 1), month=8, day=31, offset=DateOffset(weekday=MO(-1))),
        Holiday("Christmas", month=12, day=25, observance=next_monday),
        Holiday('Boxing Day', month=12, day=26, observance=next_monday_or_tuesday)
    ]


def is_observed_holiday(dt, calendar):
    """ Return True if dt is a holiday in calendar."""
    return dt in calendar.holidays(start=dt, end=dt, return_name=False)


def previous_business_day(dt, calendar):
    """
    Return the previous business day if dt is on a weekend or holiday in calendar.
    """
    while dt.weekday() > 4 or is_observed_holiday(dt, calendar):
        dt -= timedelta(days=1)
    return dt


def following_business_day(dt, calendar):
    """
    Return the next business day if dt is on a weekend or holiday in calendars.
    """
    while dt.weekday() > 4 or is_observed_holiday(dt, calendar):
        dt += timedelta(days=1)
    return dt


def modified_following(dt, calendar):
    """
    Return the next business day if dt is on a weekend or holiday in calendars unless the next business
    day is in the following month, in which case returns the previous business day.
    """
    following_bd = following_business_day(dt, calendar)

    if following_bd.month == dt.month:
        return following_bd
    else:
        return previous_business_day(dt, calendar)


def unadjusted_schedule(start_date, end_date, frequency):
    periods = []

    i = 1
    bop = start_date
    eop = min(end_date, start_date + frequency)
    periods.append((bop, eop))

    while eop < end_date:
        i += 1
        bop = eop
        eop = min(end_date, start_date + frequency * i)
        periods.append((bop, eop))

    return periods


