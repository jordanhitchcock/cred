from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import pytest
from cred.borrowing import _Borrowing, FixedRateBorrowing
from cred.interest_rate import actual360, thirty360
from cred.businessdays import modified_following, FederalReserveHolidays


# Test _Borrowing and PeriodicBorrowing
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
    # TODO: Index out of upper bound range
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


# Test FixedRateBorrowing

# Fixed rate interest only
@pytest.fixture
def fixed_io_no_stubs():
    return FixedRateBorrowing(
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2022, 1, 1),
        freq=relativedelta(months=1),
        initial_principal=1_000_000.0,
        coupon=0.12,
        amort_periods=None,
        year_frac=actual360,
        pmt_convention=modified_following,
        holidays=FederalReserveHolidays()
    )


@pytest.fixture
def fixed_io_start_stub():
    return FixedRateBorrowing(
        start_date=datetime(2020, 1, 16),
        end_date=datetime(2022, 1, 1),
        first_reg_start=datetime(2020, 2, 1),
        freq=relativedelta(months=1),
        initial_principal=1_000_000.0,
        coupon=0.12,
        amort_periods=None,
        year_frac=actual360,
        pmt_convention=modified_following,
        holidays=FederalReserveHolidays()
    )


@pytest.fixture
def fixed_io_end_stub():
    return FixedRateBorrowing(
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2022, 1, 16),
        freq=relativedelta(months=1),
        initial_principal=1_000_000.0,
        coupon=0.12,
        amort_periods=None,
        year_frac=actual360,
        pmt_convention=modified_following,
        holidays=FederalReserveHolidays()
    )


@pytest.fixture
def fixed_io_start_and_end_stubs():
    return FixedRateBorrowing(
        start_date=datetime(2020, 1, 16),
        end_date=datetime(2022, 1, 16),
        freq=relativedelta(months=1),
        first_reg_start=datetime(2020, 2, 1),
        initial_principal=1_000_000.0,
        coupon=0.12,
        amort_periods=None,
        year_frac=actual360,
        pmt_convention=modified_following,
        holidays=FederalReserveHolidays()
    )


def test_fixed_io_no_stubs_schedule(fixed_io_no_stubs):
    expected_no_stubs = pd.read_csv('tests/data/test_fixed_io_schedule_no_stubs.csv',
                                    index_col='index',
                                    parse_dates=[1, 2, 3])
    pd.testing.assert_frame_equal(expected_no_stubs, fixed_io_no_stubs.schedule())


def test_fixed_io_start_stub_schedule(fixed_io_start_stub):
    expected_start_stub = pd.read_csv('tests/data/test_fixed_io_schedule_start_stub.csv',
                                      index_col='index',
                                      parse_dates=[1, 2, 3])
    pd.testing.assert_frame_equal(expected_start_stub, fixed_io_start_stub.schedule())


def test_fixed_io_end_stub_schedule(fixed_io_end_stub):
    expected_end_stub = pd.read_csv('tests/data/test_fixed_io_schedule_end_stub.csv',
                                    index_col='index',
                                    parse_dates=[1, 2, 3])
    pd.testing.assert_frame_equal(expected_end_stub, fixed_io_end_stub.schedule())


def test_fixed_io_start_and_end_stubs_schedule(fixed_io_start_and_end_stubs):
    expected_start_and_end_stub = pd.read_csv('tests/data/test_fixed_io_schedule_start_and_end_stubs.csv',
                                              index_col='index',
                                              parse_dates=[1, 2, 3])
    pd.testing.assert_frame_equal(expected_start_and_end_stub, fixed_io_start_and_end_stubs.schedule())


# Fixed rate with constant payment amortization
@pytest.fixture
def fixed_constant_amort_no_stubs():
    return FixedRateBorrowing(
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2022, 1, 1),
        freq=relativedelta(months=1),
        initial_principal=1_000_000.0,
        coupon=0.12,
        amort_periods=250,
        year_frac=actual360
    )

# TODO: No amort on stub payment
@pytest.fixture
def fixed_constant_amort_start_stub():
    return FixedRateBorrowing(
        start_date=datetime(2020, 1, 17),
        end_date=datetime(2022, 1, 1),
        freq=relativedelta(months=1),
        first_reg_start=datetime(2020, 2, 1),
        initial_principal=1_000_000.0,
        coupon=0.12,
        amort_periods=250,
        year_frac=actual360
    )


@pytest.fixture
def fixed_constant_amort_end_stub():
    return FixedRateBorrowing(
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2021, 12, 15),
        freq=relativedelta(months=1),
        initial_principal=1_000_000.0,
        coupon=0.12,
        amort_periods=250,
        year_frac=actual360
    )


@pytest.fixture
def fixed_constant_amort_start_and_end_stubs():
    return FixedRateBorrowing(
        start_date=datetime(2020, 1, 2),
        end_date=datetime(2021, 12, 2),
        freq=relativedelta(months=1),
        first_reg_start=datetime(2020, 2, 1),
        initial_principal=1_000_000.0,
        coupon=0.12,
        amort_periods=250,
        year_frac=actual360
    )


def test_fixed_constant_amort_no_stubs(fixed_constant_amort_no_stubs):
    expected_no_stubs = pd.read_csv('tests/data/test_fixed_constant_amort_no_stubs.csv',
                                    index_col='index',
                                    parse_dates=[1, 2, 3])
    pd.testing.assert_frame_equal(expected_no_stubs, fixed_constant_amort_no_stubs.schedule())


