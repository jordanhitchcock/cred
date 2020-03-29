from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytest

from cred.interest_rate import actual360, thirty360, is_month_end


@pytest.mark.parametrize(
    'dt1,dt2,expected',
    [
        (datetime(2019, 1, 1), datetime(2019, 1, 1), 0 / 360),
        (datetime(2019, 1, 1), datetime(2021, 1, 1), 731 / 360),
        (datetime(2019, 1, 1), datetime(2021, 1, 15), 745 / 360),
        (datetime(2019, 1, 15), datetime(2021, 1, 17), 733 / 360),
        (datetime(2019, 1, 31), datetime(2021, 1, 31), 731 / 360),
        (datetime(2019, 1, 16), datetime(2017, 12, 31), -381 / 360),
    ]
)
def test_actual360(dt1, dt2, expected):
    assert expected == actual360(dt1, dt2)


@pytest.mark.parametrize(
    'dt1,dt2,expected',
    [
        (datetime(2019, 1, 1), datetime(2019, 1, 1), 0 / 360),
        (datetime(2019, 1, 1), datetime(2021, 1, 1), 720 / 360),
        (datetime(2019, 1, 1), datetime(2021, 1, 15), 734 / 360),
        (datetime(2019, 1, 15), datetime(2021, 1, 17), 722 / 360),
        (datetime(2019, 1, 31), datetime(2021, 1, 31), 720 / 360),
        (datetime(2019, 1, 16), datetime(2017, 12, 31), -375 / 360),
    ]
)
def test_thirty360(dt1, dt2, expected):
    assert expected == thirty360(dt1, dt2)


@pytest.mark.parametrize(
    'dt,expected',
    [
        (datetime(2019, 1, 1), False),
        (datetime(2019, 1, 31), True),
        (datetime(2019, 6, 30), True),
        (datetime(2019, 2, 28), True),
        (datetime(2020, 2, 28), False),
        (datetime(2020, 2, 29), True)
    ]
)
def test_is_month_end(dt, expected):
    assert is_month_end(dt) == expected


# @pytest.mark.parametrize(
#     'rate,freq,expected',
#     [
#         (0, relativedelta(months=3), 0.0),
#         (0.1, relativedelta(years=2), 0.21),
#         (0.1, relativedelta(years=1), 0.1),
#         (0.1, relativedelta(months=3), 0.0241136890844451),
#         (0.1, relativedelta(months=1), 0.00797414042890376),
#         (-0.05, relativedelta(months=3), -0.0127414550985662),
#         (0.1, relativedelta(months=1, days=1), 0.008237380814549500)
#     ]
# )
# def test_decompounded_periodic_rate(rate, freq, expected):
#     assert decompounded_periodic_rate(rate, freq) + expected == pytest.approx(2 * expected)
#
#
# @pytest.mark.parametrize(
#     'rate,freq,expected',
#     [
#         (0, relativedelta(months=3), 0.0),
#         (0.1, relativedelta(years=2), 0.2),
#         (0.1, relativedelta(years=1), 0.1),
#         (0.1, relativedelta(months=3), 0.025),
#         (0.1, relativedelta(months=1), 0.008333333333333330),
#         (-0.05, relativedelta(months=3), -0.0125),
#         (0.1, relativedelta(months=1, days=1), 0.008607305936073060)
#     ]
# )
# def test_simple_periodic_rate(rate, freq, expected):
#     assert simple_periodic_rate(rate, freq) + expected == pytest.approx(2 * expected)
