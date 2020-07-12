from dateutil.relativedelta import relativedelta

from cred.interest_rate import periods_in_year


class BasePrepayment:

    def __init__(self):
        self.ppmt_type = self.__class__.__name__

    def required_repayment(self, borrowing, dt):
        raise NotImplementedError

    def __repr__(self):
        desc = 'Type: ' + self.ppmt_type + '\n'
        return desc


class OpenPrepayment(BasePrepayment):

    _period_breakage_types = [
        None,
        'accrued_and_unpaid',
        'full_period'
    ]

    def __init__(self, period_breakage='full_period'):
        """
        Object that calculates repayment for open prepayment terms. `period_breakage` defines the repayment amount if
        the date of repayment is not on a payment date and interest period end date. Includes regularly scheduled
        payments due on the date or repayment, if any.

        * **None:**  Repayment amount equals the outstanding balance with adjustments for any pre-paid amounts or amounts
        unpaid. For example, if the interest period ends on the first of the month but isn't paid until the third due to
        business day adjustments, the repayment amount on the second will equal the outstanding principal amount plus
        the regularly scheduled payment due on the third.
        * **"accrued_an_unpaid":** In addition unpaid amounts, adds accrued interest to the repayment amount. Building on
        the previous example, this method would add one day of interest (from the first to the second) to the total
        repayment amount.
        * **"full_period":** If the repayment date is on any day other than the last day of an interest period, includes
        interest that accrues over the entire period. Building on the first example again, the "full_period" repayment
        amount would equal the outstanding principal plus the unpaid amount due on the third plus the interest that
        would accrue to but excluding the first day of the next month.

        Parameters
        ----------
        period_breakage
            Breakage type must be `None`, 'accrued_and_unpaid', or 'full_period'
        """
        super(OpenPrepayment, self).__init__()
        if period_breakage not in self._period_breakage_types:
            raise ValueError(f'period_breakage must be on of {self._period_breakage_types}.')
        self.period_breakage = period_breakage

    def required_repayment(self, borrowing, dt):
        """Return required repayment amount based on open prepayment."""
        # check that date is in bounds
        pmts = borrowing.payments(pmt_dt=True)
        if dt < borrowing.start_date or dt > pmts[-1][0]:
            return None
        # calc repayment amount
        amt = borrowing.outstanding_principal(dt, include_dt=True)

        if self.period_breakage is None or self.period_breakage == 'accrued_and_unpaid':
            amt += self.unpaid_interest(borrowing, dt)
        if self.period_breakage == 'accrued_and_unpaid':
            amt += self.net_accrued_interest(borrowing, dt)
        if self.period_breakage == 'full_period':
            amt += self.unpaid_and_current_period_interest(borrowing, dt)

        return amt

    def unpaid_interest(self, borrowing, dt):
        """Unpaid interest, including interest due on `dt`."""
        return borrowing.unpaid_amount(dt, interest=True, princ=False, include_dt=True)

    def net_accrued_interest(self, borrowing, dt):
        """
        Accrued but interest during the period in which `dt` falls. Calculates interest from and including the first day
        of the period, to but excluding `dt` net of any amount already paid.
        """
        accrued = borrowing.accrued_interest(dt, include_dt=False)
        period = borrowing.date_period(dt)
        if dt >= period.get_pmt_date():
            accrued = max(accrued - period.get_interest_pmt(), 0)
        return accrued

    def unpaid_and_current_period_interest(self, borrowing, dt):
        """Unpaid interest including interest due on `dt` plus interest accruing through the end of the period in which
        `dt` falls."""
        unpaid = borrowing.unpaid_amount(dt, interest=True, princ=False, include_dt=True)
        period = borrowing.date_period(dt, inc_period_end=True)
        if dt < period.get_pmt_date() and dt < period.get_end_date():
            period_int = period.get_interest_pmt()
        else:
            period_int = 0.0
        return unpaid + period_int

    def __repr__(self):
        repr = super(OpenPrepayment, self).__repr__()
        repr = repr + 'Period breakage: ' + str(self.period_breakage) + '\n'
        return repr


