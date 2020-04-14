from cred.businessdays import is_month_end


def actual360(dt1, dt2):
    """Returns the fraction of a year between `dt1` and `dt2` on an actual / 360 day count basis."""

    days = (dt2 - dt1).days
    return days / 360


def thirty360(dt1, dt2):
    """Returns the fraction of a year between `dt1` and `dt2` on 30 / 360 day count basis."""

    y1, m1, d1 = dt1.year, dt1.month, dt1.day
    y2, m2, d2 = dt2.year, dt2.month, dt2.day

    if is_month_end(dt1) and (dt1.month == 2) and is_month_end(dt2) and (dt2.month == 2):
        d2 = 30
    if is_month_end(dt1) and (dt1.month == 2):
        d1 = 30
    if (d2 == 31) and ((d1 == 30) or (d1 == 31)):
        d2 = 30
    if d1 == 31:
        d1 = 30

    days = 360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)

    return days / 360


# def decompounded_periodic_rate(rate, freq):
#     """
#     Return decompounded periodic rate with the number of periods based on freq.
#
#     Parameters
#     ----------
#     rate: float
#         Annual rate
#     freq: dateutil.relativedelta.relativedelta
#         dateutil.relativedelta representing a period. Years equals 1 period, months equal 12, days equal 365.
#
#     Returns
#     -------
#     float
#     """
#     yearfrac = freq.years + (freq.months / 12) + (freq.days / 365)
#     return (1 + rate) ** yearfrac - 1
#
#
# def simple_periodic_rate(rate, freq):
#     """
#     Return simpled periodic rate with the number of periods based on freq.
#
#     Parameters
#     ----------
#     rate: float
#         Annual rate
#     freq: dateutil.relativedelta.relativedelta
#         dateutil.relativedelta representing a period. Years equals 1 period, months equal 12, days equal 365.
#
#     Returns
#     -------
#     float
#     """
#     yearfrac = freq.years + (freq.months / 12) + (freq.days / 365)
#     return rate * yearfrac


