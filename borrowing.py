import pandas as pd

from period import Period, InterestPeriod


class _Borrowing:

    def __init__(self):
        self._periods = {}
        self._cache = False
        self.period_type = Period

    def __enter__(self):
        self._start_caching()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stop_caching()

    def period(self, i):
        """ Return period at index i"""
        if i < 0:
            raise IndexError('Cannot access period with index less than 0')

        if (self._cache is True) and (i in self._periods.keys()):
            return self._periods[i]

        p = self._create_period(i)

        if self._cache is True:
            self._periods[i] = p

        return p

    def _create_period(self, i):
        if i < 0:
            raise ValueError('Value for period index must be greater than or equal to 0')

        p = self.period_type(i)
        self.set_period_values(p)
        return p

    def _start_caching(self):
        self._periods = {}
        self._cache = True

    def _stop_caching(self):
        self._cache = False
        self._periods = {}

    def set_period_values(self, period):
        """
        Called to set period values. Public interface to customize period values, mst be implemented by subclasses.
        Parameters
        __________
        period: Period
            Period to set values
        """
        raise NotImplementedError

    def schedule(self):
        """Return borrowing schedule. Must be implemented by subclasses"""
        raise NotImplementedError


class PeriodicBorrowing(_Borrowing):
    """Abstract class for debt with regular, periodic principal and interest periods. Superclass for
    FixedRateBorrowing.

    Parameters
    ----------
    start_date: datetime-like
        Borrowing start date
    end_date: datetime-like
        Borrowing end date
    freq: dateutil.relativedelta.relativedelta
        Interest period frequency
    initial_principal
        Initial principal amount of the borrowing
    """

    def __init__(self, start_date, end_date, freq, initial_principal):

        super().__init__()
        self.period_type = InterestPeriod
        self.start_date = start_date
        self.end_date = end_date
        self.freq = freq
        self.initial_principal = initial_principal

    def set_period_values(self, period):
        period.add_start_date(self.period_start_date(period.index))
        period.add_end_date(self.period_end_date(period.index))
        period.add_pmt_date(self.pmt_date(period))
        period.add_balance(self.bop_principal(period), 'bop_principal')
        period.add_display_field(self.interest_rate(period), 'interest_rate')
        period.add_display_field(self.interest_payment(period), 'interest_payment')
        period.add_display_field(self.principal_payment(period), 'principal_payment')
        period.add_payment(self.period_payment(period), 'payment')
        period.add_display_field(self.eop_principal(period), 'eop_principal')

    def period_start_date(self, i):
        return self.start_date + self.freq * i

    def period_end_date(self, i):
        return self.start_date + self.freq * (i + 1)

    def pmt_date(self, period):
        return period.end_date

    def bop_principal(self, period):
        if period.index == 0:
            return self.initial_principal
        return self.period(period.index - 1).eop_principal

    def interest_rate(self, period):
        raise NotImplementedError

    def interest_payment(self, period):
        return period.interest_rate / 12 * period.bop_principal

    def principal_payment(self, period):
        if period.end_date == self.end_date:
            return period.bop_principal
        return 0

    def period_payment(self, period):
        return period.interest_payment + period.principal_payment

    def eop_principal(self, period):
        return period.bop_principal - period.principal_payment

    def schedule(self):
        """Returns the borrowing's cash flow schedule"""
        self._start_caching()
        schedule = []

        i = 0
        while self.period_end_date(i) <= self.end_date:
            p = self.period(i)
            schedule.append(p.schedule())
            i += 1

        df = pd.DataFrame(schedule).set_index('index')
        self._stop_caching()
        return df


class FixedRateBorrowing(PeriodicBorrowing):
    """
    PeriodicBorrowing subclass for fixed rate borrowings.

    Parameters
    ----------
    start_date: datetime-like
    end_date: datetime-like
    freq: dateutil.relativedelta.relativedelta
        Interest period frequency
    initial_principal
        Initial principal amount of the borrowing
    coupon
    amort_periods: int, object, optional(default=None)
        If None (default), will be calculated as interest only.

        If `amort_periods` is a single number, then will
        calculate principal payments based on a fully amortizing schedule with constant principal and interest
        payments (e.g. `360` where `freq=relativedelta(months=1)` will calculate 30 year amortization with constant
        monthly payments.

        If `amort_periods` is an object, it must implement `__getitem__` and must have length at least greater than or
        equal to the number of periods. Custom amortization schedules can be provided this way, for example using lists
        or `pandas.Series` objects with amortization amount for period i at index i. Note that custom amortizations
        schedules should include the balloon payment as well.
    """

    def __init__(self, start_date, end_date, freq, initial_principal, coupon, amort_periods=None):
        super().__init__(start_date, end_date, freq, initial_principal)
        self.coupon = coupon
        self.amort_periods = amort_periods

    def interest_rate(self, period):
        return self.coupon

    def principal_payment(self, period):
        # interest only if amort is None
        if self.amort_periods is None:
            return self._interest_only(period)
        # if amort value implements __getitem__, get amort value for period
        elif hasattr(self.amort_periods, '__getitem__'):
            return self.amort_periods[period.index]
        # else try calculating amortization based on number of amort periods
        return self._constant_pmt_amort(period)

    def _interest_only(self, period):
        if period.end_date == self.end_date:
            return period.bop_principal
        return 0

    def _constant_pmt_amort(self, period):
        # last period
        if period.end_date == self.end_date:
            return period.bop_principal
        # periodic amortization
        periodic_ir = self.coupon / 12
        if periodic_ir == 0:
            return self.initial_principal / self.amort_periods

        pmt = periodic_ir / (1 - (1 + periodic_ir) ** -self.amort_periods) * self.initial_principal
        return pmt - period.interest_payment



