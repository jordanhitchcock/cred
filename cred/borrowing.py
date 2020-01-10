from collections import OrderedDict

from pandas import DataFrame

from cred.period import Period, fixed_interest_rate, interest_pmt, bop_principal, eop_principal, interest_only
from cred.businessdays import unadjusted_schedule


class Borrowing:
    def __init__(self, start, end, frequency, period_rules):
        self.start = start
        self.end = end
        self.frequency = frequency
        self.period_rules = period_rules

    def schedule(self):
        unadj_dates = unadjusted_schedule(self.start, self.end, self.frequency)
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

    def __init__(self, start, end, frequency, coupon, initial_principal):
        self.coupon = coupon
        self.initial_principal = initial_principal

        rules = OrderedDict()
        rules['bop_principal'] = bop_principal(initial_principal)
        rules['interest_rate'] = fixed_interest_rate(coupon)
        rules['interest_pmt'] = interest_pmt()
        rules['principal'] = interest_only(end)
        rules['eop_principal'] = eop_principal()

        super().__init__(start, end, frequency, period_rules=rules)


