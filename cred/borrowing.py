from collections import OrderedDict
from dateutil.relativedelta import relativedelta

from pandas import DataFrame, Series

from cred.businessdays import unadjusted_schedule
from cred.interest_rate import actual360, thirty360
from cred.period import Period, adj_date, fixed_interest_rate, interest_pmt, bop_principal, eop_principal, interest_only, floating_interest_rate
from cred.period import START_DATE, END_DATE, ADJ_END_DATE, BOP_PRINCIPAL, EOP_PRINCIPAL, PRINCIPAL_PAYMENT, INDEX_RATE, INTEREST_RATE, INTEREST_PAYMENT


def open_repayment(borrowing, date):
    return borrowing.outstanding_principal(date)


def percent_of_principal(dates, percentages):
    """ Return outstanding principal plus the given percentage. Ending stubs will default to open repayment."""
    thresholds = Series(percentages, index=dates)
    thresholds.sort_index(ascending=True)

    def repayment(borrowing, date):
        outstanding_balance = open_repayment(borrowing, date)

        if date > max(dates):
            return outstanding_balance

        i = thresholds.index.get_loc(date, method='bfill')
        return outstanding_balance * (1 + thresholds[i])
    return repayment


def yield_maintenance(rate_provider, wal=False, spread=0, day_count_method=actual360):
    """
    Yield maintenance function factory.
    :param rate_provider: Function that takes two datetime and returns the discount rate
    :type rate_provider: function
    :param wal: True if the discount rate should be based on remaining weight average life, False if it should be calculated on remaining term (default)
    :type wal: bool
    :param spread: Spread to add to the discount rate
    :type spread: float
    :param day_count_method: Function for calculating year fractions for discount factors, default is actual / 360
    :type day_count_method: function
    :return: function
    """
    def pv(borrowing, exit_date):
        remaining_cf = borrowing.remaining_cash_flow(exit_date, include_date=True, attrs=[END_DATE, INTEREST_PAYMENT, PRINCIPAL_PAYMENT])

        remaining_pmt_dates = remaining_cf.pop(END_DATE)
        remaining_cf = Series(remaining_cf.sum(axis=1).values, index=remaining_pmt_dates)
        if wal:
            remaining_days = [(dt - exit_date).days for dt in remaining_pmt_dates]
            remaining_days = sum(remaining_days) / len(remaining_days)
        else:
            remaining_days = (remaining_pmt_dates.iloc[-1] - exit_date).days

        discount_rate = rate_provider(exit_date, exit_date + relativedelta(days=remaining_days)) + spread
        year_fracs = [day_count_method(exit_date, dt) for dt in remaining_pmt_dates]
        discount_factors = [(1 / ((1 + discount_rate) ** yf)) for yf in year_fracs]

        return sum([amt * df for amt, df in zip(remaining_cf, discount_factors)])

    return pv


def defeasance(rate_provider, day_count=thirty360):
    """
    Factory for defeasance repayment functions.
    :param rate_provider: Function that takes two datetime and returns a float for the discount rate
    :type rate_provider: function
    :param day_count: Day count function for building discount factors, default is 30/360
    :type day_count: function
    :return: function
    """
    def pv(borrowing, exit_date):
        remaining_cf = borrowing.remaining_cash_flow(exit_date, include_date=True,
                                                     attrs=[END_DATE, INTEREST_PAYMENT, PRINCIPAL_PAYMENT])

        remaining_pmt_dates = remaining_cf.pop(END_DATE)
        remaining_cf = Series(remaining_cf.sum(axis=1).values, index=remaining_pmt_dates)

        discout_factors = []
        for dt in remaining_pmt_dates:
            discout_factors.append(1/(1 + rate_provider(exit_date, dt)) ** day_count(exit_date, dt))

        return sum([amt * df for amt, df in zip(remaining_cf, discout_factors)])

    return pv


