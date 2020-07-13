import itertools

from datetime import datetime
from dateutil.relativedelta import relativedelta

import pandas as pd
from cred.businessdays import unadjusted, Monthly
from cred.interest_rate import actual360
from cred.period import Period, InterestPeriod


class _Borrowing:

    def __init__(self, desc=None):
        self.desc = desc
        self._cached_periods = {}
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

        if (self._cache is True) and (i in self._cached_periods.keys()):
            return self._cached_periods[i]

        p = self._create_period(i)

        if self._cache is True:
            self._cached_periods[i] = p

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
            self._cached_periods = {}
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
        """Return borrowing schedule. Must be implemented by subclasses."""
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
    calc_convention: function, optional(default=cred.businessdays.unadjusted)
        Business day adjustment method for interest calculation dates. Function that takes a date as its first argument
        and a list of holidays as its second argument and returns the adjusted date. See `cred.businessdays.following`,
        `preceding`, and `modified_following`. Assigned to `adjust_calc_date'.
    pmt_convention: function, optional(default=cred.businessdays.unadjusted)
        Business day adjustment method for payment dates. Function that takes a date as its first argument and a list of
        holidays as its second argument and returns the adjusted date. See `cred.businessdays.following`, `preceding`,
        and `modified_following`. Assigned to `adjust_pmt_date'.
    holiday_calendar: pandas.tseries.holiday.AbstractHolidayCalendar, optional(default=None)
        Payment holidays to use in adjusting payment dates. Defaults to None.
    desc: int, str, optional(default=None)
        Optional borrowing description.
    prepayment: BasePrepayment, optional(default=None)
        Optional BasePrepayment subclass that defines prepayment terms and calculates prepayment costs.
    """

    def __init__(self, start_date, end_date, freq, initial_principal, first_reg_start=None, year_frac=actual360,
                 calc_convention=unadjusted, pmt_convention=unadjusted, holiday_calendar=None, desc=None,
                 prepayment=None):

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
        self.prepayment = prepayment
        self._set_holiday_calendar(holiday_calendar)

        self.year_frac = year_frac
        self.adjust_calc_date = calc_convention
        self.adjust_pmt_date = pmt_convention

    def _get_holiday_calendar(self):
        return self._holiday_calendar

    def _set_holiday_calendar(self, calendar):
        if calendar is None:
            self._holidays = None
        else:
            self._holidays = calendar.holidays(datetime(1970, 1, 1), datetime(2200, 1, 1))
        self._holiday_calendar = calendar

    holiday_calendar = property(_get_holiday_calendar, _set_holiday_calendar)

    @property
    def holidays(self):
        return self._holidays

    @property
    def periods(self):
        return self._schedule_periods()

    # Indexing and accessing values
    def date_period(self, dt, inc_period_end=False):
        """
        Returns the period that date falls inside. Default is inclusive of period start date and exclusive of end date.
        Dates prior to the borrowing start date or after the max(borrowing end date, final payment date) raise and
        index error.

        Parameters
        ----------
        dt: datetime-like
            Look-up date
        inc_period_end: bool optional(default=False)
            Determines whether roll dates are included in the ending or starting period. Be default, end dates are
            considered the start date for the next period and are not included.

        Returns
        -------
        InterestPeriod
        """
        i = self.date_index(dt, inc_period_end=inc_period_end)
        return self.period(i)

    def date_index(self, dt, inc_period_end=False):
        """
        Returns the index of the period that contains the date argument. Default is inclusive of period start dates and
        exclusive of end dates. Dates prior to the borrowing start date or after the latest of the borrowing end date or
        final payment date raise and index error.

        Parameters
        ----------
        dt: datetime-like
            Look-up date
        inc_period_end: bool
            Determines whether roll dates are included in the ending or starting period. Be default, end dates are
            considered the start date for the next period and are not included.

        Returns
        -------
        int
        """
        # TODO: add tests
        if dt < self.start_date:
            raise IndexError(f'Date {dt} is before the borrowing start date {self.start_date}.')

        # if dt is the borrowing end date,
        if dt == self.end_date:
            dt = dt + relativedelta(days=-1)

        i = 0
        end_date = self.period_end_date(i)
        while end_date:
            if dt < end_date:
                return i
            elif (dt == end_date) and inc_period_end:
                return i

            i += 1
            end_date = self.period_end_date(i)
        i -= 1
        if dt <= max(self.period_end_date(i), self.pmt_date(i)):
            return i
        else:
            raise IndexError(f'Date {dt} is after the loan ends.')

    def payments(self, first_dt=None, last_dt=None, pmt_dt=False):
        """
        Returns a list of list of `(date, payment_amount)` for all payments from `first_dt` to `last_dt` inclusive. If
        `pmt_dt=False`, then dates will correspond to scheduled period end dates. `pmt_dt=True` will evaluate and return
        dates based on their adjusted payment dates.

        Passing `first_dt` or `last_dt` as `None` will return payments from the first period or through the last period
        respectively. Passing both as `None` will return payments for the entire term of the borrowing.

        Parameters
        ----------
        first_dt: datetime-like, optional(default=None)
            First payment date, inclusive
        last_dt: datetime-like, optional(default=None)
            Last payment date, inclusive
        pmt_dt: bool
            Whether to evaluate dates based on scheduled period end dates or adjusted period payment dates

        Returns
        -------
        list((date, float))
        """
        if first_dt is None:
            first_dt = pd.Timestamp.min
        if last_dt is None:
            last_dt = pd.Timestamp.max

        periods = self._schedule_periods()
        pmts = [p.get_payment() for p in periods]

        if pmt_dt:
            dts = [p.get_pmt_date() for p in periods]
            dt_mask = [(dt >= first_dt) & (dt <= last_dt) for dt in dts]
        else:
            dts = [p.get_end_date() for p in periods]
            dt_mask = [(dt >= first_dt) & (dt <= last_dt) for dt in dts]

        return list(zip(itertools.compress(dts, dt_mask), itertools.compress(pmts, dt_mask)))

    def accrued_interest(self, dt, include_dt=False):
        """
        Returns the amount of interest accrued from the start of the interest period in which `dt` falls to `dt`. By
        default, calculates interest from and including the period start date to but excluding `dt`. Set
        `include_dt=True` to include interest accrued through and including `dt`.
        """
        # TODO: add tests
        period = self.date_period(dt, inc_period_end=False)

        if dt > period.get_end_date():
            return 0

        percent_period = min(self.year_frac(period.get_start_date(), dt + relativedelta(days=1 * include_dt)) /
                             self.year_frac(period.get_start_date(), period.get_end_date()), 1)
        return percent_period * period.get_interest_pmt()

    def unpaid_amount(self, dt, interest=True, princ=True, include_dt=False):
        """
        Returns the total unpaid interest and/or principal, if any. Specifically, returns the amount of interest to be
        paid on the payment date if `dt` is greater than or equal to the period end date but less than (or less than or
        equal to if `include_dt=True`) the period payment date and/or any scheduled principal payments if dt is between
        the period end date and payment date.

        By default, does not include any payments due on `dt`.

        Parameters
        ----------
        dt: datetime-like
            Date of evaluation
        interest: bool
            Include unpaid interest if True
        princ: bool
            Include unpaid principal if True
        include_dt: bool
            Include amounts scheduled to be paid on `dt`
        """
        # TODO: add tests
        i = self.date_index(dt, inc_period_end=True)

        unpaid_int = 0
        unpaid_princ = 0
        for i in range(0, i+1):
            p = self.period(i)
            if p.get_end_date() <= dt < p.get_pmt_date():
                unpaid_int += p.get_interest_pmt() * interest
                unpaid_princ += p.get_principal_pmt() * princ
            if include_dt and dt == p.get_pmt_date():
                unpaid_int += p.get_interest_pmt() * interest
                unpaid_princ += p.get_principal_pmt() * princ

        return unpaid_int + unpaid_princ

    def outstanding_principal(self, dt, include_dt=False):
        """
        Returns the clean amount not including any accrued interest. The outstanding amount contemplates payment dates
        rather than period end dates, so the balance is not reduced by any amortization until the payment date occurs.

        Returns None for dates prior to the start date, and returns the last period's beginning balance less principal
        payment for any date equal or greater than the final payment date.

        See `repayment_amount` for total cost to repay including any prepayment premiums.

        Parameters
        ----------
        dt: datetime-like
            As-of date
        include_dt: bool, optional(default=False)
            Indicates whether to include principal payments due on `dt`

        Returns
        -------
        float
        """
        if dt < self.start_date:
            return None

        periods = self._schedule_periods()

        outstanding = self.initial_principal

        for p in periods:
            if include_dt and dt > p.get_pmt_date():
                outstanding -= p.get_principal_pmt()
            elif not include_dt and dt >= p.get_pmt_date():
                outstanding -= p.get_principal_pmt()

        return outstanding

    # Building the schedule
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
        """Returns the borrowing's cash flow schedule as a `pandas.DataFrame`."""
        periods = self._schedule_periods()
        schedule = [p.schedule() for p in periods]
        df = pd.DataFrame(schedule).set_index('index')
        return df

    def set_period_values(self, period):
        """
        Called for each period after it is initialized to set the period's values. Calculating period values may rely on
        previously set values for that period (e.g. see interest payment), so order matters.

        `PeriodicBorrowing` and its subclasses use `InterestPeriod` which should have a start date, end date, payment
        date, beginning period principal, interest payment, and principal payments.
        """
        period.add_start_date(self.period_start_date(period.index))
        period.add_end_date(self.period_end_date(period.index))
        period.add_pmt_date(self.pmt_date(period.index))
        period.add_bop_principal(self.bop_principal(period))
        period.add_display_field(self.interest_rate(period), 'interest_rate')
        period.add_interest_pmt(self.interest_payment(period))
        period.add_principal_pmt(self.principal_payment(period))
        period.add_display_field(self.period_payment(period), 'payment')
        period.add_display_field(self.eop_principal(period), 'eop_principal')

    # Period value methods
    def period_start_date(self, i):
        """Returns the calculation start date for period with index `i`."""
        # first period
        if i == 0:
            dt = self.start_date
        # beginning stub period
        elif self.start_date != self.first_reg_start:
            dt = self.first_reg_start + self.freq * (i - 1)
        # not beginning stub period
        else:
            dt = self.start_date + self.freq * i

        return self.adjust_calc_date(dt, self.holidays)

    def period_end_date(self, i):
        """
        Returns end period calculation end date for period with index `i`. Returns `None` for indexes greater than
        then number of interest periods in the loan.
        """
        if self.start_date == self.first_reg_start:
            i += 1

        end_dt = self.first_reg_start + self.freq * i

        if end_dt > self.end_date + self.freq - relativedelta(days=1):
            return None
        return self.adjust_calc_date(min(end_dt, self.end_date), self.holidays)

    def pmt_date(self, i):
        """Returns the payment date for period with index `i`."""
        if (self.start_date != self.first_reg_start) and i == 0:
            dt = self.period_start_date(i)
        else:
            dt = self.period_end_date(i)
        return self.adjust_pmt_date(dt, self.holidays)

    def bop_principal(self, period):
        """Returns the beginning of interest period principal balance for the `InterestPeriod` argument."""
        if period.index == 0:
            return self.initial_principal
        return self.period(period.index - 1).eop_principal

    def interest_rate(self, period):
        raise NotImplementedError

    def interest_payment(self, period):
        """
        Calculates the interest payment for the period as the year fraction from the period's start date to end date
        (using the borrowing's `year_frac` method) times the period's `interest_rate` property times the period's
        `bop_principal` property.

        Parameters
        ----------
        period: InterestPeriod
            `PeriodicBorrowing` uses `InterestPeriod` class periods.
        Returns
        -------
        float
        """
        yf = self.year_frac(period.start_date, period.end_date)
        return period.interest_rate * yf * period.bop_principal

    def principal_payment(self, period):
        """Returns the principal payment for the period. By default this assumings interest only unless overridden by a
        subclass (e.g. FixedRateBorrowing)."""
        if period.end_date >= self.end_date:
            return period.bop_principal
        return 0

    def period_payment(self, period):
        """Returns the sum of the period's interest and principal payments."""
        return period.interest_payment + period.principal_payment

    def eop_principal(self, period):
        """Period beginning balance less the period principal payment."""
        return period.bop_principal - period.principal_payment

    # Prepayment
    def repayment_amount(self, dt):
        """Required repayment amount including any prepayment premiums as defined by the `prepayment` object. See
        `borrowing.outstanding_principal` for clean balance."""
        if self.prepayment is None:
            raise AttributeError('Must define a prepayment calculator attribute.')
        return self.prepayment.required_repayment(self, dt)


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

    def __init__(self, start_date, end_date, freq, initial_principal, coupon, amort_periods=None, io_periods=0,
                 **kwargs):
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
