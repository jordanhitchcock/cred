

class Period:

    def __init__(self, id, start, end, previous_period, rules={}):  # Rules as collections.OrderedDict
        self.id = id
        self.start = start
        self.end = end
        self.previous_period = previous_period
        self.schedule = {}

        self.schedule['start_date'] = self.start
        self.schedule['end_date'] = self.end

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
        if period.end == maturity_date:
            return period.__getattribute__(bop_principal_attr)

        return 0

    return principal_pmt


# Interest functions
def fixed_interest_rate(coupon):
    def interest_rate(period):
        return coupon

    return interest_rate


def interest_pmt(yearfrac='actual360', bop_principal_attr='bop_principal', interest_rate_attr='interest_rate'):
    def interest(period):
        yearfrac = (period.end - period.start).days / 360
        return period.__getattribute__(bop_principal_attr) * yearfrac * period.__getattribute__(interest_rate_attr)

    return interest

