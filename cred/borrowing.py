from collections import OrderedDict

from pandas import DataFrame

from cred.businessdays import unadjusted_schedule
from cred.interest_rate import actual360, thirty360
from cred.period import Period, adj_date, fixed_interest_rate, interest_pmt, bop_principal, eop_principal, interest_only, index_rate, floating_interest_rate
from cred.period import START_DATE, END_DATE, ADJ_END_DATE, BOP_PRINCIPAL, EOP_PRINCIPAL, PRINCIPAL_PAYMENT, INDEX_RATE, INTEREST_RATE, INTEREST_PAYMENT


class AbstractBorrowing:
    # TODO: clean up date inputs
    def __init__(self, start_date, frequency, end_date=None, periods=None, first_reg_date=None, period_rules=None):
        """
        Base level Borrowing class. Custom Borrowing classes should subclass Borrowing.

        :param start_date: Borrowing start date
        :type start_date: datetime
        :param end_date: Borrowing end date
        :type end_date: datetime
        :param frequency: Period frequency
        :type frequency: dateutil.relativedelta
        :param first_reg_date: Starting date of the first regular period, pass None if it's the same as the start_date (default)
        :type first_reg_date: None, datetime
        :param period_rules: OrderedDict of name, function rules passed to Periods
        :type period_rules: OrderedDict
        """
        if end_date is None and periods is None:
            raise Exception('Requires either the end date or number of periods.')
        if end_date is not None and periods is not None:
            raise Exception('Cannot provide both and end date and number of periods.')

        self.start_date = start_date
        self.frequency = frequency
        self.period_rules = period_rules
        if first_reg_date is None:
            self.first_reg_date = start_date
        else:
            self.first_reg_date = first_reg_date
        self.end_date = end_date
        if periods is not None:
            self.end_date = (first_reg_date + frequency * periods) - (start_date != self.first_reg_date)
        self.periods = periods

    def calc_period_dates(self):
        """ Return a list of (start date, end date) for each period."""
        dates = []
        if self.start_date != self.first_reg_date:
            dates.append((self.start_date, self.first_reg_date))
        return dates + unadjusted_schedule(self.first_reg_date, self.end_date, self.frequency)

    def schedule(self):
        """ Build Periods and returns a DataFrame of aggregated Period.schedule."""
        unadj_dates = self.calc_period_dates()
        i = 1
        periods = []

        for start, end in unadj_dates:
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
        either be a string or list of names. Returns Series if one cash flow or DataFrame if more than one.
        """
        schedule = self.schedule()

        if start_date is not None:
            schedule = schedule[schedule[START_DATE] >= start_date]
        if end_date is not None:
            schedule = schedule[schedule[END_DATE] <= end_date]

        return schedule[attr_names]


class PeriodicBorrowing(AbstractBorrowing):

    def __init__(self, initial_principal, *args, **kwargs):
        super().__init__(args, kwargs)
        self.initial_principal = initial_principal


class FixedRateBorrowing(AbstractBorrowing):

    def __init__(self, start_date, end_date, frequency, coupon, initial_principal, amort=None, **kwargs):
        """
        Borrowing subclass for fixed rate debt.

        :param start_date: Borrowing start date
        :type start_date: datetime
        :param end_date: Borrowing end date
        :type end_date: datetime
        :param frequency: Period frequency, defaults to monthly
        :type frequency: dateutil.relativedelta
        :param coupon: Coupon rate
        :type coupon: float
        :param initial_principal: Initial principal amount
        :type initial_principal: float, int
        :param amort: Amortization rule or None (default), if None then interest only.
        :type amort: func, None
        """
        self.coupon = coupon
        self.initial_principal = initial_principal

        rules = OrderedDict()
        # rules[ADJ_START_DATE] = adj_date('start_date')
        # rules[ADJ_END_DATE] = adj_date('end_date')
        rules[BOP_PRINCIPAL] = bop_principal(initial_principal)
        rules[INTEREST_RATE] = fixed_interest_rate(coupon)
        rules[INTEREST_PAYMENT] = interest_pmt(kwargs.get('day_count', actual360))
        if amort is None:
            rules[PRINCIPAL_PAYMENT] = interest_only(end_date)
        else:
            rules[PRINCIPAL_PAYMENT] = amort
        rules[EOP_PRINCIPAL] = eop_principal()

        super().__init__(initial_principal, start_date, frequency, end_date=end_date, period_rules=rules)


class FloatingRateBorrowing(AbstractBorrowing):
    # TODO document kwargs, add to other borrowings
    def __init__(self, start_date, end_date, frequency, spread, index_rate_provider, initial_principal, **kwargs):
        """
        Borrowing subclass for floating rate borrowings. The index_rate_provider should be an object that provides the
        applicable rate when obj.rate(datetime) is called.

        :param start_date: Borrowing start date
        :type start_date: datetime
        :param end_date: Borrowing end date
        :type end_date: datetime
        :param frequency: Period frequency, defaults to monthly
        :type frequency: dateutil.relativedelta
        :param spread: Borrowing interest rate spread
        :type spread: float
        :param index_rate_provider: Object that provides index rates when obj.rate(datetime) is called
        :type index_rate_provider: object
        :param initial_principal: Initial principal balance
        :type initial_principal: float, int
        """
        self.spread = spread
        self.index_rate_provider = index_rate_provider
        self.initial_principal = initial_principal

        rules = OrderedDict()
        # rules[ADJ_START_DATE] = adj_date('start_date')
        # rules[ADJ_END_DATE] = adj_date('end_date')
        rules[BOP_PRINCIPAL] = bop_principal(initial_principal)
        rules[INDEX_RATE] = index_rate(self.index_rate_provider)
        rules[INTEREST_RATE] = floating_interest_rate(self.spread)
        rules[INTEREST_PAYMENT] = interest_pmt(kwargs.get('day_count', actual360))
        rules[PRINCIPAL_PAYMENT] = interest_only(end_date)
        rules[EOP_PRINCIPAL] = eop_principal()

        super().__init__(start_date, frequency, end_date=end_date, period_rules=rules)

