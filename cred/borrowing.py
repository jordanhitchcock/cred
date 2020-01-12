from collections import OrderedDict

from pandas import DataFrame

from cred.period import Period, adj_date, fixed_interest_rate, interest_pmt, bop_principal, eop_principal, interest_only, index_rate, floating_interest_rate
from cred.period import ADJ_START_DATE, ADJ_END_DATE, BOP_PRINCIPAL, EOP_PRINCIPAL, PRINCIPAL_PAYMENT, INDEX_RATE, INTEREST_RATE, INTEREST_PAYMENT
from cred.businessdays import unadjusted_schedule


class Borrowing:
    def __init__(self, start_date, end_date, frequency, period_rules):
        """
        Base level Borrowing class. Custom Borrowing classes should subclass Borrowing.

        :param start_date: Borrowing start date
        :type start_date: datetime
        :param end_date: Borrowing end date
        :type end_date: datetime
        :param frequency: Period frequency
        :type frequency: dateutil.relativedelta
        :param period_rules: OrderedDict of name, function rules passed to Periods
        :type period_rules: OrderedDict
        """
        self.start_date = start_date
        self.end_date = end_date
        self.frequency = frequency
        self.period_rules = period_rules

    def schedule(self):
        unadj_dates = unadjusted_schedule(self.start_date, self.end_date, self.frequency)
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


class FixedRateBorrowing(Borrowing):

    def __init__(self, start_date, end_date, frequency, coupon, initial_principal):
        """
        Borrowing sublcass for fixed rate debt.

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
        """
        self.coupon = coupon
        self.initial_principal = initial_principal

        rules = OrderedDict()
        rules[ADJ_START_DATE] = adj_date('start_date')
        rules[ADJ_END_DATE] = adj_date('end_date')
        rules[BOP_PRINCIPAL] = bop_principal(initial_principal)
        rules[INTEREST_RATE] = fixed_interest_rate(coupon)
        rules[INTEREST_PAYMENT] = interest_pmt()
        rules[PRINCIPAL_PAYMENT] = interest_only(end_date)
        rules[EOP_PRINCIPAL] = eop_principal()

        super().__init__(start_date, end_date, frequency, period_rules=rules)


class FloatingRateBorrowing(Borrowing):

    def __init__(self, start_date, end_date, frequency, spread, index_rate_provider, initial_principal):
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

        rules = OrderedDict()
        rules[ADJ_START_DATE] = adj_date('start_date')
        rules[ADJ_END_DATE] = adj_date('end_date')
        rules[BOP_PRINCIPAL] = bop_principal(initial_principal)
        rules[INDEX_RATE] = index_rate(self.index_rate_provider)
        rules[INTEREST_RATE] = floating_interest_rate(self.spread)
        rules[INTEREST_PAYMENT] = interest_pmt()
        rules[PRINCIPAL_PAYMENT] = interest_only(end_date)
        rules[EOP_PRINCIPAL] = eop_principal()

        super().__init__(start_date, end_date, frequency, period_rules=rules)

