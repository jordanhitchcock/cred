import calendar as cal
from dateutil.relativedelta import relativedelta
from pandas.tseries.holiday import *


class FederalReserveHolidays(AbstractHolidayCalendar):
    """
    U.S. Federal Reserve banking holidays. Holidays are thought to be accurate, but you should verify independently.
    """

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
    """
    London banking holidays. Holidays are thought to be accurate, but you should verify independently.
    """

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
    """ Return True if dt is a holiday in calendar. Return `False` if `calendar` is `None`."""
    if calendar is None:
        return False
    return dt in calendar.holidays(start=dt, end=dt, return_name=False)


def is_month_end(dt):
    """Returns True if `dt` is the last day of the month."""
    return dt.day == cal.monthrange(dt.year, dt.month)[1]


def preceeding(dt, calendar):
    """
    Return the previous business day if `dt` is on a weekend or holiday in `calendar`.
    """
    while dt.weekday() > 4 or is_observed_holiday(dt, calendar):
        dt -= timedelta(days=1)
    return dt


def following(dt, calendar):
    """
    Return the next business day if `dt` is on a weekend or holiday in `calendar`.
    """
    while dt.weekday() > 4 or is_observed_holiday(dt, calendar):
        dt += timedelta(days=1)
    return dt


def modified_following(dt, calendar):
    """
    Return the next business day if `dt` is on a weekend or holiday in `calendar` unless the next business
    day is in the following calendar month, in which case returns the previous business day.
    """
    following_bd = following(dt, calendar)

    if following_bd.month == dt.month:
        return following_bd
    else:
        return preceeding(dt, calendar)


def unadjusted(dt, calendar=None):
    """Return unadjusted date. `calendar` parameter does not affect return value, provides consistency with
    other convention functions."""
    return dt


class Monthly:
    """
    Monthly date offset that recognizes whether it is added to the last day of the month. If so, returns the last day of
    the corresponding month. Convenience offset for interest periods that may roll on the last day of the month.

    Example: adding `Monthly()` to `date(2020, 6, 30)` returns `date(2020, 7, 31)`. The default
    object is a one month offset.

    Parameters
    ----------
    months: int
        Offset in months.
    """

    def __init__(self, months=1):
        self.months = months

    def __repr__(self):
        return f'Months: {self.months}'

    def __add__(self, other):
        if is_month_end(other):
            return other + relativedelta(months=self.months + 1, day=1, days=-1)
        return other + relativedelta(months=self.months)

    def __radd__(self, other):
        return self.__add__(other)

    def __mul__(self, other):
        return self.__class__(months=self.months * other)

    def __rmul__(self, other):
        return self.__mul__(other)
