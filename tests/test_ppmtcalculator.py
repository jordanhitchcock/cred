import pytest
from datetime import datetime
from dateutil.relativedelta import relativedelta

from cred import FixedRateBorrowing, actual360, following, unadjusted, preceding, FederalReserveHolidays, Monthly, \
    thirty360
from cred.ppmtcalculator import OpenPrepayment, StepDown, Defeasance


@pytest.fixture
def fixed_constant_amort_end_stub_unadjusted():
    return FixedRateBorrowing(
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2021, 12, 18),
        freq=relativedelta(months=1),
        initial_principal=1_000_000.0,
        coupon=0.12,
        amort_periods=250,
        year_frac=actual360,
        holiday_calendar=FederalReserveHolidays(),
        pmt_convention=unadjusted
    )


@pytest.fixture
def fixed_constant_amort_end_stub_preceding():
    return FixedRateBorrowing(
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2021, 12, 18),
        freq=relativedelta(months=1),
        initial_principal=1_000_000.0,
        coupon=0.12,
        amort_periods=250,
        year_frac=actual360,
        holiday_calendar=FederalReserveHolidays(),
        pmt_convention=preceding
    )


@pytest.fixture
def fixed_constant_amort_end_stub_following():
    return FixedRateBorrowing(
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2021, 12, 18),
        freq=relativedelta(months=1),
        initial_principal=1_000_000.0,
        coupon=0.12,
        amort_periods=250,
        year_frac=actual360,
        holiday_calendar=FederalReserveHolidays(),
        pmt_convention=following
    )


