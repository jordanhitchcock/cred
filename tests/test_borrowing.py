from cred import FixedRateBorrowing, thirty360
from datetime import datetime
from dateutil.relativedelta import relativedelta

import pandas as pd
import pytest

# TODO clean up testing for Borrowing

@pytest.fixture
def fixed_io_borrowing():
    borrowing = FixedRateBorrowing(datetime(2020,1,1), datetime(2020,7,1), relativedelta(months=1), 0.05, -100, day_count=thirty360)
    return borrowing

@pytest.fixture
def floating_io_borrowing():
    borrowing = AbstractBorrowing()
    return borrowing


@pytest.fixture
def fixed_constant_pmt_borrowing():
    borrowing = AbstractBorrowing()
    return borrowing


@pytest.fixture
def fixed_custom_amort_borrowing():
    borrowing = AbstractBorrowing()
    return borrowing


@pytest.fixture
def floating_custom_amort_borrowing():
    borrowing = AbstractBorrowing()
    return borrowing


@pytest.fixture
def fixed_custom_accreting_borrowing():
    borrowing = AbstractBorrowing()
    return borrowing


@pytest.fixture
def floating_custom_accreting_borrowing():
    borrowing = AbstractBorrowing()
    return borrowing


def test_fixed_io_schedule(fixed_io_borrowing):
    actual = fixed_io_borrowing.schedule()

    expected = pd.DataFrame({
        'start_date': [datetime(2020,1,1), datetime(2020,2,1), datetime(2020,3,1), datetime(2020,4,1), datetime(2020,5,1), datetime(2020,6,1)],
        'end_date': [datetime(2020, 2, 1), datetime(2020, 3, 1), datetime(2020, 4, 1), datetime(2020, 5, 1), datetime(2020, 6, 1), datetime(2020, 7, 1)],
        'bop_principal': [-100] * 6,
        'interest_rate': [0.05] * 6,
        'interest_payment': [-5 / 12] * 6,
        'principal_payment': [0] * 5 + [-100],
        'eop_principal': [-100] * 5 + [0]
    })
    pd.testing.assert_frame_equal(actual, expected)


def test_floating_io_schedule(floating_io_borrowing):
    actual = floating_io_borrowing.schedule()

    expected = {
        'period': [1, 2, 3, 4, 5, 6],
        'bop_principal': [-100.00] * 6,
        'index_rate': [0.02] * 3 + [0.03] * 3,
        'interest_rate': [0.05] * 3 + [0.06] * 3,
        'interest': [-5.0] * 3 + [-6.0] * 3,
        'principal': [0] * 5 + [-100],
        'payment': [-5.0] * 3 + [-6.0] * 2 + [-106.0],
        'eop_principal': [-100.0] * 5 + [0.0]
    }

    assert actual == expected


def test_fixed_constant_pmt_schedule(fixed_constant_pmt_borrowing):
    actual = fixed_constant_pmt_borrowing.schedule()

    expected = {
        'period': [1, 2, 3, 4, 5, 6],
        'bop_principal': [-100.00, -98.49, -96.90, -95.24, -93.49, -91.66],
        'coupon': [0.05] * 6,
        'interest': [-5.00, -4.92, -4.85, -4.76, -4.67, -4.58],
        'principal': [-1.51, -1.59, -1.66, -1.75, -1.84, -91.65],
        'payment': [-6.51, -6.51, -6.51, -6.51, -6.51, -96.23],
        'eop_principal': [-98.49, -96.9, -95.24, -93.49, -91.65, 0.00]
    }

    assert actual == expected


def test_fixed_custom_amort_schedule(fixed_custom_amort_borrowing):
    actual = fixed_custom_amort_borrowing.schedule()

    expected = {
        'period': [1, 2, 3, 4, 5, 6],
        'bop_principal': [-100.00, -99.00, -98.00, -97.00, -96.00, -95.00],
        'coupon': [0.05] * 6,
        'interest': [-5.00, -4.95, -4.90, -4.85, -4.80, -4.75],
        'principal': [-1.00] * 5 + [-95.00],
        'payment': [-6.00, -5.95, -5.90, -5.85, -5.80, -5.75],
        'eop_principal': [-99.00, -98.00, -97.00, -96.00, -95.00, 0.00]
    }

    assert actual == expected


def test_floating_custom_amort_schedule(floating_custom_amort_borrowing):
    actual = floating_custom_amort_borrowing.schedule()

    expected = {
        'period': [1, 2, 3, 4, 5, 6],
        'bop_principal': [-100.00, -99.00, -98.00, -97.00, -96.00, -95.00],
        'index_rate': [0.02] * 3 + [0.03] * 3,
        'interest_rate': [0.05] * 3 + [0.06] * 3,
        'interest': [-5.0, -4.95, -4.9, -5.82, -5.76, -5.7],
        'principal': [-1.00] * 5 + [-95.00],
        'payment': [-6.0, -5.95, -5.9, -6.82, -6.76, -100.7],
        'eop_principal': [-99.00, -98.00, -97.00, -96.00, -95.00, 0.00]
    }

    assert actual == expected


def test_fixed_custom_accreting_schedule(fixed_custom_accreting_borrowing):
    actual = fixed_custom_accreting_borrowing.schedule()

    expected = {
        'period': [1, 2, 3, 4, 5, 6],
        'bop_principal': [-100.0, -101.0, -102.0, -103.0, -104.0, -105.0],
        'coupon': [0.05] * 6,
        'interest': [-5.0, -5.05, -5.1, -5.15, -5.2, -5.25],
        'principal': [1.0] * 5 + [-105.0],
        'payment': [-4.0, -4.05, -4.1, -4.15, -4.2, -110.25],
        'eop_principal': [-101.0, -102.0, -103.0, -104.0, -105.0, 0.0]
    }

    assert actual == expected


def test_floating_custom_accreting_schedule(floating_custom_accreting_borrowing):
    actual = floating_custom_accreting_borrowing.schedule()

    expected = {
        'period': [1, 2, 3, 4, 5, 6],
        'bop_principal': [-100.00, -101.00, -102.00, -103.00, -104.00, -105.00],
        'index_rate': [0.02] * 3 + [0.03] * 3,
        'interest_rate': [0.05] * 3 + [0.06] * 3,
        'interest': [-5.0, -5.05, -5.1, -6.18, -6.24, -6.3],
        'principal': [1.00] * 5 + [-105.00],
        'payment': [-4.0, -4.05, -4.1, -5.18, -5.24, -111.3],
        'eop_principal': [-101.0, -102.0, -103.0, -104.0, -105.0, 0.00]
    }

    assert actual == expected
