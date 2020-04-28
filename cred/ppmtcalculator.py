

class BasePrepaymentCalculator:

    def __init__(self, ppmt_type):
        self.ppmt_type = ppmt_type

    def repayment_amount(self, borrowing, dt):
        raise NotImplementedError

    def __repr__(self):
        desc = 'Type: ' + self.ppmt_type + '\n'
        return desc


class Defeasance(BasePrepaymentCalculator):

    def __init__(self, df_func, open_dt_offset, dfz_to_open):
        super(Defeasance, self).__init__('defeasance')
        self.df = df_func
        self.open_dt_offset = open_dt_offset
        self.dfz_to_open = dfz_to_open

    def repayment_amount(self, borrowing, dt):
        """
        Returns total repayment cost including accrued and unpaid interest and estimated securities cost for repaying the
        borrowing on `dt` if the borrowing is subject to defeasance. Estimates defeasance cost by discounting future
        payments from their adjusted payment date. If the borrowing's property `dfz_to_open == True`, future cash flows are
        terminated on the open date at the outstanding principal balance plus any accrued and unpaid interest. The open
        window start date is determined by applying the borrowing's `open_dt_offset` to the borrowing end date.

        Realized defeasance costs will differ based on inefficiencies in the underlying securities portfolio, fees, and any
        variations in specific loan language (e.g. requirement that securities payout on the first business day prior to the
        unadjusted period end dates).
        """

        # return None if dt is before start_date or after the final pmt date
        if (dt < borrowing.start_date) or (dt > borrowing.adjust_pmt_date(borrowing.end_date, borrowing.holidays)):
            return None

        # calc first open date
        open_date = None
        if self.open_dt_offset is not None:
            open_date = borrowing.end_date - self.open_dt_offset

        # if dt in open window
        if open_date and dt >= open_date:
            remaining_pmts = dict(borrowing.payments(dt, pmt_dt=True))
            next_pmt_dt = min([pmt for pmt in remaining_pmts.keys() if pmt >= dt])
            return borrowing.outstanding_principal(next_pmt_dt) + remaining_pmts[next_pmt_dt]

        # if dt prior to open date
        if self.dfz_to_open:
            remaining_pmts = self._pmts_between_dates(borrowing, dt, open_date)
        else:
            remaining_pmts = dict(borrowing.payments(first_dt=dt, pmt_dt=True))

        pv = 0
        for pmt_dt, pmt in remaining_pmts.items():
            pv += self.df(dt, pmt_dt) * pmt

        return pv

    def _pmts_between_dates(self, borrowing, start_dt, end_dt):
        # TODO: Should this be a borrowing method?
        """
        Returns a dict of {payment date: payment} pairs for scheduled payments from `start_dt` to `end_dt` , inclusive,
        where the payment amount on `end_dt` equals the outstanding balance plus accrued and unpaid interest.
        """
        remaining_pmts = dict(borrowing.payments(first_dt=start_dt, last_dt=end_dt, pmt_dt=True))

        filtered_pmts = {k: v for k, v in remaining_pmts.items() if k <= end_dt}
        repayment_dt_pmt = filtered_pmts.get(end_dt, 0)
        repayment_dt_pmt += borrowing.outstanding_principal(end_dt) + borrowing.accrued_unpaid_int(end_dt)
        filtered_pmts[end_dt] = repayment_dt_pmt
        return filtered_pmts


    def __repr__(self):
        desc = super(Defeasance, self).__repr__()
        desc = desc + 'Open window offset: ' + str(self.open_dt_offset) + '\n'
        desc = desc + 'Defease to open date: ' + str(self.dfz_to_open) + '\n'
        desc = desc + 'Discount factors: ' + self.df.__name__ + '\n'
        return desc


class Stepdown(BasePrepaymentCalculator):

    def __init__(self, expiration_offsets, premiums):
        """
        Prepayment calculator for penalties based on the percentage of outstanding principal. Repayment amount equals
        the applicable premium times the outstanding principal balance plus interest through the next payment date. The
        lists of date offsets and premiums must be the same length. Assumes 0.0% premium for any dates after the final
        expiration offset.


        Parameters
        ----------
        expiration_offsets: list(dateutil.relativedelta.relativedelta)
            Expiration dates for each percentage level (i.e. threshold will apply up to but excluding the offset date).
            Offsets applied to the first regular period start date.
        premiums: list(float)

        """
        if len(expiration_offsets) != len(premiums):
            raise ValueError(f'Length of offsets ({len(expiration_offsets)} does not equal the length of thresholds '
                             f'{len(premiums)}.')

        super(Stepdown, self).__init__('stepdown')
        self.expiration_offsets = expiration_offsets
        self.premiums = premiums

    def repayment_amount(self, borrowing, dt):
        """
        Total cost of repayment including prepayment premium and interest through the next payment date. Assumes a
        0.0% premium for all dates after the last defined expiration offset. Returns `None` for any dates before the
        borrowing start date or after the final payment date.

        Parameters
        ----------
        borrowing: PeriodicBorrowing
            Borrowing to calculate the repayment amount on.
        dt: datetime-like
            Date of repayment.

        Returns
        -------
        float
        """
        pmts = borrowing.payments(pmt_dt=True)

        if dt < borrowing.start_date or dt > pmts[-1][0]:
            return None

        pmts = dict(pmts)
        next_pmt_dt = min([pmt for pmt in pmts.keys() if pmt >= dt])

        expiration_dts = [borrowing.start_date + offset for offset in self.expiration_offsets]
        premiums = dict(zip(expiration_dts, self.premiums))

        if dt >= max(expiration_dts):
            applicable_premium = 1.0
        else:
            expir_dt = min([ex_dt for ex_dt in expiration_dts if ex_dt > dt])
            applicable_premium = 1 + premiums[expir_dt]

        return applicable_premium * borrowing.outstanding_principal(dt) + pmts[next_pmt_dt]

    def __repr__(self):
        desc = super(Stepdown, self).__repr__()
        desc = desc + 'Expiration offsets: ' + repr(self.expiration_offsets) + '\n'
        desc = desc + 'Premiums: ' + repr(self.premiums) + '\n'
        return desc


class OpenPrepayment(BasePrepaymentCalculator):

    def __init__(self):
        super(OpenPrepayment, self).__init__('open_prepayment')

    def repayment_amount(self, borrowing, dt):
        """
        Returns the outstanding principal balance plus the payment amount due on the next payment date. Returns `None`
        if the repayment date is before the borrowing start date or after the final payment date.

        Parameters
        ----------
        borrowing: PeriodicBorrowing
            Borrowing to calculate repayment on
        dt: datetime-like
            Date of repayment

        Returns
        -------
        float
        """
        # TODO: this doesn't work for preceding pmt convention
        pmts = borrowing.payments(pmt_dt=True)

        if dt < borrowing.start_date or dt > pmts[-1][0]:
            return None

        pmts = dict(pmts)
        next_pmt_dt = min([pmt for pmt in pmts.keys() if pmt >= dt])

        return borrowing.outstanding_principal(dt) + pmts[next_pmt_dt]


    def __repr__(self):
        return super(OpenPrepayment, self).__repr__('open')
