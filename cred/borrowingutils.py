import pandas as pd


def defeasance(borrowing, dt):
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

    # confirm that borrowing as open_dt_offset and dfz_to_open attrs
    if not _has_attrs(borrowing, 'open_dt_offset', 'dfz_to_open', 'rate_provider'):
        raise AttributeError('Borrowing must have .open_dt_offset, .dfz_to_open, and .rate_provider attributes to defease.')

    # return None if dt is before start_date or after the final pmt date
    if (dt < borrowing.start_date) or (dt > borrowing.adjust_pmt_date(borrowing.end_date, borrowing.holidays)):
        return None

    # calc first open date
    open_date = None
    if borrowing.open_dt_offset is not None:
        open_date = borrowing.end_date - borrowing.open_dt_offset

    # if dt in open window
    if open_date and dt >= open_date:
        remaining_pmts = dict(borrowing.payments(dt, pmt_dt=True))
        next_pmt_dt = min([pmt for pmt in remaining_pmts.keys() if pmt >= dt])
        return borrowing.outstanding_principal(next_pmt_dt) + remaining_pmts[next_pmt_dt]

    # if dt prior to open date
    if borrowing.dfz_to_open:
        remaining_pmts = _pmts_between_dates(borrowing, dt, open_date)
    else:
        remaining_pmts = dict(borrowing.payments(first_dt=dt, pmt_dt=True))

    pv = 0
    for pmt_dt, pmt in remaining_pmts.items():
        pv += borrowing.rate_provider.df(dt, pmt_dt) * pmt

    return pv


def yield_maintenance(borrowing, dt):
    pass


def _pmts_between_dates(borrowing, start_dt, end_dt):
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


def _has_attrs(borrowing, *args):
    has_attr = [hasattr(borrowing, arg) for arg in args]
    return all(has_attr)
