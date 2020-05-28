from cred.businessdays import is_month_end


def periods_in_year(offset):
    """
    Returns the number of periods in a year based on `years`, `months`, and `days` in the offset. Raises a ValueError if
    the offset object does not have years, months, or days properties with values other than 0.

    Calculated as: 1 / (years + 12 / months + 365 / days)

    Examples
    --------
    >>> periods_in_year(Monthly(3))
    4
    >>> periods_in_year(relativedelta(months=1, days=1))
    11.618037135278515
    """
    days = offset.__dict__.get('days', 0)
    months = offset.__dict__.get('months', 0)
    years = offset.__dict__.get('years', 0)

    periods = 0
    try:
        periods += days / 365
    except ZeroDivisionError:
        pass
    try:
        periods += months / 12
    except ZeroDivisionError:
        pass
    try:
        periods += years
    except ZeroDivisionError:
        pass

    if periods == 0:
        raise ValueError('Offset does not have years, months, or days properties with values different than 0.')

    return 1 / periods


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

