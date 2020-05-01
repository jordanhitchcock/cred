

class BasePrepaymentCalculator:

    def __init__(self):
        self.ppmt_type = self.__class__.__name__

    def required_repayment(self, borrowing, dt):
        raise NotImplementedError

    def __repr__(self):
        desc = 'Type: ' + self.ppmt_type + '\n'
        return desc

#
# class Defeasance(BasePrepaymentCalculator):
#
#     def __init__(self, df_func, open_dt_offset, dfz_to_open):
#         super(Defeasance, self).__init__('defeasance')
#         self.df = df_func
#         self.open_dt_offset = open_dt_offset
#         self.dfz_to_open = dfz_to_open
#
#     def repayment_amount(self, borrowing, dt):
#         """
#         Returns total repayment cost including accrued and unpaid interest and estimated securities cost for repaying the
#         borrowing on `dt` if the borrowing is subject to defeasance. Estimates defeasance cost by discounting future
#         payments from their adjusted payment date. If the borrowing's property `dfz_to_open == True`, future cash flows are
#         terminated on the open date at the outstanding principal balance plus any accrued and unpaid interest. The open
#         window start date is determined by applying the borrowing's `open_dt_offset` to the borrowing end date.
#
#         Realized defeasance costs will differ based on inefficiencies in the underlying securities portfolio, fees, and any
#         variations in specific loan language (e.g. requirement that securities payout on the first business day prior to the
#         unadjusted period end dates).
#         """
#
#         # return None if dt is before start_date or after the final pmt date
#         if (dt < borrowing.start_date) or (dt > borrowing.adjust_pmt_date(borrowing.end_date, borrowing.holidays)):
#             return None
#
#         # calc first open date
#         open_date = None
#         if self.open_dt_offset is not None:
#             open_date = borrowing.end_date - self.open_dt_offset
#
#         # if dt in open window
#         if open_date and dt >= open_date:
#             remaining_pmts = dict(borrowing.payments(dt, pmt_dt=True))
#             next_pmt_dt = min([pmt for pmt in remaining_pmts.keys() if pmt >= dt])
#             return borrowing.outstanding_principal(next_pmt_dt) + remaining_pmts[next_pmt_dt]
#
#         # if dt prior to open date
#         if self.dfz_to_open:
#             remaining_pmts = self._pmts_between_dates(borrowing, dt, open_date)
#         else:
#             remaining_pmts = dict(borrowing.payments(first_dt=dt, pmt_dt=True))
#
#         pv = 0
#         for pmt_dt, pmt in remaining_pmts.items():
#             pv += self.df(dt, pmt_dt) * pmt
#
#         return pv
#
#     def _pmts_between_dates(self, borrowing, start_dt, end_dt):
#         # TODO: Should this be a borrowing method?
#         """
#         Returns a dict of {payment date: payment} pairs for scheduled payments from `start_dt` to `end_dt` , inclusive,
#         where the payment amount on `end_dt` equals the outstanding balance plus accrued and unpaid interest.
#         """
#         remaining_pmts = dict(borrowing.payments(first_dt=start_dt, last_dt=end_dt, pmt_dt=True))
#
#         filtered_pmts = {k: v for k, v in remaining_pmts.items() if k <= end_dt}
#         repayment_dt_pmt = filtered_pmts.get(end_dt, 0)
#         repayment_dt_pmt += borrowing.outstanding_principal(end_dt) + borrowing.accrued_unpaid_int(end_dt)
#         filtered_pmts[end_dt] = repayment_dt_pmt
#         return filtered_pmts
#
#     def __repr__(self):
#         desc = super(Defeasance, self).__repr__()
#         desc = desc + 'Open window offset: ' + str(self.open_dt_offset) + '\n'
#         desc = desc + 'Defease to open date: ' + str(self.dfz_to_open) + '\n'
#         desc = desc + 'Discount factors: ' + self.df.__name__ + '\n'
#         return desc
#
#
# class Stepdown(BasePrepaymentCalculator):
#
#     def __init__(self, expiration_offsets, premiums):
#         """
#         Prepayment calculator for penalties based on the percentage of outstanding principal. Repayment amount equals
#         the applicable premium times the outstanding principal balance plus interest through the next payment date. The
#         lists of date offsets and premiums must be the same length. Assumes 0.0% premium for any dates after the final
#         expiration offset.
#
#
#         Parameters
#         ----------
#         expiration_offsets: list(dateutil.relativedelta.relativedelta)
#             Expiration dates for each percentage level (i.e. threshold will apply up to but excluding the offset date).
#             Offsets applied to the first regular period start date.
#         premiums: list(float)
#
#         """
#         if len(expiration_offsets) != len(premiums):
#             raise ValueError(f'Length of offsets ({len(expiration_offsets)} does not equal the length of thresholds '
#                              f'{len(premiums)}.')
#
#         super(Stepdown, self).__init__('stepdown')
#         self.expiration_offsets = expiration_offsets
#         self.premiums = premiums
#
#     def repayment_amount(self, borrowing, dt):
#         """
#         Total cost of repayment including prepayment premium and interest through the next payment date. Assumes a
#         0.0% premium for all dates after the last defined expiration offset. Returns `None` for any dates before the
#         borrowing start date or after the final payment date.
#
#         Parameters
#         ----------
#         borrowing: PeriodicBorrowing
#             Borrowing to calculate the repayment amount on.
#         dt: datetime-like
#             Date of repayment.
#
#         Returns
#         -------
#         float
#         """
#         pmts = borrowing.payments(pmt_dt=True)
#
#         if dt < borrowing.start_date or dt > pmts[-1][0]:
#             return None
#
#         pmts = dict(pmts)
#         next_pmt_dt = min([pmt for pmt in pmts.keys() if pmt >= dt])
#
#         expiration_dts = [borrowing.start_date + offset for offset in self.expiration_offsets]
#         premiums = dict(zip(expiration_dts, self.premiums))
#
#         if dt >= max(expiration_dts):
#             applicable_premium = 1.0
#         else:
#             expir_dt = min([ex_dt for ex_dt in expiration_dts if ex_dt > dt])
#             applicable_premium = 1 + premiums[expir_dt]
#
#         return applicable_premium * borrowing.outstanding_principal(dt) + pmts[next_pmt_dt]
#
#     def __repr__(self):
#         desc = super(Stepdown, self).__repr__()
#         desc = desc + 'Expiration offsets: ' + repr(self.expiration_offsets) + '\n'
#         desc = desc + 'Premiums: ' + repr(self.premiums) + '\n'
#         return desc
#
#
# class YieldMaintenance(BasePrepaymentCalculator):
#
#     undiscounted_int_methods = [
#         'unpaid', 'accrued_and_unpaid', 'full_period'
#     ]
#
#     def __init__(self, rate_func, spread=0.0, undiscounted_interest='full_period', first_discount_pmt=0,
#                  ym_to_open=False, open_dt_offset=None, min_premium=None):
#         """
#         Yield maintenance calculator object that can be applied to PeriodicBorrowings.
#
#         Parameters
#         ----------
#         rate_func: function
#             Function that takes two dates and returns the yield between them stated in an semi-annual compounding terms
#         spread: float optional(default=0.0)
#             Spread added to the benchmark rate for discounting
#         undiscounted_interest: str optional(default='full_period')
#             String that defines undiscounted interest to be paid on the closing date. Must be one of the following:
#                 `unpaid`: Any interest from the previous period that remains unpaid
#                 `accrued_and_unpaid`: Unpaid interest plus, if prepaid on a date other than a period end date, interest
#                 accrued from the the period start date to but excluding the date of prepayment
#                 `full_period`: Any unpaid interest plus, if prepaid on a date other than a period end date, any interest
#                 accruing through the end of the current interest period
#         first_discount_pmt: int, default=0
#             First payment to discount. 0 is the next payment, 1 skips the next payment and starts discounting the
#             from the following payment, etc...
#         ym_to_open: bool, default=False
#             Boolean indicating whether to discount cash flows through the open window or through maturity
#         open_dt_offset: dateutil.relativedelta.relativedelta, default=None
#             `None` if no open period. Otherwise, the date offset from the borrowing end date for the first open date
#         min_premium: float, default=None
#             `None` if no minimum prepayment penalty, otherwise a float representing the minimum penalty expressed as a
#             percent of principal
#         """
#         super(YieldMaintenance, self).__init__('yield_maintenance')
#         self.benchmark_rate = rate_func
#         self.spread = spread
#         if undiscounted_interest not in self.undiscounted_int_methods:
#             raise ValueError(f'undiscounted_interest must be one of: {self.undiscounted_int_methods}.')
#         else:
#             self.undiscounted_interest = undiscounted_interest
#         self.first_discount_pmt = first_discount_pmt
#         self.open_dt_offset = open_dt_offset
#         self.min_premium = min_premium
#         self.ym_to_open = ym_to_open
#
#     def repayment_amount(self, borrowing, dt):
#         """
#         Returns the total repayment as of `dt` including accrued interest due and any applicable yield maintenance
#         penalty. Return `None` if the repayment date is before the borrowing start date or after the final payment date.
#
#         Parameters
#         ----------
#         borrowing: PeriodicBorrowing
#             Borrowing to calculate repayment on
#         dt: datetime-like
#             Date of repayment
#
#         Returns
#         -------
#         float
#         """
#         # TODO: this doesn't work for preceding pmt convention
#         if dt < borrowing.start_date or dt > borrowing.adjust_pmt_date(borrowing.end_date):
#             return None
#         open_dt = borrowing.end_date - self.open_dt_offset
#
#         if dt >= open_dt:
#             return 'open'
#
#         undiscounted_int = self.calc_undiscounted_interest(borrowing, dt)
#         ym_penalty = self.ym_penalty(borrowing, dt)
#
#         return borrowing.outstanding_principal(dt) + undiscounted_int + ym_penalty  # TODO: also need to include any unpaid principal payments
#
#     def calc_undiscounted_interest(self, borrowing, dt):
#         """Returns the undiscounted interest due"""
#         undiscounted_int = borrowing.unpaid_interest(dt, include_dt=True)
#         if self.undiscounted_interest == 'accrued_and_unpaid':
#             undiscounted_int += borrowing.accrued_unpaid_int(dt, include_dt=False)
#         elif self.undiscounted_interest == 'full_period':
#             p = borrowing.date_period(dt, inc_period_end=True)
#             if dt != p.get_start_date():
#                 undiscounted_int += p.get_interest_pmt()
#
#         return undiscounted_int
#
#     def discounted_cash_flows(self, borrowing, dt):
#         pass
#
#     def __repr__(self):
#         desc = super(YieldMaintenance, self).__repr__()
#         desc = desc + 'Benchmark rate: ' + self.benchmark_rate.__name__ + '\n'
#         desc = desc + 'Spread to benchmark rate: ' + f'{self.spread * 100:.0%} bps' + '\n'
#         desc = desc + 'Undiscounted interest: ' + str(self.undiscounted_interest) + '\n'
#         desc = desc + 'First discounted payment: ' + str(self.first_discount_pmt) + '\n'
#         desc = desc + 'Calculate YM to open: ' + str(self.ym_to_open) + '\n'
#         desc = desc + 'Open date offset: ' + str(self.open_dt_offset) + '\n'
#         desc = desc + 'Minimum penalty: ' + f'{self.min_premium * 100:.0%} bps' + '\n'
#         return desc
#

class OpenPrepayment(BasePrepaymentCalculator):

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
            amt += self.unpaid_amount(borrowing, dt)
        if self.period_breakage == 'accrued_and_unpaid':
            amt += self.accrued_interest(borrowing, dt)
        if self.period_breakage == 'full_period':
            amt += self.unpaid_and_current_period_interest(borrowing, dt)

        return amt

    def unpaid_amount(self, borrowing, dt):
        """Unpaid interest, including interest due on `dt`."""
        return borrowing.unpaid_interest(dt, include_dt=True)

    def accrued_interest(self, borrowing, dt):
        """Accrued interest during the period in which `dt` falls. Calculates interest from and including the first day
        of the period, to but excluding `dt`."""
        return borrowing.accrued_interest(dt, include_dt=False)

    def unpaid_and_current_period_interest(self, borrowing, dt):
        """Unpaid interest including interest due on `dt` plus interest accruing through the end of the period in which
        `dt` falls."""
        unpaid = borrowing.unpaid_interest(dt, include_dt=True)
        period = borrowing.date_period(dt, inc_period_end=True)
        if dt < period.get_pmt_date() and dt < period.get_end_date():
            period_int = period.get_interest_pmt()
        else:
            period_int = 0.0
        return unpaid + period_int



