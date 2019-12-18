from .interest_rate import FixedRate


class PrincipalPaymentProvider:
    """
    Returns the end of period principal as a percent/fraction of beginning period principal.
    """

    def __init__(self, final_period):
        self.final_period = final_period

    def period_principal_payment(self, interest_period, **kwargs):
        raise NotImplementedError


class InterestOnlyPrincipalPayments(PrincipalPaymentProvider):

    def period_principal_payment(self, interest_period, **kwargs):
        if interest_period.period_id == self.final_period:
            return 1
        return 0


class FixedRatePIKProvider(PrincipalPaymentProvider):

    def period_principal_payment(self, interest_period, **kwargs):
        if interest_period.period_id <= self.final_period:
            interest = FixedRatePIKProvider().period_interest_rate(interest_period)
            return 1 + interest
        return 0