def test_fixed_constant_amort_start_stub(fixed_constant_amort_start_stub):
    expected_start_stub = pd.read_csv('tests/data/test_fixed_constant_amort_start_stub.csv',
                                      index_col='index',
                                      parse_dates=[1, 2, 3])
    pd.testing.assert_frame_equal(expected_start_stub, fixed_constant_amort_start_stub.schedule())


def test_fixed_constant_amort_end_stub(fixed_constant_amort_end_stub):
    expected_end_stub = pd.read_csv('tests/data/test_fixed_constant_amort_end_stub.csv',
                                    index_col='index',
                                    parse_dates=[1, 2, 3])
    pd.testing.assert_frame_equal(expected_end_stub, fixed_constant_amort_end_stub.schedule())


def test_fixed_constant_amort_start_and_end_stubs(fixed_constant_amort_start_and_end_stubs):
    expected_start_and_end_stub = pd.read_csv('tests/data/test_fixed_constant_amort_start_and_end_stubs.csv',
                                              index_col='index',
                                              parse_dates=[1, 2, 3])
    pd.testing.assert_frame_equal(expected_start_and_end_stub, fixed_constant_amort_start_and_end_stubs.schedule())


def test_fixed_constant_amort_parital_io(fixed_constant_amort_no_stubs, fixed_constant_amort_start_and_end_stubs):
    fixed_constant_amort_no_stubs.io_periods = 6
    expected_no_stub = pd.read_csv('tests/data/test_fixed_constant_amort_no_stubs_6mo_io.csv',
                                   index_col='index',
                                   parse_dates=[1, 2, 3])
    pd.testing.assert_frame_equal(expected_no_stub, fixed_constant_amort_no_stubs.schedule())

    fixed_constant_amort_start_and_end_stubs.io_periods = 6
    expected_end_and_start_stubs = pd.read_csv('tests/data/test_fixed_constant_amort_start_and_end_stubs_6mo_io.csv',
                                               index_col='index',
                                               parse_dates=[1, 2, 3])
    pd.testing.assert_frame_equal(expected_end_and_start_stubs, fixed_constant_amort_start_and_end_stubs.schedule())


# Fixed rate with custom amortization schedule
@pytest.fixture
def fixed_amortizing_custom_no_stubs():
    return FixedRateBorrowing(
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2022, 1, 1),
        freq=relativedelta(months=1),
        initial_principal=1_000_000.0,
        coupon=0.12,
        amort_periods=[5_000.0] * 23 + [885000.0],
        year_frac=thirty360
    )


@pytest.fixture
def fixed_amortizing_custom_start_stub():
    return FixedRateBorrowing(
        start_date=datetime(2020, 1, 16),
        end_date=datetime(2022, 1, 1),
        freq=relativedelta(months=1),
        first_reg_start=datetime(2020, 2, 1),
        initial_principal=1_000_000.0,
        coupon=0.12,
        amort_periods=[5_000.0] * 23 + [885000.0],
        year_frac=thirty360
    )


@pytest.fixture
def fixed_amortizing_custom_end_stub():
    return FixedRateBorrowing(
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2022, 1, 15),
        freq=relativedelta(months=1),
        initial_principal=1_000_000.0,
        coupon=0.12,
        amort_periods=[5_000.0] * 24 + [880000.0],
        year_frac=thirty360
    )


@pytest.fixture
def fixed_amortizing_custom_start_and_end_stubs():
    return FixedRateBorrowing(
        start_date=datetime(2020, 1, 16),
        end_date=datetime(2021, 12, 12),
        freq=relativedelta(months=1),
        first_reg_start=datetime(2020, 2, 1),
        initial_principal=1_000_000.0,
        coupon=0.12,
        amort_periods=[5_000.0] * 23 + [885000.0],
        year_frac=thirty360
    )


def test_fixed_amortizing_custom_no_stubs(fixed_amortizing_custom_no_stubs):
    expected_schedule = pd.read_csv('tests/data/test_fixed_amortizing_custom_no_stubs.csv',
                                    index_col='index',
                                    parse_dates=[1, 2, 3])
    pd.testing.assert_frame_equal(expected_schedule, fixed_amortizing_custom_no_stubs.schedule())


def test_fixed_amortizing_custom_start_stub(fixed_amortizing_custom_start_stub):
    expected_schedule = pd.read_csv('tests/data/test_fixed_amortizing_custom_start_stub.csv',
                                    index_col='index',
                                    parse_dates=[1, 2, 3])
    pd.testing.assert_frame_equal(expected_schedule, fixed_amortizing_custom_start_stub.schedule())


def test_fixed_amortizing_custom_end_stub(fixed_amortizing_custom_end_stub):
    expected_schedule = pd.read_csv('tests/data/test_fixed_amortizing_custom_end_stub.csv',
                                    index_col='index',
                                    parse_dates=[1, 2, 3])
    pd.testing.assert_frame_equal(expected_schedule, fixed_amortizing_custom_end_stub.schedule())


def test_fixed_amortizing_custom_start_and_end_stubs(fixed_amortizing_custom_start_and_end_stubs):
    expected_schedule = pd.read_csv('tests/data/test_fixed_amortizing_custom_start_and_end_stubs.csv',
                                    index_col='index',
                                    parse_dates=[1, 2, 3])
    pd.testing.assert_frame_equal(expected_schedule, fixed_amortizing_custom_start_and_end_stubs.schedule())


