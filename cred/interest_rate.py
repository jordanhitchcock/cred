

class InterestRateProvider:
    """
    Returns the interest rate for the period.
    """

    def __init__(self, day_count=None, business_days=None, bd_adjustment=None):
        self.day_count = day_count
        self.business_days = business_days
        self.bd_adjustment = bd_adjustment

    def period_interest_rate(self, interest_period, **kwargs):
        raise NotImplementedError

    def year_frac(self, start, end):
        return 1 / 12


class FloatingRate(InterestRateProvider):

    def __init__(self, spread, day_count=None, business_days=None, bd_adjustment=None):
        super(InterestRateProvider, self).__init__(day_count=day_count,
                                                  business_days=business_days,
                                                  bd_adjustment=bd_adjustment)
        self.spread = spread

    def period_interest_rate(self, interest_period, **kwargs):

        try:
            curve = kwargs['curve']
        except KeyError:
            raise Exception('Must provide a "curve" assumption for floating rate loans.')

        year_frac = self.year_frac(interest_period.start_date, interest_period.end_date)
        index_rate = curve[interest_period.start_date]

        return (index_rate + self.spread) * year_frac


class FixedRate(InterestRateProvider):

    def __init__(self, coupon, day_count=None, business_days=None, bd_adjustment=None):
        super(InterestRateProvider, self).__init__(day_count=day_count,
                                                   business_days=business_days,
                                                   bd_adjustment=bd_adjustment)
        self.coupon = coupon

    def period_interest_rate(self, interest_period, **kwargs):
        return self.coupon * self.year_frac(interest_period.start_date, interest_period.end_date)


class InterestRate:
    pass
    # def __init__(self, spread):
    #     self.spread = spread
    #
    # def index_rate(self, period):
    #     fixing_date = period.start_date
    #     return self.curve[fixing_date]
    #
    # def rate(self, period):
    #     return self.index_rate(period) + self.spread