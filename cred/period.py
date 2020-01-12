from cred.interest_rate import actual360, thirty360


class Period:

    def __init__(self, id, start_date, end_date, previous_period, rules={}):  # Rules as collections.OrderedDict
        self.id = id
        self.start_date = start_date
        self.end_date = end_date
        self.previous_period = previous_period
        self.schedule = {}

        self.schedule['start_date'] = self.start_date
        self.schedule['end_date'] = self.end_date

        for name, func in rules.items():
            schedule_value = func(self)

            self.__setattr__(name, schedule_value)
            self.schedule[name] = schedule_value


# Principal functions
def bop_principal(initial_principal, eop_attr='eop_principal'):
    def bop_principal(period):
        if period.previous_period is not None:
            return period.previous_period.__getattribute__(eop_attr)
        return initial_principal

    return bop_principal


def eop_principal(bop_principal_attr='bop_principal', principal_pmt_attr=['principal']):
    def eop_principal(period):
        principal_pmts = 0
        for attr in principal_pmt_attr:
            amt = period.__getattribute__(attr)
            principal_pmts += amt

        return period.__getattribute__(bop_principal_attr) - principal_pmts

    return eop_principal


def interest_only(maturity_date, bop_principal_attr='bop_principal'):
    def principal_pmt(period):
        if period.end_date == maturity_date:
            return period.__getattribute__(bop_principal_attr)

        return 0

    return principal_pmt


# Interest functions
def fixed_interest_rate(coupon):
    def interest_rate(period):
        return coupon

    return interest_rate


def interest_pmt(yearfrac_method=actual360, bop_principal_attr='bop_principal', interest_rate_attr='interest_rate'):
    def interest(period):
        yearfrac = yearfrac_method(period.start_date, period.end_date)
        return period.__getattribute__(bop_principal_attr) * yearfrac * period.__getattribute__(interest_rate_attr)

    return interest

