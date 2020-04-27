import pytest
from datetime import datetime
from dateutil.relativedelta import relativedelta

from cred import FixedRateBorrowing, actual360, following, thirty360
from cred.borrowingutils import _pmts_between_dates, defeasance


@pytest.fixture
def fixed_constant_amort_end_stub():
    return FixedRateBorrowing(
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2021, 12, 18),
        freq=relativedelta(months=1),
        initial_principal=1_000_000.0,
        coupon=0.12,
        amort_periods=250,
        year_frac=actual360,
        pmt_convention=following
    )


def test_pmts_between_dates(fixed_constant_amort_end_stub):
    assert _pmts_between_dates(fixed_constant_amort_end_stub,
                                  datetime(2019, 1, 1),
                                  datetime(2021, 12, 20)) == dict(fixed_constant_amort_end_stub.payments(pmt_dt=True))  # prior to closing date to last pmt
    assert _pmts_between_dates(fixed_constant_amort_end_stub,
                                  datetime(2020, 1, 1),
                                  datetime(2021, 12, 20)) == dict(fixed_constant_amort_end_stub.payments(pmt_dt=True))  # closing date to last pmt
    assert _pmts_between_dates(fixed_constant_amort_end_stub,
                                  datetime(2021, 12, 15),
                                  datetime(2021, 12, 20)) == {datetime(2021, 12, 20, 0, 0): 985930.9367610348}  # 18th is a saturday, last period to last pmt
    assert _pmts_between_dates(fixed_constant_amort_end_stub,
                                  datetime(2021, 12, 20),
                                  datetime(2021, 12, 20)) == {datetime(2021, 12, 20, 0, 0): 985930.9367610348}  # 18th is a saturday, last pmt to last pmt
    assert _pmts_between_dates(fixed_constant_amort_end_stub,
                               datetime(2021, 12, 1),
                               datetime(2021, 12, 10)) == {datetime(2021, 12, 1, 0, 0): 10906.441153481215,
                                                           datetime(2021, 12, 10, 0, 0): 983316.6021590831}  # period start (w prev period pmt on start) to middle of period
    assert _pmts_between_dates(fixed_constant_amort_end_stub,
                               datetime(2021, 5, 1),
                               datetime(2021, 6, 19)) == {datetime(2021, 5, 3, 0, 0): 10906.441153481215,
                                                          datetime(2021, 6, 1, 0, 0): 10906.441153481215,
                                                          datetime(2021, 6, 19, 0, 0): 991729.2851844121}  # period start (w prev period pmt on 3rd) to middle of following period


@pytest.fixture
def iterest_rate_provider_12_pct():
    # fixture for an object that returns est discount factors for 12% rate w act / 360 basis
    class RateProvider:

        def df(self, dt1, dt2):
            yf = actual360(dt1, dt2)
            return (1 + 0.12 / 360 * 365) ** - yf

    return RateProvider()


def test_defeasance_no_open(fixed_constant_amort_end_stub, iterest_rate_provider_12_pct):
    with pytest.raises(AttributeError):  # raises error if borrowing doesn't have all required attrs
        defeasance(fixed_constant_amort_end_stub, datetime(2020, 6, 5))
    fixed_constant_amort_end_stub.rate_provider = iterest_rate_provider_12_pct
    fixed_constant_amort_end_stub.open_dt_offset = None
    fixed_constant_amort_end_stub.dfz_to_open = False
    assert defeasance(fixed_constant_amort_end_stub, datetime(2020, 1, 1)) == pytest.approx(1007601.59018467)  # start date, full term
    assert defeasance(fixed_constant_amort_end_stub, datetime(2020, 7, 15)) == pytest.approx(1005258.99814295)  # dfz in middle of period
    assert defeasance(fixed_constant_amort_end_stub, datetime(2020, 8, 3)) == pytest.approx(1011369.07630207)  # dfz on pmt date
    assert defeasance(fixed_constant_amort_end_stub, datetime(2021, 12, 20)) == pytest.approx(985930.936761)  # final pmt date
    assert defeasance(fixed_constant_amort_end_stub, datetime(2019, 12, 31)) is None  # before start date
    assert defeasance(fixed_constant_amort_end_stub, datetime(2030, 1, 1)) is None  # after final pmt date


