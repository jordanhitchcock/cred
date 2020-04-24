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


def test_date_index_no_stubs(fixed_io_no_stubs):
    assert fixed_io_no_stubs.date_index(datetime(2020, 1, 1)) == 0  # borrowing start date
    assert fixed_io_no_stubs.date_index(datetime(2020, 1, 2)) == 0
    assert fixed_io_no_stubs.date_index(datetime(2020, 1, 31)) == 0
    assert fixed_io_no_stubs.date_index(datetime(2020, 2, 1)) == 1
    assert fixed_io_no_stubs.date_index(datetime(2021, 12, 31)) == 23
    assert fixed_io_no_stubs.date_index(datetime(2022, 1, 1)) == 23  # borrowing end date
    with pytest.raises(Exception):
        fixed_io_no_stubs.date_index(datetime(2019, 12, 31))  # before borrowing start date
    with pytest.raises(Exception):
        fixed_io_no_stubs.date_index(datetime(2022, 1, 2))  # after borrowing end date


def test_date_index_start_stub(fixed_io_start_stub):
    assert fixed_io_start_stub.date_index(datetime(2020, 1, 16)) == 0  # borrowing start date
    assert fixed_io_start_stub.date_index(datetime(2020, 1, 18)) == 0
    assert fixed_io_start_stub.date_index(datetime(2020, 1, 31)) == 0
    assert fixed_io_start_stub.date_index(datetime(2020, 2, 1)) == 1
    assert fixed_io_start_stub.date_index(datetime(2021, 12, 31)) == 23
    assert fixed_io_start_stub.date_index(datetime(2022, 1, 1)) == 23  # borrowing end date
    with pytest.raises(Exception):
        fixed_io_start_stub.date_index(datetime(2020, 1, 1))  # before borrowing start date
    with pytest.raises(Exception):
        fixed_io_start_stub.date_index(datetime(2022, 1, 2))  # after borrowing end date


def test_date_index_end_stub(fixed_io_end_stub):
    assert fixed_io_end_stub.date_index(datetime(2020, 1, 1)) == 0  # borrowing start date
    assert fixed_io_end_stub.date_index(datetime(2020, 1, 18)) == 0
    assert fixed_io_end_stub.date_index(datetime(2020, 1, 31)) == 0
    assert fixed_io_end_stub.date_index(datetime(2020, 2, 1)) == 1
    assert fixed_io_end_stub.date_index(datetime(2021, 12, 31)) == 23
    assert fixed_io_end_stub.date_index(datetime(2022, 1, 1)) == 24
    assert fixed_io_end_stub.date_index(datetime(2022, 1, 16)) == 24
    with pytest.raises(Exception):
        fixed_io_end_stub.date_index(datetime(2019, 12, 31))  # before borrowing start date
    with pytest.raises(Exception):
        fixed_io_end_stub.date_index(datetime(2022, 1, 17))  # after borrowing end date


def test_date_index_start_and_end_stubs(fixed_io_start_and_end_stubs):
    assert fixed_io_start_and_end_stubs.date_index(datetime(2020, 1, 16)) == 0  # borrowing start date
    assert fixed_io_start_and_end_stubs.date_index(datetime(2020, 1, 18)) == 0
    assert fixed_io_start_and_end_stubs.date_index(datetime(2020, 1, 31)) == 0
    assert fixed_io_start_and_end_stubs.date_index(datetime(2020, 2, 1)) == 1
    assert fixed_io_start_and_end_stubs.date_index(datetime(2021, 12, 31)) == 23
    assert fixed_io_start_and_end_stubs.date_index(datetime(2022, 1, 1)) == 24
    assert fixed_io_start_and_end_stubs.date_index(datetime(2022, 1, 16)) == 24
    with pytest.raises(IndexError):
        fixed_io_start_and_end_stubs.date_index(datetime(2019, 12, 31))  # before borrowing start date
    with pytest.raises(Exception):
        fixed_io_start_and_end_stubs.date_index(datetime(2022, 1, 17))  # after borrowing end date
    # one day stub periods
    fixed_io_start_and_end_stubs.start_date = datetime(2020, 1, 31)
    fixed_io_start_and_end_stubs.end_date = datetime(2022, 1, 2)
    assert fixed_io_start_and_end_stubs.date_index(datetime(2020, 1, 31)) == 0
    assert fixed_io_start_and_end_stubs.date_index(datetime(2020, 2, 1)) == 1
    assert fixed_io_start_and_end_stubs.date_index(datetime(2022, 1, 1)) == 24
    assert fixed_io_start_and_end_stubs.date_index(datetime(2022, 1, 2)) == 24


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