# @pytest.fixture
# def iterest_rate_provider_12_pct():
#     # fixture for an object that returns est discount factors for 12% rate w act / 360 basis
#     class RateProvider:
#
#         def df(self, dt1, dt2):
#             yf = actual360(dt1, dt2)
#             return (1 + 0.12 / 360 * 365) ** - yf
#
#     return RateProvider()
#
#
# @pytest.fixture
# def dfz_calculator_no_open(iterest_rate_provider_12_pct):
#     dfz = DefeasanceCalculator(df_func=iterest_rate_provider_12_pct.df,
#                                open_dt_offset=None,
#                                dfz_to_open=None)
#     return dfz
#
#
# @pytest.fixture
# def dfz_calculator_dfz_to_open_false(iterest_rate_provider_12_pct):
#     dfz = DefeasanceCalculator(df_func=iterest_rate_provider_12_pct.df,
#                                open_dt_offset=relativedelta(months=2, days=17),
#                                dfz_to_open=False)
#     return dfz
#
#
# @pytest.fixture
# def dfz_calculator_dfz_to_open_true(iterest_rate_provider_12_pct):
#     dfz = DefeasanceCalculator(df_func=iterest_rate_provider_12_pct.df,
#                                open_dt_offset=relativedelta(months=2, days=17),
#                                dfz_to_open=True)
#     return dfz
#
#
# def test_pmts_between_dates(dfz_calculator_no_open, fixed_constant_amort_end_stub):
#     assert dfz_calculator_no_open._pmts_between_dates(fixed_constant_amort_end_stub,
#                                   datetime(2019, 1, 1),
#                                   datetime(2021, 12, 20)) == dict(fixed_constant_amort_end_stub.payments(pmt_dt=True))  # prior to closing date to last pmt
#     assert dfz_calculator_no_open._pmts_between_dates(fixed_constant_amort_end_stub,
#                                   datetime(2020, 1, 1),
#                                   datetime(2021, 12, 20)) == dict(fixed_constant_amort_end_stub.payments(pmt_dt=True))  # closing date to last pmt
#     assert dfz_calculator_no_open._pmts_between_dates(fixed_constant_amort_end_stub,
#                                   datetime(2021, 12, 15),
#                                   datetime(2021, 12, 20)) == {datetime(2021, 12, 20, 0, 0): 985930.9367610348}  # 18th is a saturday, last period to last pmt
#     assert dfz_calculator_no_open._pmts_between_dates(fixed_constant_amort_end_stub,
#                                   datetime(2021, 12, 20),
#                                   datetime(2021, 12, 20)) == {datetime(2021, 12, 20, 0, 0): 985930.9367610348}  # 18th is a saturday, last pmt to last pmt
#     assert dfz_calculator_no_open._pmts_between_dates(fixed_constant_amort_end_stub,
#                                datetime(2021, 12, 1),
#                                datetime(2021, 12, 10)) == {datetime(2021, 12, 1, 0, 0): 10906.441153481215,
#                                                            datetime(2021, 12, 10, 0, 0): 983316.6021590831}  # period start (w prev period pmt on start) to middle of period
#     assert dfz_calculator_no_open._pmts_between_dates(fixed_constant_amort_end_stub,
#                                datetime(2021, 5, 1),
#                                datetime(2021, 6, 19)) == {datetime(2021, 5, 3, 0, 0): 10906.441153481215,
#                                                           datetime(2021, 6, 1, 0, 0): 10906.441153481215,
#                                                           datetime(2021, 6, 19, 0, 0): 991729.2851844121}  # period start (w prev period pmt on 3rd) to middle of following period
#
#
# def test_defeasance_no_open(dfz_calculator_no_open, fixed_constant_amort_end_stub, iterest_rate_provider_12_pct):
#     assert dfz_calculator_no_open.repayment_amount(fixed_constant_amort_end_stub, datetime(2020, 1, 1)) == pytest.approx(1007601.59018467)  # start date, full term
#     assert dfz_calculator_no_open.repayment_amount(fixed_constant_amort_end_stub, datetime(2020, 7, 15)) == pytest.approx(1005258.99814295)  # dfz in middle of period
#     assert dfz_calculator_no_open.repayment_amount(fixed_constant_amort_end_stub, datetime(2020, 8, 3)) == pytest.approx(1011369.07630207)  # dfz on pmt date
#     assert dfz_calculator_no_open.repayment_amount(fixed_constant_amort_end_stub, datetime(2021, 12, 20)) == pytest.approx(985930.936761)  # final pmt date
#     assert dfz_calculator_no_open.repayment_amount(fixed_constant_amort_end_stub, datetime(2019, 12, 31)) is None  # before start date
#     assert dfz_calculator_no_open.repayment_amount(fixed_constant_amort_end_stub, datetime(2030, 1, 1)) is None  # after final pmt date
#
#
# def test_defeasance_dfz_to_open_false(dfz_calculator_dfz_to_open_false, fixed_constant_amort_end_stub, iterest_rate_provider_12_pct):
#     assert dfz_calculator_dfz_to_open_false.repayment_amount(fixed_constant_amort_end_stub, datetime(2020, 1, 1)) == pytest.approx(1007601.59018467)  # start date, full term
#     assert dfz_calculator_dfz_to_open_false.repayment_amount(fixed_constant_amort_end_stub, datetime(2020, 7, 15)) == pytest.approx(1005258.99814295)  # dfz in middle of period
#     assert dfz_calculator_dfz_to_open_false.repayment_amount(fixed_constant_amort_end_stub, datetime(2020, 8, 1)) == pytest.approx(1010724.16521482)  # dfz on end dt with pmt date afer
#     assert dfz_calculator_dfz_to_open_false.repayment_amount(fixed_constant_amort_end_stub, datetime(2020, 8, 3)) == pytest.approx(1011369.07630207)  # dfz on pmt date
#     assert dfz_calculator_dfz_to_open_false.repayment_amount(fixed_constant_amort_end_stub, datetime(2021, 10, 1)) == pytest.approx(993130.478363)  # open start dt
#     assert dfz_calculator_dfz_to_open_false.repayment_amount(fixed_constant_amort_end_stub, datetime(2021, 12, 20)) == pytest.approx(985930.936761)  # final pmt date
#     assert dfz_calculator_dfz_to_open_false.repayment_amount(fixed_constant_amort_end_stub, datetime(2019, 12, 31)) is None  # before start date
#     assert dfz_calculator_dfz_to_open_false.repayment_amount(fixed_constant_amort_end_stub, datetime(2030, 1, 1)) is None  # after final pmt date
#
#
# def test_defeasance_dfz_to_open_true(dfz_calculator_dfz_to_open_true, fixed_constant_amort_end_stub, iterest_rate_provider_12_pct):
#     assert dfz_calculator_dfz_to_open_true.repayment_amount(fixed_constant_amort_end_stub, datetime(2020, 1, 1)) == pytest.approx(1007303.94552329)  # start date, full term
#     assert dfz_calculator_dfz_to_open_true.repayment_amount(fixed_constant_amort_end_stub, datetime(2020, 7, 15)) == pytest.approx(1004942.1536422)  # dfz in middle of period
#     assert dfz_calculator_dfz_to_open_true.repayment_amount(fixed_constant_amort_end_stub, datetime(2020, 8, 1)) == pytest.approx(1010405.59816482)  # dfz on end dt with pmt date afer
#     assert dfz_calculator_dfz_to_open_true.repayment_amount(fixed_constant_amort_end_stub, datetime(2020, 8, 3)) == pytest.approx(1011050.30598452)  # dfz on pmt date
#     assert dfz_calculator_dfz_to_open_true.repayment_amount(fixed_constant_amort_end_stub, datetime(2021, 10, 1)) == pytest.approx(993130.478363)  # open start dt
#     assert dfz_calculator_dfz_to_open_true.repayment_amount(fixed_constant_amort_end_stub, datetime(2021, 11, 13)) == pytest.approx(991281.916885)  # open period non pmt date
#     assert dfz_calculator_dfz_to_open_true.repayment_amount(fixed_constant_amort_end_stub, datetime(2021, 12, 19)) == pytest.approx(985930.936761)  # between end date and final pmt date
#     assert dfz_calculator_dfz_to_open_true.repayment_amount(fixed_constant_amort_end_stub, datetime(2021, 12, 20)) == pytest.approx(985930.936761)  # final pmt date
#     assert dfz_calculator_dfz_to_open_true.repayment_amount(fixed_constant_amort_end_stub, datetime(2019, 12, 31)) is None  # before start date
#     assert dfz_calculator_dfz_to_open_true.repayment_amount(fixed_constant_amort_end_stub, datetime(2030, 1, 1)) is None  # after final pmt date


