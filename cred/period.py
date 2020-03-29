from dateutil.relativedelta import relativedelta
from pandas.tseries.holiday import AbstractHolidayCalendar, HolidayCalendarFactory

from cred.interest_rate import actual360, thirty360
from cred.businessdays import FederalReserveHolidays, LondonBankHolidays, modified_following


class PeriodMeta(type):
    def __new__(cls, name, bases, dct):
        p = super().__new__(cls, name, bases, dct)

        payment_names = []
        balance_names = []
        data_field_names = []
        for k, v in dct.items():
            if hasattr(v, '_payment'):
                payment_names.append(v.__name__)
            if hasattr(v, '_balance'):
                balance_names.append(v.__name__)
            if hasattr(v, '_data_field'):
                data_field_names.append(v.__name__)

        if not hasattr(p, 'payment_names'):
            p.payment_names = []
        if not hasattr(p, 'balance_names'):
            p.balance_names = []
        if not hasattr(p, 'data_field_names'):
            p.data_field_names = []

        p.payment_names += payment_names
        p.balance_names += balance_names
        p.data_field_names += data_field_names
        return p


class Period(metaclass=PeriodMeta):

    payment_names = []
    balance_names = []
    data_field_names = []

    def __init__(self, period_id, borrowing):
        """
        Base Period class.
        :param period_id: Zero-index id
        :param borrowing: Borrowing that manages Period instance
        """
        self.period_id = period_id
        self.borrowing = borrowing

    def build_schedule(self):
        """
        Called to build period schedule. Override in subclasses to return dictionary of {schedule_name: value} items.
        :return: dict
        """
        raise NotImplementedError

    @staticmethod
    def payment(f):
        f._payment = True
        return f

    @staticmethod
    def balance(f):
        f._balance = True
        return f

    @staticmethod
    def data_field(f):
        f._data_field = True
        return f


class RegularPeriod(Period):
    """
    Convenience class for common fixed rate loan structures.
    """

    def build_schedule(self):
        return {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'payment_date': self.pmt_date,
            'bop_balance': self.bop_balance,
            'interest_rate': self.interest_rate,
            'interest_payment': self.interest_pmt,
            'principal_payment': self.principal_pmt,
            'payment': self.pmt,
            'eop_balance': self.eop_balance
        }

    def start_date(self):
        pass

    def end_date(self):
        pass

    def pmt_date(self):
        pass

    def bop_balance(self):
        pass

    def interest_rate(self):
        return self.borrowing.interest_rate(self.period_id)

    def interest_pmt(self):
        pass

    def principal_pmt(self):
        pass

    def pmt(self):
        pass

    def eop_balance(self):
        pass



















# Date functions
def adj_date(unadj_date_attr, calendars=[FederalReserveHolidays, LondonBankHolidays], convention=modified_following):
    """
    Factory to create a Period rule that returns date adjusted for calendar holidays based on the convention for date at the specified Period attribute.

    :param unadj_date_attr: Name of unadjusted Period date attribute
    :type unadj_date_attr: str
    :param calendars: List of Pandas HolidayCalendars
    :type calendars: list
    :param convention: Adjustment convention
    :type convention: func
    :return: A Period rule function for adjusted date
    """
    holiday_cal = calendars[0]
    if len(calendars) > 0:

        for additional_cal in calendars:
            holiday_cal = HolidayCalendarFactory(holiday_cal.__name__ + additional_cal.__name__, holiday_cal, additional_cal)

    def adj_func(period):
        unadj_date = period.__getattribute__(unadj_date_attr)

        return modified_following(unadj_date, holiday_cal())

    return adj_func

