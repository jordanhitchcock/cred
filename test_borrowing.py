from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import pytest
from borrowing import _Borrowing, PeriodicBorrowing, FixedRateBorrowing


@pytest.fixture
def borrowing():
    return _Borrowing()


@pytest.fixture
def simple_borrowing_subclass():
    class SubBorrowing(_Borrowing):
        def set_period_values(self, period):
            period.add_balance(100, 'bop_principal')
            period.add_display_field(0.09, 'interest_rate')
            period.add_payment(9, 'interest')
            return period

    return SubBorrowing()


@pytest.fixture
def periodic_borrowing():
    pb = PeriodicBorrowing(datetime(2020, 1, 1),
                           datetime(2022, 1, 1),
                           relativedelta(months=1),
                           1_000_000.0)
    return pb


@pytest.fixture
def fixed_io():
    return FixedRateBorrowing(
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2022, 1, 1),
        freq=relativedelta(months=1),
        initial_principal=1_000_000.0,
        coupon=0.12,
        amort_periods=None
    )


@pytest.fixture
def fixed_amortizing_constant_pmt():
    return FixedRateBorrowing(
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2022, 1, 1),
        freq=relativedelta(months=1),
        initial_principal=1_000_000.0,
        coupon=0.12,
        amort_periods=360
    )


@pytest.fixture
def fixed_amortizing_custom():
    return FixedRateBorrowing(
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2022, 1, 1),
        freq=relativedelta(months=1),
        initial_principal=1_000_000.0,
        coupon=0.12,
        amort_periods=[5_000.0] * 23 + [885000.0]
    )


def test_period(simple_borrowing_subclass):
    assert simple_borrowing_subclass.period(0).index == 0
    assert simple_borrowing_subclass.period(5).index == 5
    with pytest.raises(IndexError) as error:
        simple_borrowing_subclass.period(-1)
        assert 'Cannot access period with index less than 0' in str(error.value)
    # with pytest.raises(IndexError):
    #     borrowing.period(1000)


def test_context_manager(simple_borrowing_subclass):
    assert len(simple_borrowing_subclass._periods) == 0
    with simple_borrowing_subclass as sbs:
        sbs.period(2)
        assert len(sbs._periods) == 1
        sbs.period(0)
        assert len(sbs._periods) == 2

    assert len(simple_borrowing_subclass._periods) == 0


def test_create_period(simple_borrowing_subclass):
    assert simple_borrowing_subclass._create_period(2).index == 2
    with pytest.raises(ValueError) as error:
        simple_borrowing_subclass._create_period(-1)
        assert 'Value for period index must be greater than or equal to 0' in str(error.value)
    # with pytest.raises(IndexError):
    #     borrowing.create_period(1000)


def test_set_period_values(borrowing, simple_borrowing_subclass):
    with pytest.raises(NotImplementedError):
        borrowing.set_period_values(0)

    p = simple_borrowing_subclass.period(0)
    assert p.outstanding_principal() == 100
    assert p.payment() == 9
    assert p.schedule() == {
        'index': 0,
        'bop_principal': 100,
        'interest_rate': 0.09,
        'interest': 9
    }


def test_fixed_rate_schedule(fixed_io):
    expected_schedule = pd.read_csv('test_fixed_io_schedule.csv', index_col='index', parse_dates=[1, 2, 3])
    pd.testing.assert_frame_equal(expected_schedule, fixed_io.schedule())


def test_fixed_amortizing_constant_pmt_schedule(fixed_amortizing_constant_pmt):
    expected_schedule = pd.read_csv('test_fixed_amortizing_constant_pmt_schedule.csv', index_col='index',
                                    parse_dates=[1, 2, 3])
    pd.testing.assert_frame_equal(expected_schedule, fixed_amortizing_constant_pmt.schedule())


def test_fixed_amortizing_custom_schedule(fixed_amortizing_custom):
    expected_schedule = pd.read_csv('test_fixed_amortizing_custom_schedule.csv', index_col='index',
                                    parse_dates=[1, 2, 3])
    pd.testing.assert_frame_equal(expected_schedule, fixed_amortizing_custom.schedule())

