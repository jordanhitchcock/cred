

class AbstractInterestPeriod:

    def __init__(self, period_id, period_start_date=None, period_end_date=None):
        self.period_id = period_id
        self.period_start_date = period_start_date
        self.period_end_date = period_end_date


class ScheduleBuilder:

    def __init__(self, interest_rate_provider, principal_payment_provider, initial_principal, periods, start_date=None, end_date=None):
        self.periods = periods
        # TODO: make it so you can provide either number of periods or start/end/roll dates
        self.interest_periods = self.create_interest_periods()
        self.interest_rate_provider = interest_rate_provider
        self.principal_payment_provider = principal_payment_provider
        self.initial_principal = initial_principal

    def create_interest_periods(self):
        new_periods = []
        for period in range(1, self.periods + 1):
            new_periods.append(AbstractInterestPeriod(period))
        return new_periods

    def build_schedule(self, **scenario_kwargs):

        bop_principal_amounts = [self.initial_principal]
        interest_pmts = []
        principal_pmts = []
        eop_principal_amounts = []

        for period in self.interest_periods:
            bop_amount = bop_principal_amounts[-1]

            period_interest_rate = self.interest_rate_provider.period_interest_rate(period, scenario_kwargs)
            interest_pmts.append(period_interest_rate * bop_amount)

            period_principal_pmt = self.principal_payment_provider.period_principal_payment(period, scenario_kwargs)
            principal_pmts.append(bop_amount * period_principal_pmt)

            eop_principal_amounts.append(bop_amount + principal_pmts[-1])

            bop_principal_amounts.append(bop_amount + eop_principal_amounts[-1])
        bop_principal_amounts.pop()

        return {
            'bop_principal_amounts': bop_principal_amounts,
            'interest_pmts': interest_pmts,
            'principal_pmts': principal_pmts,
            'eop_principal_amounts': eop_principal_amounts
        }