# Test Open Prepayment

@pytest.fixture
def open_ppmt_unpaid():
    return OpenPrepayment(period_breakage=None)


def test_open_ppmt_unpaid_unadjusted(open_ppmt_unpaid, fixed_constant_amort_end_stub_unadjusted):
    assert open_ppmt_unpaid.required_repayment(fixed_constant_amort_end_stub_unadjusted, datetime(2021, 1, 1)) == pytest.approx(1001496.082168)
    assert open_ppmt_unpaid.required_repayment(fixed_constant_amort_end_stub_unadjusted, datetime(2021, 8, 2)) == pytest.approx(984035.576856)


def test_open_ppmt_unpaid_preceding(open_ppmt_unpaid, fixed_constant_amort_end_stub_preceding):
    assert open_ppmt_unpaid.required_repayment(fixed_constant_amort_end_stub_preceding, datetime(2020, 10, 29)) == pytest.approx(992883.843693)
    assert open_ppmt_unpaid.required_repayment(fixed_constant_amort_end_stub_preceding, datetime(2020, 10, 30)) == pytest.approx(1003143.64341)
    assert open_ppmt_unpaid.required_repayment(fixed_constant_amort_end_stub_preceding, datetime(2020, 10, 31)) == pytest.approx(992237.202257)
    assert open_ppmt_unpaid.required_repayment(fixed_constant_amort_end_stub_preceding, datetime(2020, 11, 1)) == pytest.approx(992237.202257)
    assert open_ppmt_unpaid.required_repayment(fixed_constant_amort_end_stub_preceding, datetime(2021, 12, 18)) is None