def test_defeasance_dfz_to_open_false(fixed_constant_amort_end_stub, iterest_rate_provider_12_pct):
    with pytest.raises(AttributeError):  # raises error if borrowing doesn't have all required attrs
        defeasance(fixed_constant_amort_end_stub, datetime(2020, 6, 5))
    fixed_constant_amort_end_stub.rate_provider = iterest_rate_provider_12_pct
    fixed_constant_amort_end_stub.open_dt_offset = relativedelta(months=2, days=17)
    fixed_constant_amort_end_stub.dfz_to_open = False
    assert defeasance(fixed_constant_amort_end_stub, datetime(2020, 1, 1)) == pytest.approx(1007601.59018467)  # start date, full term
    assert defeasance(fixed_constant_amort_end_stub, datetime(2020, 7, 15)) == pytest.approx(1005258.99814295)  # dfz in middle of period
    assert defeasance(fixed_constant_amort_end_stub, datetime(2020, 8, 1)) == pytest.approx(1010724.16521482)  # dfz on end dt with pmt date afer
    assert defeasance(fixed_constant_amort_end_stub, datetime(2020, 8, 3)) == pytest.approx(1011369.07630207)  # dfz on pmt date
    assert defeasance(fixed_constant_amort_end_stub, datetime(2021, 10, 1)) == pytest.approx(993130.478363)  # open start dt
    assert defeasance(fixed_constant_amort_end_stub, datetime(2021, 12, 20)) == pytest.approx(985930.936761)  # final pmt date
    assert defeasance(fixed_constant_amort_end_stub, datetime(2019, 12, 31)) is None  # before start date
    assert defeasance(fixed_constant_amort_end_stub, datetime(2030, 1, 1)) is None  # after final pmt date


def test_defeasance_dfz_to_open_true(fixed_constant_amort_end_stub, iterest_rate_provider_12_pct):
    with pytest.raises(AttributeError):  # raises error if borrowing doesn't have all required attrs
        defeasance(fixed_constant_amort_end_stub, datetime(2020, 6, 5))
    fixed_constant_amort_end_stub.rate_provider = iterest_rate_provider_12_pct
    fixed_constant_amort_end_stub.open_dt_offset = relativedelta(months=2, days=17)
    fixed_constant_amort_end_stub.dfz_to_open = True
    assert defeasance(fixed_constant_amort_end_stub, datetime(2020, 1, 1)) == pytest.approx(1007303.94552329)  # start date, full term
    assert defeasance(fixed_constant_amort_end_stub, datetime(2020, 7, 15)) == pytest.approx(1004942.1536422)  # dfz in middle of period
    assert defeasance(fixed_constant_amort_end_stub, datetime(2020, 8, 1)) == pytest.approx(1010405.59816482)  # dfz on end dt with pmt date afer
    assert defeasance(fixed_constant_amort_end_stub, datetime(2020, 8, 3)) == pytest.approx(1011050.30598452)  # dfz on pmt date
    assert defeasance(fixed_constant_amort_end_stub, datetime(2021, 10, 1)) == pytest.approx(993130.478363)  # open start dt
    assert defeasance(fixed_constant_amort_end_stub, datetime(2021, 11, 13)) == pytest.approx(991281.916885)  # open period non pmt date
    assert defeasance(fixed_constant_amort_end_stub, datetime(2021, 12, 19)) == pytest.approx(985930.936761)  # between end date and final pmt date
    assert defeasance(fixed_constant_amort_end_stub, datetime(2021, 12, 20)) == pytest.approx(985930.936761)  # final pmt date
    assert defeasance(fixed_constant_amort_end_stub, datetime(2019, 12, 31)) is None  # before start date
    assert defeasance(fixed_constant_amort_end_stub, datetime(2030, 1, 1)) is None  # after final pmt date