class Borrowing:

    def __init__(self, dates, period_rules):
        """
        Base level Borrowing class. Custom Borrowing classes should subclass Borrowing.

        :param dates: List of (start date, end date) for periods
        :type dates: list
        :param period_rules: OrderedDict of name, function rules passed to Period
        :type period_rules: OrderedDict
        """
        self.dates = dates
        self.period_rules = period_rules

    def schedule(self):
        """ Build Periods and returns a DataFrame of aggregated Period.schedule."""
        i = 1
        periods = []

        for start, end in self.dates:
            if len(periods) == 0:
                previous_period = None
            else:
                previous_period = periods[-1]

            periods.append(Period(i, start, end, previous_period, rules=self.period_rules))

            i += 1

        schedules = [period.schedule for period in periods]

        return DataFrame(schedules)

    def scheduled_cash_flow(self, attr_names, start_date=None, end_date=None):
        """ Return cash flows for attribute name(s) with optional start and end dates. attr_names can
        either be a string or list of names. Returns Series or DataFrame depending on number of attr_names.
        """
        schedule = self.schedule()

        if start_date is not None:
            schedule = schedule[schedule[START_DATE] >= start_date]
        if end_date is not None:
            schedule = schedule[schedule[END_DATE] <= end_date]
        # if start_date is not None:
        #     if end_date is not None:
        #         schedule = schedule[schedule[START_DATE] >= start_date]
        #         schedule = schedule[schedule[END_DATE] <= end_date]
        #     else:
        #         schedule = schedule[schedule[START_DATE] == start_date]
        # elif end_date is not None:
        #     schedule = schedule[schedule[END_DATE] == end_date]
        #
        return schedule[attr_names]


class PeriodicBorrowing(Borrowing):

    def __init__(self, initial_principal, start_date, frequency, first_regular_date=None, periods=None, end_date=None, period_rules=None):
        """
        Generic Borrowing type with periods of the same frequency.
        Must provide one of periods or end_date but not both.
        :param initial_principal: Initial principal
        :type initial_principal: int, float
        :param start_date: Borrowing start date
        :type start_date: datetime
        :param frequency: Interest period frequency
        :type frequency: dateutil.relativedelta
        :param first_regular_date: Starting date of first regular period, or None if the same as start_date
        :type first_regular_date: datetime, None
        :param periods: Number of periods, or None if end_date is used
        :type periods: int, None
        :param end_date: Maturity date, or None if periods is used
        :type end_date: datetime, None
        :param period_rules: OrderedDict of rules to create Period schedules
        :type period_rules: OrderedDict({str: func})
        """
        if periods is None and end_date is None:
            raise Exception('Must provide either the number of periods or the end date.')
        if periods is not None and end_date is not None:
            raise Exception('Cannot provide both the numbers of periods and an end date.')

        self.initial_principal = initial_principal
        self.start_date = start_date
        self.frequency = frequency
        if first_regular_date is None:
            self.first_regular_date = start_date
        else:
            self.first_regular_date = first_regular_date
        self.periods = periods
        if end_date is None:
            self.end_date = self.first_regular_date + self.frequency * self.periods
        else:
            self.end_date = end_date
        self.period_rules = period_rules

        period_dates = []
        if self.start_date != self.first_regular_date:
            period_dates.append((self.start_date, self.end_date))
        period_dates = period_dates + unadjusted_schedule(self.first_regular_date, end_date, frequency)

        super().__init__(period_dates, period_rules=self.period_rules)

    def repayment_amount(self, date):
        """ Calculate loan repayment costs for date. Should be implemented by subclasses."""
        raise NotImplementedError('PeriodicBorrowing.repayment_amount not implemented in {} subclass.'.format(self.__class__))

    def net_cash_flows(self, exit_date, pmt_attrs=[INTEREST_PAYMENT, PRINCIPAL_PAYMENT]):
        """
        Return net cash flows through exit_date, including initial principal and loan repayment costs.
        :param exit_date: Date of repayment
        :type exit_date: datetime
        :param pmt_attrs: List of schedule series to sum as periodic cash flows, default is interest and amortization.
        :type pmt_attrs: list
        :return: Net cash flows
        :rtype: pandas.Series
        """
        pmts = self.scheduled_cash_flow(pmt_attrs, start_date=self.start_date, end_date=exit_date).sum(axis=1)
        repayment_amt = self.repayment_amount(exit_date)
        return Series([-self.initial_principal] + pmts.to_list() + [repayment_amt])

    def outstanding_principal(self, date):
        """ Return the outstanding principal balance for a given date."""
        if (date < self.start_date) or (date > self.end_date):
            raise IndexError('Date is outside borrowing dates.')

        if date == self.start_date:
            return self.initial_principal

        schedule = self.schedule().set_index(END_DATE)

        i = schedule.index.get_loc(date, method='ffill')
        return schedule[EOP_PRINCIPAL][i]

    def remaining_cash_flow(self, date, include_date=True, attrs=[INTEREST_PAYMENT, PRINCIPAL_PAYMENT]):
        """ Return remaining cash flows through borrowing end date, optionally excluding any cash flows on date of evaluation."""
        schedule = self.schedule()
        if include_date:
            return schedule.loc[schedule[END_DATE] >= date, attrs]
        else:
            return schedule.loc[schedule[END_DATE] > date, attrs]


