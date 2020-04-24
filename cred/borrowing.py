from dateutil.relativedelta import relativedelta

import pandas as pd
from cred.businessdays import unadjusted, Monthly
from cred.interest_rate import actual360
from cred.period import Period, InterestPeriod


class _Borrowing:

    def __init__(self, desc=None):
        self.desc = desc
        self._periods = {}
        self._in_context = False
        self._cache = False
        self.period_type = Period

    def __enter__(self):
        self._start_caching()
        self._in_context = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._in_context = False
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
        if not self._in_context:
            self._cache = False
            self._periods = {}

    def set_period_values(self, period):
        """
        Called to set period values. Public interface to customize period values, mst be implemented by subclasses.

        Parameters
        __________
        period: Period
            Period to set values. Use `period.add_payment`, `period.add_balance`, or `period.add_data_field` to add to
            include in the period's schedule output.
        """
        raise NotImplementedError

    def schedule(self):
        """Return borrowing schedule. Must be implemented by subclasses"""
        raise NotImplementedError


class PeriodicBorrowing(_Borrowing):
    """
    Abstract class for debt with regular, periodic principal and interest periods. Superclass for
    FixedRateBorrowing.

    Parameters
    ----------
    start_date: datetime-like
        Borrowing start date
    end_date: datetime-like
        Borrowing end date
    freq: Monthly, dateutil.relativedelta.relativedelta
        Interest period frequency. Using the `Monthly` offset is recommended to automatically recognize end of month
        roll dates appropriately.
    initial_principal
        Initial principal amount of the borrowing
    first_reg_start: datetime-like, optional(default=None)
        Start date of first regular interest period. If `None` (default), will be the same as the `start_date`.
    year_frac: function
        Function that takes two dates and returns the year fraction between them. Bound to `Borrowing.year_frac`.
        Default function is `cred.interest.actual360`. Use `cred.interest.thrity360` for NASD 30 / 360 day count.
    pmt_convention: function, optional(default=cred.businessdays.unadjusted)
        Function that takes a date as its first argument and a list of holidays as its second argument and returns the
        adjusted date. See `cred.businessdays.following`, `preceding`, and `modified_following`.
        Bound to `adjust_pmt_date'.
    b_days: pandas.tseries.holiday.AbstractHolidayCalendar, optional(default=None)
        Payment holidays to use in adjusting payment dates. Defaults to None.
    desc: int, str, optional(default=None)
        Optional borrowing description.
    """

    def __init__(self, start_date, end_date, freq, initial_principal, first_reg_start=None, year_frac=actual360,
                 pmt_convention=unadjusted, holidays=None, desc=None):

        super().__init__(desc)
        self.period_type = InterestPeriod
        self.start_date = start_date
        if first_reg_start is not None:
            self.first_reg_start = first_reg_start
        else:
            self.first_reg_start = start_date
        self.end_date = end_date
        self.freq = freq
        self.initial_principal = initial_principal
        self.holidays = holidays

        self.year_frac = year_frac
        self.adjust_pmt_date = pmt_convention

    def date_index(self, dt):
        """
        Returns the index of the period that contains the date argument. Indexes roll on period start dates for
        for consistency with the "from and including, to and excluding" convention. So, calling this method on a roll
        date will return the index for the period which has a matching start date, not the index with a matching end
        date. Calling this method on the borrowing end date will return the index for the last period.

        Examples
        --------
        # Examples for a borrowing starting 2020-01-01, rolling on 2020-02-01, and maturing on 2020-03-01
        >>> borrowing.date_index(date(2020, 1, 31))
        0
        >>> borrowing.date_index(date(2020, 2, 1))
        1
        >>> borroiwng.date_index(date(2020, 3, 1))
        1

        Parameters
        ----------
        dt: datetime-like

        Returns
        -------
        Index of period that contains `dt`
        """
        if dt < self.start_date:
            raise IndexError(f'Date {dt} is before the borrowing start date {self.start_date}.')
        if dt > self.end_date:
            raise IndexError(f'Date {dt} is after borrowing end date {self.end_date}.')
        # if dt is the borrowing end date,
        if dt == self.end_date:
            dt = dt + relativedelta(days=-1)

        i = 0
        start_date = self.period_start_date(i)
        while start_date:
            if start_date > dt:
                return i - 1

            i += 1
            start_date = self.period_start_date(i)

    def set_period_values(self, period):
        period.add_start_date(self.period_start_date(period.index))
        period.add_end_date(self.period_end_date(period.index))
        period.add_pmt_date(self.pmt_date(period.index))
        period.add_balance(self.bop_principal(period), 'bop_principal')
        period.add_display_field(self.interest_rate(period), 'interest_rate')
        period.add_display_field(self.interest_payment(period), 'interest_payment')
        period.add_display_field(self.principal_payment(period), 'principal_payment')
        period.add_payment(self.period_payment(period), 'payment')
        period.add_display_field(self.eop_principal(period), 'eop_principal')

    def period_start_date(self, i):
        # first period
        if i == 0:
            return self.start_date
        # beginning stub period
        if self.start_date != self.first_reg_start:
            return self.first_reg_start + self.freq * (i - 1)
        # not beginning stub period
        return self.start_date + self.freq * i

    def period_end_date(self, i):
        if self.start_date == self.first_reg_start:
            i += 1

        end_dt = self.first_reg_start + self.freq * i

        if end_dt > self.end_date + self.freq - relativedelta(days=1):
            return None
        return min(end_dt, self.end_date)

    def pmt_date(self, i):
        if (self.start_date != self.first_reg_start) and i == 0:
            return self.period_start_date(i)
        return self.adjust_pmt_date(self.period_end_date(i), self.holidays)

    def bop_principal(self, period):
        if period.index == 0:
            return self.initial_principal
        return self.period(period.index - 1).eop_principal

    def interest_rate(self, period):
        raise NotImplementedError

    def interest_payment(self, period):
        yf = self.year_frac(period.start_date, period.end_date)
        return period.interest_rate * yf * period.bop_principal

    def principal_payment(self, period):
        if period.end_date >= self.end_date:
            return period.bop_principal
        return 0

    def period_payment(self, period):
        return period.interest_payment + period.principal_payment

    def eop_principal(self, period):
        return period.bop_principal - period.principal_payment

    def _schedule_periods(self):
        self._start_caching()
        periods = []

        i = 0
        while self.period_end_date(i) is not None:
            p = self.period(i)
            periods.append(p)
            i += 1

        self._stop_caching()
        return periods

    def schedule(self):
        """Returns the borrowing's cash flow schedule"""
        periods = self._schedule_periods()
        schedule = [p.schedule() for p in periods]
        df = pd.DataFrame(schedule).set_index('index')
        return df

    def accrued(self, dt, attr):
        """
        Returns the accrued value for the attr parameter. `attr` must be a period schedule attribute. Returns the amount
        accrued from and including the corresponding period start date to and excludind the date parameter. Uses the
        loan's `year_frac` method to determine the percent accrued.

        Parameters
        ----------
        dt: datetime-like
            Date to accrue to (but not include)
        attr: str
            Name of the period attribute to calculate the accrued amount

        Returns
        -------
        float
        """
        i = self.date_index(dt)
        p = self.period(i)

        amt = p.__getattribute__(attr)
        percent_frac = self.year_frac(p.start_date, dt) / self.year_frac(p.start_date, p.end_date)

        return amt * percent_frac

    # TODO: Maybe collapse into accrued with bool arg for unpaid=False
    def accrued_and_unpaid(self, dt, attr):
        """
        Returns the accrued but unpaid amount of the attribute to but excluding the date parameter. Assumes that amounts
        accrued over an interest period are fulled paid on the period's payment date.

        Parameters
        ----------
        dt: datetime-like
            Date to accrue to (but not include)
        attr: str
            Name of the period attribute to calculate the accrued amount

        Returns
        -------
        float
        """
        dt_i = self.date_index(dt)
        periods = self._schedule_periods()
        paid = 0
        accrued = 0

        for p in periods[0:dt_i + 1]:
            if p.payment_date <= dt:
                paid += p.__getattribute__(attr)
            if p.index < dt_i:
                accrued += p.__getattribute__(attr)
            elif p.index == dt_i:
                accrued += self.accrued(dt, attr)

        return accrued - paid

    def accrued_interest(self, dt, int_attr='interest_payment'):
        """Convenience method for calculating accrued interest. Calls `accrued` with default attribute name
        `interest_payment`."""
        return self.accrued(dt, int_attr)

    # TODO: make robust to period property changes
    def outstanding_amount(self, dt):
        """
        Returns the scheduled outstanding amount for a given date based on interest period start and end dates (i.e.
        does not consider payment dates).

        Parameters
        ----------
        dt: datetime-like
            As of date

        Returns
        -------
        float
        """
        dt_i = self.date_index(dt)
        if dt == self.end_date:
            return self.period(dt_i).eop_principal
        return self.period(dt_i).outstanding_principal()