def test_open_ppmt_unpaid_following(open_ppmt_unpaid, fixed_constant_amort_end_stub_following):
    assert open_ppmt_unpaid.required_repayment(fixed_constant_amort_end_stub_following, datetime(2021, 5, 2)) == pytest.approx(997433.171551)
    assert open_ppmt_unpaid.required_repayment(fixed_constant_amort_end_stub_following, datetime(2021, 5, 3)) == pytest.approx(997433.171551)
    assert open_ppmt_unpaid.required_repayment(fixed_constant_amort_end_stub_following, datetime(2021, 5, 4)) == pytest.approx(986526.730398)
    assert open_ppmt_unpaid.required_repayment(fixed_constant_amort_end_stub_following, datetime(2021, 12, 19)) == pytest.approx(985930.936761)
    assert open_ppmt_unpaid.required_repayment(fixed_constant_amort_end_stub_following, datetime(2021, 12, 20)) == pytest.approx(985930.936761)


def test_open_ppmt_unpaid_outside_dates(open_ppmt_unpaid, fixed_constant_amort_end_stub_unadjusted):
    assert open_ppmt_unpaid.required_repayment(fixed_constant_amort_end_stub_unadjusted, datetime(2019, 12, 31)) is None
    assert open_ppmt_unpaid.required_repayment(fixed_constant_amort_end_stub_unadjusted, datetime(2021, 12, 21)) is None


@pytest.fixture
def open_ppmt_accrued():
    return OpenPrepayment(period_breakage='accrued_and_unpaid')


def test_open_ppmt_accrued_unadjusted(open_ppmt_accrued,  fixed_constant_amort_end_stub_unadjusted):
    assert open_ppmt_accrued.required_repayment(fixed_constant_amort_end_stub_unadjusted, datetime(2021, 1, 1)) == pytest.approx(1001496.082168898)
    assert open_ppmt_accrued.required_repayment(fixed_constant_amort_end_stub_unadjusted, datetime(2021, 8, 2)) == pytest.approx(984363.588714952)


def test_open_ppmt_accrued_preceding(open_ppmt_accrued, fixed_constant_amort_end_stub_preceding):
    assert open_ppmt_accrued.required_repayment(fixed_constant_amort_end_stub_preceding, datetime(2020, 10, 29)) == pytest.approx(1002150.75956747)
    assert open_ppmt_accrued.required_repayment(fixed_constant_amort_end_stub_preceding, datetime(2020, 10, 30)) == pytest.approx(1003143.64341)
    assert open_ppmt_accrued.required_repayment(fixed_constant_amort_end_stub_preceding, datetime(2020, 10, 31)) == pytest.approx(992237.202257)
    assert open_ppmt_accrued.required_repayment(fixed_constant_amort_end_stub_preceding, datetime(2020, 11, 1)) == pytest.approx(992237.202257)
    assert open_ppmt_accrued.required_repayment(fixed_constant_amort_end_stub_preceding, datetime(2021, 12, 18)) == None


def test_open_ppmt_accrued_following(open_ppmt_accrued, fixed_constant_amort_end_stub_following):
    assert open_ppmt_accrued.required_repayment(fixed_constant_amort_end_stub_following, datetime(2021, 5, 2)) == pytest.approx(997762.013794466)
    assert open_ppmt_accrued.required_repayment(fixed_constant_amort_end_stub_following, datetime(2021, 5, 3)) == pytest.approx(998090.856037932)
    assert open_ppmt_accrued.required_repayment(fixed_constant_amort_end_stub_following, datetime(2021, 5, 4)) == pytest.approx(987513.257128398)
    assert open_ppmt_accrued.required_repayment(fixed_constant_amort_end_stub_following, datetime(2021, 12, 19)) == pytest.approx(985930.936761)
    assert open_ppmt_accrued.required_repayment(fixed_constant_amort_end_stub_following, datetime(2021, 12, 20)) == pytest.approx(985930.936761)


def test_open_ppmt_accrued_outside_dates(open_ppmt_accrued, fixed_constant_amort_end_stub_unadjusted):
    assert open_ppmt_accrued.required_repayment(fixed_constant_amort_end_stub_unadjusted, datetime(2019, 12, 31)) is None
    assert open_ppmt_accrued.required_repayment(fixed_constant_amort_end_stub_unadjusted, datetime(2021, 12, 21)) is None


@pytest.fixture
def open_ppmt_full_period():
    return OpenPrepayment(period_breakage='full_period')