class FixedRateBorrowing(PeriodicBorrowing):

    def __init__(self, start_date, end_date, coupon, initial_principal, amort=None, frequency=relativedelta(months=1),
                 repayment=None, **kwargs):
        """
        Borrowing subclass for fixed rate debt.

        :param start_date: Borrowing start date
        :type start_date: datetime
        :param end_date: Borrowing end date
        :type end_date: datetime
        :param coupon: Coupon rate
        :type coupon: float
        :param initial_principal: Initial principal amount
        :type initial_principal: float, int
        :param amort: Amortization rule or None (default), if None then interest only.
        :type amort: func, None
        :param frequency: Period frequency, defaults to monthly
        :type frequency: dateutil.relativedelta
        :param repayment: Repayment method
        :type repayment: func
        """
        self.coupon = coupon
        self.initial_principal = initial_principal
        self.repayment_amount = repayment.__get__(self)

        rules = OrderedDict()
        rules[BOP_PRINCIPAL] = bop_principal(initial_principal)
        rules[INTEREST_RATE] = fixed_interest_rate(coupon)
        rules[INTEREST_PAYMENT] = interest_pmt(kwargs.get('day_count', actual360))
        if amort is None:
            rules[PRINCIPAL_PAYMENT] = interest_only(end_date)
        else:
            rules[PRINCIPAL_PAYMENT] = amort
        rules[EOP_PRINCIPAL] = eop_principal()

        super().__init__(initial_principal, start_date, frequency, end_date=end_date, period_rules=rules)


class FloatingRateBorrowing(PeriodicBorrowing):

    def __init__(self, start_date, end_date, spread, index_rate_provider, initial_principal,
                 frequency=relativedelta(months=1), repayment=open_repayment, **kwargs):
        """
        Borrowing subclass for floating rate borrowings. The index_rate_provider should be a function that takes one
        datetime argument and returns a the appropriate index rate.

        :param start_date: Borrowing start date
        :type start_date: datetime
        :param end_date: Borrowing end date
        :type end_date: datetime
        :param spread: Borrowing interest rate spread
        :type spread: float
        :param index_rate_provider: function that takes a datetime as the only argument and returns the index rate
        :type index_rate_provider: function
        :param initial_principal: Initial principal balance
        :type initial_principal: float, int
        :param frequency: Period frequency, defaults to monthly
        :type frequency: dateutil.relativedelta
        :param repayment: Repayment method, default is open
        :type repayment: func
        """
        self.spread = spread
        self.index_rate_provider = index_rate_provider
        self.repayment_amount = repayment.__get__(self)

        rules = OrderedDict()
        rules[BOP_PRINCIPAL] = bop_principal(initial_principal)
        rules[INDEX_RATE] = self.index_rate_provider
        rules[INTEREST_RATE] = floating_interest_rate(self.spread)
        rules[INTEREST_PAYMENT] = interest_pmt(kwargs.get('day_count', actual360))
        rules[PRINCIPAL_PAYMENT] = interest_only(end_date)
        rules[EOP_PRINCIPAL] = eop_principal()

        super().__init__(initial_principal, start_date, frequency, end_date=end_date, period_rules=rules)