# Test accrued interest
def test_accrued(fixed_constant_amort_start_and_end_stubs):
    fixed_constant_amort_start_and_end_stubs.io_periods = 6
    assert fixed_constant_amort_start_and_end_stubs.accrued(datetime(2020, 1, 2), 'interest_payment') == pytest.approx(0.0)
    assert fixed_constant_amort_start_and_end_stubs.accrued(datetime(2020, 1, 17), 'interest_payment') == pytest.approx(5000.0)
    assert fixed_constant_amort_start_and_end_stubs.accrued(datetime(2020, 6, 1), 'interest_payment') == pytest.approx(0.0)
    assert fixed_constant_amort_start_and_end_stubs.accrued(datetime(2020, 12, 15), 'interest_payment') == pytest.approx(4652.66240004073)
    assert fixed_constant_amort_start_and_end_stubs.accrued(datetime(2021, 12, 2), 'interest_payment') == pytest.approx(328.9536160567391)
    with pytest.raises(IndexError):
        fixed_constant_amort_start_and_end_stubs.accrued(datetime(2020, 1, 1), 'interest_payment')
    with pytest.raises(IndexError):
        fixed_constant_amort_start_and_end_stubs.accrued(datetime(2021, 12, 3), 'interest_payment')


def test_accrued_and_unpaid(fixed_io_start_and_end_stubs):
    assert fixed_io_start_and_end_stubs.accrued_and_unpaid(datetime(2020, 1, 16), 'interest_payment') == pytest.approx(-5333.33333333333)  # start stub prepaid
    assert fixed_io_start_and_end_stubs.accrued_and_unpaid(datetime(2020, 1, 17), 'interest_payment') == pytest.approx(-5000.0)  # start stub prepaid
    assert fixed_io_start_and_end_stubs.accrued_and_unpaid(datetime(2020, 2, 1), 'interest_payment') == pytest.approx(0.0)
    assert fixed_io_start_and_end_stubs.accrued_and_unpaid(datetime(2020, 2, 15), 'interest_payment') == pytest.approx(4666.66666666667)
    assert fixed_io_start_and_end_stubs.accrued_and_unpaid(datetime(2020, 3, 1), 'interest_payment') == pytest.approx(9666.66666666667)  # pmt date 3/2
    assert fixed_io_start_and_end_stubs.accrued_and_unpaid(datetime(2022, 1, 16), 'interest_payment') == pytest.approx(5000.0)  # maturity date
    with pytest.raises(IndexError):
        fixed_io_start_and_end_stubs.accrued_and_unpaid(datetime(2020, 1, 15), 'interest_payment')
    # TODO: raises index error if dt is after the last period end date but before the last period payment date


# Test outstanding balance
def test_outstanding_amount(fixed_constant_amort_start_and_end_stubs):
    assert fixed_constant_amort_start_and_end_stubs.outstanding_amount(datetime(2020, 1, 2)) == pytest.approx(1000000.0)  # closing date
    assert fixed_constant_amort_start_and_end_stubs.outstanding_amount(datetime(2020, 1, 15)) == pytest.approx(1000000.0)
    assert fixed_constant_amort_start_and_end_stubs.outstanding_amount(datetime(2020, 3, 1)) == pytest.approx(998760.225513185)  # period end date
    assert fixed_constant_amort_start_and_end_stubs.outstanding_amount(datetime(2021, 12, 2)) == pytest.approx(0.0)  # maturity date
    with pytest.raises(IndexError):
        fixed_constant_amort_start_and_end_stubs.outstanding_amount(datetime(2020, 1, 1))

