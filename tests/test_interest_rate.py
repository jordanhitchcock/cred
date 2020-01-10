from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytest

from cred.interest_rate import actual360, thirty360, is_month_end


class Provider:
    def spread(self, period):
        return 0.03

    def index_rate(self, period):
        return 0.01

    def coupon(self, period):
        return 0.05


rate_provider = Provider()


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