class FixedRateBorrowing(PeriodicBorrowing):
    """
    PeriodicBorrowing subclass for fixed rate borrowings.

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
    coupon: float
        Coupon rate
    amort_periods: int, object, optional(default=None)
        If None (default), will be calculated as interest only.

        If `amort_periods` is a single number `n`, then will calculate principal payments based on a fully amortizing
        schedule over `n` periods of length `freq` with constant principal and interest payments (e.g. `360` where
        `freq=relativedelta(months=1)` will calculate 30 year amortization with constant monthly payments.

        If `amort_periods` is an object, it must implement `__getitem__` and must have length at least greater than or
        equal to the number of periods. Custom amortization schedules can be provided this way, for example using lists
        or `pandas.Series` objects with amortization amount for period i at index i. Note that custom amortizations
        schedules should include the balloon payment as well.
    io_periods: int, optional(default=0)
        If `amort_periods` is a number (i.e. amortization with constant principal and interest payments), then defines
        the leading number of full interest only periods. Calculated from the `first_reg_start` date, so any leading
        stub periods are ignored.
    **kwargs
        Keyword arguments passed to superclass (PeriodicBorrowing) initialization. Ex. `desc` for borrowing description,
        `year_frac` for day count convention, `pmt_convention` for business day adjustment, `first_reg_start`, etc.
    """

    def __init__(self, start_date, end_date, freq, initial_principal, coupon, amort_periods=None, io_periods=0, **kwargs):
        super().__init__(start_date, end_date, freq, initial_principal, **kwargs)
        self.coupon = coupon
        self.amort_periods = amort_periods
        self.io_periods = io_periods

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
        # no amort if in io period
        if period.start_date < self.first_reg_start + self.freq * self.io_periods:
            return self._interest_only(period)
        # no amort if first period is stub
        if (period.index == 0) & (self.start_date != self.first_reg_start):
            return 0
        # last period
        if period.end_date == self.end_date:
            return period.bop_principal
        # periodic amortization
        periodic_ir = self.coupon / 12
        if periodic_ir == 0:
            return self.initial_principal / self.amort_periods

        pmt = periodic_ir / (1 - (1 + periodic_ir) ** -self.amort_periods) * self.initial_principal
        return pmt - period.interest_payment

