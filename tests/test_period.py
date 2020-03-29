from datetime import date
import pytest
from cred.period import Period, InterestPeriod


@pytest.fixture
def period():
    return Period(0)


@pytest.fixture
def interest_period():
    return InterestPeriod(0)


def test_outstanding_principal(period):
    assert period.outstanding_principal() == 0
    period.add_balance(9, 'bop_principal')
    assert period.outstanding_principal() == 9
    period.add_balance(4, 'draws')
    assert period.outstanding_principal() == 13


def test_balance_cols(period):
    assert period.balance_cols == []
    period.add_balance(9, 'bop_principal')
    assert period.balance_cols == ['bop_principal']
    period.add_balance(4, 'draws')
    assert period.balance_cols == ['bop_principal', 'draws']


def test_payment(period):
    assert period.payment() == 0
    period.add_payment(9, 'interest')
    assert period.payment() == 9
    period.add_payment(4, 'principal')
    assert period.payment() == 13


def test_payment_cols(period):
    assert period.payment_cols == []
    period.add_payment(None, 'interest')
    period.add_payment(None, 'principal')
    assert period.payment_cols == ['interest', 'principal']


def test_add_display_field(period):
    assert period.display_field_cols == ['index']
    period.add_display_field(0.01, 'index_rate')
    assert period.display_field_cols == ['index', 'index_rate']
    period.add_display_field(0.05, 'interest_rate')
    assert period.display_field_cols == ['index', 'index_rate', 'interest_rate']


def test_schedule_cols(period):
    assert period.schedule_cols == ['index']
    period.add_display_field(0.03, 'interest_rate')
    assert period.schedule_cols == ['index', 'interest_rate']
    period.add_balance(100, 'bop_principal')
    assert period.schedule_cols == ['index', 'interest_rate', 'bop_principal']
    period.add_payment(3, 'interest_payment')
    assert period.schedule_cols == ['index', 'interest_rate', 'bop_principal', 'interest_payment']


def test_schedule(period):
    assert period.schedule() == {'index': 0}
    period.add_balance(100, 'bop_principal')
    period.add_display_field(0.05, 'interest_rate')
    period.add_payment(5, 'interest_payment')
    assert period.schedule() == {
        'index': 0,
        'bop_principal': 100,
        'interest_rate': 0.05,
        'interest_payment': 5
    }


def test_interest_period_attributes(interest_period):
    interest_period.add_start_date(date(2020, 1, 1), 'start_date')
    interest_period.add_end_date(date(2020, 2, 1), 'end_date')
    interest_period.add_pmt_date(date(2020, 2, 1), 'pmt_date')
    assert interest_period.start_date == date(2020, 1, 1)
    assert interest_period.end_date == date(2020, 2, 1)
    assert interest_period.pmt_date == date(2020, 2, 1)


def test_interest_period_schedule(interest_period):
    assert interest_period.schedule() == {'index': 0}
    interest_period.add_balance(100, 'bop_principal')
    interest_period.add_display_field(0.05, 'interest_rate')
    interest_period.add_payment(5, 'interest_payment')
    assert interest_period.schedule() == {
        'index': 0,
        'bop_principal': 100,
        'interest_rate': 0.05,
        'interest_payment': 5
    }
    # TODO: Decide if/when and what type of errors to raise if start/end/pmt dates are not set
    # Maybe just when they are needed, so if asking for balance or similar?