class StepDown(OpenPrepayment):

    def __init__(self, expiration_offsets, premiums, period_breakage='full_period'):
        """
        Prepayment estimator object for loan exit costs based on a percentage of outstanding principal.

        Repayment costs under this structure are defined by a list of percentages in decimal form for each premium level
        and a matching list of date offsets that denote the expiration date for each premium level.

        Date offsets are applied to the borrowing's first regular period start date and then adjusted based on the
        borrowing's `adjust_pmt_date` method. Offsets are interpreted as expiration dates, so any date on or after a
        given expiration date would use the following premium level. Repayment dates on or after the final expiration
        date are assumed to be open.

        Premiums are applied to the to the-current outstanding principal amount outstanding. Note that the outstanding
        principal balance is adjusted based on amortization payments made on payment dates rather than interest period
        start and end dates.

        Period breakage determines how interest payments are determined if the repayment date is not on a payment date.
        See the `OpenPrepayment` super class for additional detail on how period breakage is determined.

        Parameters
        ----------
        expiration_offsets: list(relativedelta.relativedelta)
            Offsets applied to a borrowing's first regular start date to get the unadjusted expiration date for each
            threshold level
        premiums: list(float)
            List of prepayment premiums expressed as a fraction of the then-current outstanding principal
        period_breakage: str, None optional(default='full_period')
            Period breakage type passed to OpenPrepayment, must be `None`, 'accrued_and_unpaid' or 'full_period'
        """
        if len(expiration_offsets) != len(premiums):
            raise ValueError('Lists of expiration offsets and premiums must be the same lengths.')

        super(StepDown, self).__init__(period_breakage)
        self.expiration_offsets = expiration_offsets
        self.premiums = premiums

    def required_repayment(self, borrowing, dt):
        """Required amount to prepay the borrowing at the given date."""
        open_amt = super(StepDown, self).required_repayment(borrowing, dt)
        ppmt_premium = self.ppmt_premium(borrowing, dt)
        if open_amt is None:
            return None
        return open_amt + ppmt_premium

    def ppmt_premium(self, borrowing, dt):
        """The prepayment premium for prepaying on `dt`."""
        principal = borrowing.outstanding_principal(dt, include_dt=False)
        if principal is None:
            return None
        return principal * self.premium_pct(borrowing, dt)

    def premium_pct(self, borrowing, dt):
        """The premium at `dt` expressed as a percent in decimal form of the then outstanding balance."""
        expir_dts = self.expiration_dates(borrowing)

        if dt >= expir_dts[-1]:
            return 0.0

        expir_i = min([i for i, d in enumerate(expir_dts) if d > dt])
        return self.premiums[expir_i]

    def expiration_dates(self, borrowing):
        """Premium expiration dates adjusted for payment date business days by applying the expiration offsets to
        the borrowing's first regular period start date."""
        dts = [borrowing.first_reg_start + offset for offset in self.expiration_offsets]
        return [borrowing.adjust_pmt_date(dt, borrowing.holidays) for dt in dts]

    def __repr__(self):
        repr = super(StepDown, self).__repr__()
        repr = repr + 'Offsets: ' + str(self.expiration_offsets) + '\n'
        repr = repr + 'Premiums: ' + str(self.premiums) + '\n'
        return repr


class Defeasance(OpenPrepayment):

    def __init__(self, df_func, open_dt_offset=None, dfz_to_open=False, period_breakage='full_period'):
        """
        Prepayment class for PeriodicBorrowings that estimates the cost of defeasance substitution collateral.
        This class takes a function which returns the appropriate discount factor between the closing date and each
        future payment date to estimate the cost of substitution collateral. The cost of collateral equals the sum of
        discount factors times the remaining future payments.

        Remaining future payments can either be structured to the open date or through maturity. The first open date is
        calculated by applying the open date offset to the borrowing end date. Interest period breakage during the open
        window is calculated using the same method described in `OpenPrepayment` based on `period_breakage`.

        Parameters
        ----------
        df_func: function
            Function that takes two dates and returns the discount factor between them
        open_dt_offset: date-offset
            Date offset from borrowing end date to the first open prepayment date
        dfz_to_open: bool
            Boolean indicating whether to defease cash flows through the open date or maturity
        period_breakage: str, None optional(default='full_period')
            Period breakage type passed to OpenPrepayment, must be `None`, 'accrued_and_unpaid' or 'full_period' passed
            to OpenPrepayment
        """
        super(Defeasance, self).__init__(period_breakage)
        self.df = df_func
        self.open_dt_offset = open_dt_offset
        self.dfz_to_open = dfz_to_open

    def required_repayment(self, borrowing, dt):
        """Return the total estimated cost of replacement collateral"""
        open_dt = self.open_date(borrowing)

        open_pmt = super(Defeasance, self).required_repayment(borrowing, dt)
        if open_pmt is None or (open_dt and (dt >= open_dt)):
            return open_pmt

        dfz_to = (self.dfz_to_open or None) and open_dt
        pmt_dts, pmts = zip(*borrowing.payments(first_dt=dt, last_dt=dfz_to, pmt_dt=True))
        dfs = [self.df(dt, pmt_dt) for pmt_dt in pmt_dts]

        pv_periodic = sum([df * pmt for df, pmt in zip(dfs, pmts)])
        pv_balloon = self.df(dt, pmt_dts[-1]) * borrowing.outstanding_principal(pmt_dts[-1], include_dt=False)
        return pv_periodic + pv_balloon

    def open_date(self, borrowing):
        """Open date for borrowing"""
        if self.open_dt_offset is None:
            return None
        return borrowing.end_date + self.open_dt_offset

    def __repr__(self):
        repr = super(Defeasance, self).__repr__()
        repr = repr + 'Discount factors: ' + self.df.__name__ + '\n'
        repr = repr + 'Open date offset: ' + str(self.open_dt_offset) + '\n'
        repr = repr + 'Defease to open: ' + str(self.dfz_to_open) + '\n'
        return repr


