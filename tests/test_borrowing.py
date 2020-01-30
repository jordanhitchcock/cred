from cred import FixedRateBorrowing, thirty360, open_repayment, defeasance, actual360
from datetime import datetime
from dateutil.relativedelta import relativedelta

import pandas as pd
import pytest


@pytest.fixture
def fixed_constant_payment_amort_borrowing():
    borrowing = FixedRateBorrowing.monthly_amortizing_loan(start_date=datetime(2015, 1, 1),
                                                           principal=1_000_000,
                                                           coupon=0.05,
                                                           periods=120,
                                                           repayment=defeasance(lambda dt1, dt2: 0.02))
    return borrowing


def test_fixed_constant_payment_amort_schedule(fixed_constant_payment_amort_borrowing):
    expected = pd.read_csv('./tests/data/fixed_constant_payment_amort_borrowing.csv')
    expected['start_date'] = pd.to_datetime(expected['start_date'])
    expected['end_date'] = pd.to_datetime(expected['end_date'])
    pd.testing.assert_frame_equal(expected, fixed_constant_payment_amort_borrowing.schedule())


def test_fixed_constant_payment_amort_defeasance(fixed_constant_payment_amort_borrowing):
    actual20210801 = fixed_constant_payment_amort_borrowing.repayment_cost(datetime(2021, 8, 1))
    assert 981006.562220998 + actual20210801 == pytest.approx(981006.562220998 * 2)

    actual20210817 = fixed_constant_payment_amort_borrowing.repayment_cost(datetime(2021, 8, 17))
    assert 981870.3426046750 + actual20210817 == pytest.approx(981870.342604675000000 * 2)

    actual20250101 = fixed_constant_payment_amort_borrowing.repayment_cost(datetime(2025, 1, 1))
    assert 0.0 + actual20250101 == pytest.approx(0.0)


def test_fixed_constant_payment_amort_net_cash_flow(fixed_constant_payment_amort_borrowing):
    expected_schedule = pd.read_csv('./tests/data/fixed_constant_payment_amort_borrowing_net_cash_flow.csv',
                                    index_col=0)

    expected_schedule.index = pd.to_datetime(expected_schedule.index)
    expected = expected_schedule['2021-08-01'].dropna()
    expected.name = None
    actual = fixed_constant_payment_amort_borrowing.net_cash_flows(datetime(2021, 8, 1))
    pd.testing.assert_series_equal(expected, actual)

    expected_schedule.index = pd.to_datetime(expected_schedule.index)
    expected = expected_schedule['2021-08-17'].dropna()
    expected.name = None
    actual = fixed_constant_payment_amort_borrowing.net_cash_flows(datetime(2021, 8, 17))
    pd.testing.assert_series_equal(expected, actual)

    expected_schedule.index = pd.to_datetime(expected_schedule.index)
    expected = expected_schedule['2025-01-01'].dropna()
    expected.name = None
    actual = fixed_constant_payment_amort_borrowing.net_cash_flows(datetime(2025, 1, 1))
    pd.testing.assert_series_equal(expected, actual)

