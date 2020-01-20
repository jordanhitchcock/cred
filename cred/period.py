from dateutil.relativedelta import relativedelta
from pandas.tseries.holiday import AbstractHolidayCalendar, HolidayCalendarFactory

from cred.interest_rate import actual360, thirty360
from cred.businessdays import FederalReserveHolidays, LondonBankHolidays, modified_following


START_DATE = 'start_date'
END_DATE = 'end_date'
ADJ_START_DATE = 'adj_start_date'
ADJ_END_DATE = 'adj_end_date'
BOP_PRINCIPAL = 'bop_principal'
EOP_PRINCIPAL = 'eop_principal'
PRINCIPAL_PAYMENT = 'principal_payment'
INTEREST_RATE = 'interest_rate'
INTEREST_PAYMENT = 'interest_payment'
INDEX_RATE = 'index_rate'


class Period:

    def __init__(self, id, start_date, end_date, previous_period, rules={}):  # Rules as collections.OrderedDict
        self.id = id
        self.start_date = start_date
        self.end_date = end_date
        self.previous_period = previous_period
        self.schedule = {}

        self.schedule[START_DATE] = self.start_date
        self.schedule[END_DATE] = self.end_date

        for name, func in rules.items():
            schedule_value = func(self)

            self.__setattr__(name, schedule_value)
            self.schedule[name] = schedule_value


# Date functions
def adj_date(unadj_date_attr, calendars=[FederalReserveHolidays, LondonBankHolidays], convention=modified_following):
    """
    Factory to create a Period rule that returns date adjusted for calendar holidays based on the convention for date at the specified Period attribute.

    :param unadj_date_attr: Name of unadjusted Period date attribute
    :type unadj_date_attr: str
    :param calendars: List of Pandas HolidayCalendars
    :type calendars: list
    :param convention: Adjustment convention
    :type convention: func
    :return: A Period rule function for adjusted date
    """
    holiday_cal = calendars[0]
    if len(calendars) > 0:

        for additional_cal in calendars:
            holiday_cal = HolidayCalendarFactory(holiday_cal.__name__ + additional_cal.__name__, holiday_cal, additional_cal)

    def adj_func(period):
        unadj_date = period.__getattribute__(unadj_date_attr)

        return modified_following(unadj_date, holiday_cal())

    return adj_func


# Principal functions
def bop_principal(initial_principal, eop_attr=EOP_PRINCIPAL):
    def bop_principal(period):
        if period.previous_period is not None:
            return period.previous_period.__getattribute__(eop_attr)
        return initial_principal

    return bop_principal


def eop_principal(bop_principal_attr=BOP_PRINCIPAL, principal_pmt_attr=[PRINCIPAL_PAYMENT]):
    def eop_principal(period):
        principal_pmts = 0
        for attr in principal_pmt_attr:
            amt = period.__getattribute__(attr)
            principal_pmts += amt

        return period.__getattribute__(bop_principal_attr) - principal_pmts

    return eop_principal


def interest_only(maturity_date, bop_principal_attr=BOP_PRINCIPAL):
    def principal_pmt(period):
        if period.end_date == maturity_date:
            return period.__getattribute__(bop_principal_attr)

        return 0

    return principal_pmt


def constant_pmt_amort(amort_start,
                       maturity_date,
                       amort_periods,
                       freq,
                       annual_rate,
                       initial_principal,
                       fv=0,
                       interest_attr=INTEREST_PAYMENT,
                       bop_principal_attr=BOP_PRINCIPAL):
    """
    Factory for constant payment amortization Period rules.

    :param amort_start: First unadjusted amortization payment date, payments before this date are interest only
    :type amort_start: datetime
    :param maturity_date: Borrowing maturity date
    :type maturity_date: datetime
    :param amort_periods: Total amortization periods
    :type amort_periods: int
    :param freq: Amortization payment frequency
    :type freq: relativedelta
    :param annual_rate: Annual interest rate for calculating payment amount
    :type annual_rate: float
    :param initial_principal: Initial principal
    :type initial_principal: int, float
    :param fv: Future value
    :type fv: int, float
    :param interest_attr: Name of interest payment attribute, defaults to interest
    :type interest_attr: str
    :param bop_principal_attr: Beginning of period principal attribute name, default to bop_principal
    :type bop_principal_attr: str
    :return: func
    """
    yearfac = ((freq.years * 360) + (freq.months * 30) + freq.days) / 360
    periodic_rate = annual_rate * yearfac
    pmt = (initial_principal - fv) * (periodic_rate + (periodic_rate / ((1 + periodic_rate) ** amort_periods - 1)))

    def principal_pmt(period):
        if period.end_date == maturity_date:
            return period.__getattribute__(bop_principal_attr)
        elif period.end_date < amort_start:
            return 0
        return pmt - period.__getattribute__(interest_attr)

    return principal_pmt


# Interest functions
def fixed_interest_rate(coupon):
    """
    Factory for fixed rate Period rules.

    :param coupon: Coupon rate
    :type coupon: float
    :return: Period rule function for the coupon rate
    """
    def interest_rate(period):
        return coupon

    return interest_rate


def interest_pmt(yearfrac_method=actual360, bop_principal_attr=BOP_PRINCIPAL, interest_rate_attr=INTEREST_RATE):
    """
    Factory for interest payment Period rules.

    :param yearfrac_method: Day count convention, defaults to `actual360`
    :type yearfrac_method: function
    :param bop_principal_attr: Beginning of period principal balance attribute name, defaults to "bop_principal"
    :type bop_principal_attr: str
    :param interest_rate_attr: Interest rate attribute name, defaults to "interest_rate"
    :type interest_rate_attr: str
    :return: Returns a function to be used as a Period rule for interest payments
    """
    def interest(period):
        yearfrac = yearfrac_method(period.start_date, period.end_date)
        return period.__getattribute__(bop_principal_attr) * yearfrac * period.__getattribute__(interest_rate_attr)

    return interest


def floating_interest_rate(spread, index_rate_attr=INDEX_RATE):
    """
    Factory for floating interest rate (spread plus index rate) Period rules.

    :param spread: Loan spread
    :type spread: float
    :param index_rate_attr: Index rate rule name
    :type index_rate_attr: str
    :return: Returns a function to be used as a Period rule for the interest rate (index plus spread)
    """
    def interest_rate(period):
        return period.__getattribute__(index_rate_attr) + spread

    return interest_rate