class SimpleYieldMaintenance(OpenPrepayment):

    def __init__(self, rate_func, margin=0.0, wal_rate=False, open_dt_offset=None, ym_to_open=False, min_penalty=None,
                 period_breakage='full_period'):
        """
        Prepayment class for estimating yield maintenance on PeriodicBorrowings. Discounts remaining payments (either to
        maturity or to the open date) at an annual rate equal to the index rate provided by `rate_func` plus the margin.
        The index rate will can be structured to mirror either the term of the remaining payments (i.e. maturity or
        the open date depending on which date the yeild maintenance is structured to) or the weighted average life (WAL)
        of remaining payments. Discount factors are built assuming a simple periodic rate equal to the discount rate
        divided by frequency of borrowing's interest periods. See the `discount_factor` method for detail.

        Future payments are discounted from their unadjusted period end dates rather than payment dates.

        Minimum penalties apply during the yield maintenance period. If there is a minimum penalty, the required
        repayment amount will be equal to the greater of yield maintenance or the open prepayment amount plus the
        outstanding principal amount times the min penalty percent.

        Parameters
        ----------
        rate_func: function
            Function that takes two dates and returns the annualized index rate used in discounting
        margin: float, optional(default=0.0)
            The additional margin added to the index rate used in discounting, if any
        wal_rate: bool, optional(default=False)
            True if the term of the index rate used for discounting should match the weighted average life of the
            remaining payments, False if it should match the term of the final scheduled payment (either the open date
            or maturity).
        open_dt_offset: date-offset, optional(default=None)
            Date offset to apply to the borrowing's end date to get the first day of the open window or None if no open
            window.
        ym_to_open: bool, optional(default=False)
            True if cash flows should be discounted to the open window, False if cash flows should be discounted to
            maturity. Affects the discount rate if `wal_rate == False`.
        min_penalty: float, optional(default=None)
            Minimum penalty as a percent of the outstanding principal balance or None if no min penalty.
        period_breakage: str, None optional(default='full_period')
            Period breakage type passed to OpenPrepayment, must be `None`, 'accrued_and_unpaid' or 'full_period' passed
            to OpenPrepayment
        """
        super(SimpleYieldMaintenance, self).__init__(period_breakage=period_breakage)
        self.index_rate = rate_func
        self.margin = margin
        self.wal_rate = wal_rate
        self.open_dt_offset = open_dt_offset
        self.ym_to_open = ym_to_open
        self.min_penalty = min_penalty

    def required_repayment(self, borrowing, dt):
        open_pmt = super(SimpleYieldMaintenance, self).required_repayment(borrowing, dt)

        open_dt = self.open_date(borrowing)
        if open_pmt is None or (open_dt and dt >= open_dt):
            return open_pmt

        pmts = self.remaining_pmts(borrowing, dt)
        dfs = self.discount_factors(borrowing, dt)

        repay_amt = sum([df * pmt for df, pmt in zip(dfs, pmts.values())])

        if self.min_penalty:
            repay_amt = max(repay_amt, self.min_repayment_amount(borrowing, dt))

        return repay_amt + borrowing.unpaid_amount(dt, interest=True, princ=True, include_dt=True)

    def open_date(self, borrowing):
        """Open date for borrowing."""
        if self.open_dt_offset is None:
            return None
        return borrowing.end_date + self.open_dt_offset

    def min_repayment_amount(self, borrowing, dt):
        return borrowing.outstanding_principal(dt, include_dt=False) * (1 + self.min_penalty)

    def discount_factors(self, borrowing, dt):
        """Discount factors used to calculate yield maintenance."""
        pmts = self.remaining_pmts(borrowing, dt)

        periodic_rate = self.discount_rate(borrowing, dt) * 1 / periods_in_year(borrowing.freq)
        yfs = [borrowing.year_frac(dt, pmt_dt) for pmt_dt in pmts.keys()]
        dfs = [(1 + periodic_rate) ** -yf for yf in yfs]
        return dfs

    def discount_rate(self, borrowing, dt):
        """Discount rate for yield maintenance at date."""
        open_dt = self.open_date(borrowing)

        if open_dt and dt >= open_dt:
            raise ValueError('Date is on or after the open date')
        if dt < borrowing.start_date:
            raise ValueError('Date is before the borrowing start date')

        if self.wal_rate:
            term_date = dt + relativedelta(days=self.discount_rate_term(borrowing, dt))
        else:
            term_date = (self.ym_to_open and open_dt) or borrowing.end_date
        return self.index_rate(dt, term_date) + self.margin

    def discount_rate_term(self, borrowing, dt):
        """Return the number of days used to calculate the term of the discount rate. If `wal_rate` is True, returns the
        weight avgerage number of remaining days. If `ym_to_open` is True, calculates (weighted avg) days to the open
        date rather than the maturity date."""
        discount_to_dt = (self.ym_to_open and self.open_date(borrowing)) or borrowing.end_date

        if self.wal_rate:
            ym_to_dt = (self.ym_to_open and self.open_date(borrowing)) or borrowing.end_date

            princ_pmts = {}
            for p in borrowing.periods:

                # regularly scheduled principal
                if (dt < p.get_end_date() <= ym_to_dt) and (p.get_pmt_date() > dt):
                    princ_pmts[p.get_end_date()] = p.get_principal_pmt()

                # balloon
                if p.get_start_date() <= ym_to_dt < p.get_end_date() and p.get_start_date() >= dt:
                    princ_pmts[ym_to_dt] = princ_pmts.get(ym_to_dt, 0) + p.get_bop_principal()

            if ym_to_dt < borrowing.end_date:
                princ_pmts[ym_to_dt] = princ_pmts.get(ym_to_dt, 0)

            cum_princ = sum(princ_pmts.values())
            days = sum([(end_dt - dt).days * princ / cum_princ for end_dt, princ in princ_pmts.items()])
        else:
            days = (discount_to_dt - dt).days

        return days

    def remaining_pmts(self, borrowing, dt):
        """
        Principal and interest payments from `dt` to maturity, or the open date if `ym_to_open` is True. Based on
        period end dates. The last payment will include all outstanding principal and accrued interest. Return value is
        a dict of {pmt_date: pmt} pairs.
        """
        ym_to_dt = (self.ym_to_open and self.open_date(borrowing)) or borrowing.end_date

        pmts = {}
        for p in borrowing.periods:
            # regularly scheduled p&i
            if (dt < p.get_end_date() <= ym_to_dt) and (p.get_pmt_date() > dt):
                pmts[p.get_end_date()] = p.get_principal_pmt() + p.get_interest_pmt()

            # balloon
            if p.get_start_date() <= ym_to_dt < p.get_end_date() and p.get_start_date() >= dt:
                pmts[ym_to_dt] = pmts.get(ym_to_dt, 0) + p.get_bop_principal()

        if ym_to_dt < borrowing.end_date:
            pmts[ym_to_dt] = pmts.get(ym_to_dt, 0) + borrowing.accrued_interest(ym_to_dt, include_dt=False)

        return pmts

    def __repr__(self):
        repr = super(SimpleYieldMaintenance, self).__repr__()
        repr = repr + 'Index rate: ' + str(self.index_rate.__name__) + '\n'
        repr = repr + 'Margin: ' + f'{self.margin:.2%}' + '\n'
        repr = repr + 'Index rate term: ' + ((self.wal_rate and 'weighted average life') and 'open/maturity') + '\n'
        repr = repr + 'Open date offset: ' + str(self.open_dt_offset) + '\n'
        repr = repr + 'Discount cash flows to: ' + ((self.ym_to_open and 'open date') and 'maturity') + '\n'
        repr = repr + 'Min penalty: ' + '{:.1%}'.format(self.min_penalty) + '\n'
        return repr