def test_open_ppmt_full_period(open_ppmt_full_period,  fixed_constant_amort_end_stub_unadjusted):
    assert open_ppmt_full_period.required_repayment(fixed_constant_amort_end_stub_unadjusted, datetime(2021, 1, 1)) == pytest.approx(1001496.082169)
    assert open_ppmt_full_period.required_repayment(fixed_constant_amort_end_stub_unadjusted, datetime(2021, 8, 2)) == pytest.approx(994203.944484)


def test_open_ppmt_full_period_preceding(open_ppmt_full_period, fixed_constant_amort_end_stub_preceding):
    assert open_ppmt_full_period.required_repayment(fixed_constant_amort_end_stub_preceding, datetime(2020, 10, 29)) == pytest.approx(1003143.643411)
    assert open_ppmt_full_period.required_repayment(fixed_constant_amort_end_stub_preceding, datetime(2020, 10, 30)) == pytest.approx(1003143.64341)
    assert open_ppmt_full_period.required_repayment(fixed_constant_amort_end_stub_preceding, datetime(2020, 10, 31)) == pytest.approx(992237.202257)
    assert open_ppmt_full_period.required_repayment(fixed_constant_amort_end_stub_preceding, datetime(2020, 11, 1)) == pytest.approx(992237.202257)
    assert open_ppmt_full_period.required_repayment(fixed_constant_amort_end_stub_preceding, datetime(2021, 12, 18)) is None


def test_open_ppmt_full_period_following(open_ppmt_full_period, fixed_constant_amort_end_stub_following):
    assert open_ppmt_full_period.required_repayment(fixed_constant_amort_end_stub_following, datetime(2021, 5, 2)) == pytest.approx(1007627.281098)
    assert open_ppmt_full_period.required_repayment(fixed_constant_amort_end_stub_following, datetime(2021, 5, 3)) == pytest.approx(1007627.281098)
    assert open_ppmt_full_period.required_repayment(fixed_constant_amort_end_stub_following, datetime(2021, 5, 4)) == pytest.approx(996720.839945)
    assert open_ppmt_full_period.required_repayment(fixed_constant_amort_end_stub_following, datetime(2021, 12, 19)) == pytest.approx(985930.936761)
    assert open_ppmt_full_period.required_repayment(fixed_constant_amort_end_stub_following, datetime(2021, 12, 20)) == pytest.approx(985930.936761)


def test_open_ppmt_full_period_outside_dates(open_ppmt_full_period, fixed_constant_amort_end_stub_unadjusted):
    assert open_ppmt_full_period.required_repayment(fixed_constant_amort_end_stub_unadjusted, datetime(2019, 12, 31)) is None
    assert open_ppmt_full_period.required_repayment(fixed_constant_amort_end_stub_unadjusted, datetime(2021, 12, 21)) is None


# Step down penalties
@pytest.fixture
def stepdown_open():
    offsets = [Monthly(6), Monthly(10), Monthly(18)]
    premiums = [0.03, 0.02, 0.01]
    breakage = None
    return StepDown(expiration_offsets=offsets, premiums=premiums, period_breakage=breakage)


@pytest.fixture
def stepdown_no_open():
    offsets = [Monthly(6), Monthly(10), Monthly(16), Monthly(25)]
    premiums = [0.03, 0.02, 0.015, 0.01]
    breakage = None
    return StepDown(expiration_offsets=offsets, premiums=premiums, period_breakage=breakage)


def test_stepdown_unadjusted_open(fixed_constant_amort_end_stub_unadjusted, stepdown_open):
    assert stepdown_open.required_repayment(fixed_constant_amort_end_stub_unadjusted, datetime(2020, 3, 15)) == pytest.approx(1028127.02498053)  # middle of period
    assert stepdown_open.required_repayment(fixed_constant_amort_end_stub_unadjusted, datetime(2020, 4, 1)) == pytest.approx(1038423.81100298)  # on pmt date
    assert stepdown_open.required_repayment(fixed_constant_amort_end_stub_unadjusted, datetime(2021, 7, 1)) == pytest.approx(995672.542779)  # on expiration dt
    assert stepdown_open.required_repayment(fixed_constant_amort_end_stub_unadjusted, datetime(2021, 10, 15)) == pytest.approx(982224.037210)  # in open period


