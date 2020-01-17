from dateutil.relativedelta import relativedelta


# TODO: One month offset end of month
# Absolute is applied before relative
eom_offset = relativedelta(months=1, day=1, days=-1)


def is_month_end(dt):
    return dt == dt + eom_offset


def actual360(dt1, dt2):
    days = (dt2 - dt1).days
    return days / 360


def thirty360(dt1, dt2):
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