def test_stepdown_unadjusted_no_open(fixed_constant_amort_end_stub_unadjusted, stepdown_no_open):
    assert stepdown_no_open.required_repayment(fixed_constant_amort_end_stub_unadjusted, datetime(2021, 12, 18)) == pytest.approx(985930.936761)  # on maturity dt


def test_stepdown_unadjusted_outside_dates(fixed_constant_amort_end_stub_unadjusted, stepdown_no_open):
    assert stepdown_no_open.required_repayment(fixed_constant_amort_end_stub_unadjusted, datetime(2019, 12, 31)) is None
    assert stepdown_no_open.required_repayment(fixed_constant_amort_end_stub_unadjusted, datetime(2021, 12, 19)) is None


def test_stepdown_preceding_no_open(fixed_constant_amort_end_stub_preceding, stepdown_no_open):
    assert stepdown_no_open.required_repayment(fixed_constant_amort_end_stub_preceding, datetime(2020, 3, 15)) == pytest.approx(1028127.02498053)  # middle of period
    assert stepdown_no_open.required_repayment(fixed_constant_amort_end_stub_preceding, datetime(2020, 4, 1)) == pytest.approx(1038423.81100298)  # on pmt date
    assert stepdown_no_open.required_repayment(fixed_constant_amort_end_stub_preceding, datetime(2020, 10, 30)) == pytest.approx(1018027.201443855)  # on pmt date adj backwards
    assert stepdown_no_open.required_repayment(fixed_constant_amort_end_stub_preceding, datetime(2020, 10, 31)) == pytest.approx(1007120.760290855)  # bw pmt dt and end dt
    assert stepdown_no_open.required_repayment(fixed_constant_amort_end_stub_preceding, datetime(2020, 11, 1)) == pytest.approx(1007120.760290855)  # on end date with pmt adj back
    assert stepdown_no_open.required_repayment(fixed_constant_amort_end_stub_preceding, datetime(2021, 12, 17)) == pytest.approx(985930.936761)  # final pmt dt
    assert stepdown_no_open.required_repayment(fixed_constant_amort_end_stub_preceding, datetime(2021, 12, 18)) is None  # final end dt after final pmt dt


def test_stepdown_following_no_open(fixed_constant_amort_end_stub_following, stepdown_no_open):
    assert stepdown_no_open.required_repayment(fixed_constant_amort_end_stub_following, datetime(2020, 3, 15)) == pytest.approx(1028127.02498053)  # middle of period
    assert stepdown_no_open.required_repayment(fixed_constant_amort_end_stub_following, datetime(2020, 4, 1)) == pytest.approx(1038423.81100298)  # on pmt date
    assert stepdown_no_open.required_repayment(fixed_constant_amort_end_stub_following, datetime(2021, 5, 1)) == pytest.approx(1012246.5354849249)  # on end dt before pmt dt
    assert stepdown_no_open.required_repayment(fixed_constant_amort_end_stub_following, datetime(2021, 5, 2)) == pytest.approx(1012246.5354849249)  # bw end and pmt date
    assert stepdown_no_open.required_repayment(fixed_constant_amort_end_stub_following, datetime(2021, 5, 3)) == pytest.approx(1007298.4388549799)  # on pmt dt after end dt
    assert stepdown_no_open.required_repayment(fixed_constant_amort_end_stub_following, datetime(2021, 12, 19)) == pytest.approx(995734.69151832)  # after end dt before final pmt dt
    assert stepdown_no_open.required_repayment(fixed_constant_amort_end_stub_following, datetime(2021, 12, 20)) == pytest.approx(985930.936761)  # final pmt dt


# Test defeasance

@pytest.fixture
def df_func():
    def df(dt1, dt2):
        return (1 + 0.12 / 12) ** -thirty360(dt1, dt2)

    return df


@pytest.fixture
def dfz_no_open(df_func):
    return Defeasance(df_func=df_func, open_dt_offset=None)


@pytest.fixture
def dfz_to_maturity(df_func):
    return Defeasance(df_func=df_func, open_dt_offset=relativedelta(months=2, days=17), dfz_to_open=False)


@pytest.fixture
def dfz_to_open(df_func):
    return Defeasance(df_func=df_func, open_dt_offset=relativedelta(months=2, days=17), dfz_to_open=True)


def test_dfz_no_open(dfz_no_open, fixed_constant_amort_end_stub_following):
    assert dfz_no_open.required_repayment(fixed_constant_amort_end_stub_following, datetime(2020, 1, 1)) == pytest.approx(1215162.77051093)  # start date
    assert dfz_no_open.required_repayment(fixed_constant_amort_end_stub_following, datetime(2020, 4, 5)) == pytest.approx(1185574.85298199)  # middle of period
    assert dfz_no_open.required_repayment(fixed_constant_amort_end_stub_following, datetime(2020, 6, 1)) == pytest.approx(1176495.85286709)  # end dt on pmt date
    assert dfz_no_open.required_repayment(fixed_constant_amort_end_stub_following, datetime(2020, 8, 1)) == pytest.approx(1156608.52701895)  # end dt before pmt date
    assert dfz_no_open.required_repayment(fixed_constant_amort_end_stub_following, datetime(2020, 8, 3)) == pytest.approx(1156672.46566125)  # pmt date after end date
    assert dfz_no_open.required_repayment(fixed_constant_amort_end_stub_following, datetime(2021, 12, 18)) == pytest.approx(985876.436383954)  # end dt
    assert dfz_no_open.required_repayment(fixed_constant_amort_end_stub_following, datetime(2021, 12, 19)) == pytest.approx(985903.686195882)  # bw end and final pmt dt
    assert dfz_no_open.required_repayment(fixed_constant_amort_end_stub_following, datetime(2021, 12, 20)) == pytest.approx(985930.936761)  # on final pmt dt
    assert dfz_no_open.required_repayment(fixed_constant_amort_end_stub_following, datetime(2019, 12, 31)) is None  # before start date
    assert dfz_no_open.required_repayment(fixed_constant_amort_end_stub_following, datetime(2021, 12, 21)) is None  # after final pmt date


def test_dfz_to_maturity(dfz_to_maturity, fixed_constant_amort_end_stub_following):
    assert dfz_to_maturity.required_repayment(fixed_constant_amort_end_stub_following, datetime(2020, 1, 1)) == pytest.approx(1215162.77051093)  # start date
    assert dfz_to_maturity.required_repayment(fixed_constant_amort_end_stub_following, datetime(2020, 4, 5)) == pytest.approx(1185574.85298199)  # middle of period
    assert dfz_to_maturity.required_repayment(fixed_constant_amort_end_stub_following, datetime(2020, 6, 1)) == pytest.approx(1176495.85286709)  # end dt on pmt date
    assert dfz_to_maturity.required_repayment(fixed_constant_amort_end_stub_following, datetime(2020, 8, 1)) == pytest.approx(1156608.52701895)  # end dt before pmt date
    assert dfz_to_maturity.required_repayment(fixed_constant_amort_end_stub_following, datetime(2020, 8, 3)) == pytest.approx(1156672.46566125)  # pmt date after end date
    assert dfz_to_maturity.required_repayment(fixed_constant_amort_end_stub_following, datetime(2021, 10, 1)) == pytest.approx(993130.478363)  # open date
    assert dfz_to_maturity.required_repayment(fixed_constant_amort_end_stub_following, datetime(2021, 10, 2)) == pytest.approx(992373.685594)  # first day after open dt


def test_dfz_to_open(dfz_to_open, fixed_constant_amort_end_stub_following):
    assert dfz_to_open.required_repayment(fixed_constant_amort_end_stub_following, datetime(2020, 1, 1)) == pytest.approx(1192223.51736981)  # start date
    assert dfz_to_open.required_repayment(fixed_constant_amort_end_stub_following, datetime(2020, 4, 1)) == pytest.approx(1173353.8376713)  # period end date
    assert dfz_to_open.required_repayment(fixed_constant_amort_end_stub_following, datetime(2021, 10, 1)) == pytest.approx(993130.478363)  # open date
    assert dfz_to_open.required_repayment(fixed_constant_amort_end_stub_following, datetime(2021, 10, 2)) == pytest.approx(992373.685594)  # first day after open dt

