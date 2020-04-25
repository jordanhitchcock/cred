
START_DATE = 'start_date'
END_DATE = 'end_date'
PAYMENT_DATE = 'payment_date'
INTEREST_PAYMENT = 'interest_payment'
PRINCIPAL_PAYMENT = 'principal_payment'
BOP_PRINCIPAL = 'bop_principal'


class Period:
    """
    Superclass for InterestPeriod.

    Parameters
    ----------
    i: int
        Zero-based period index (e.g. the fourth period will have index 3)
    """

    def __init__(self, i):
        self.index = i
        self.payment_cols = []
        self.display_field_cols = ['index']
        self.schedule_cols = ['index']

    def add_payment(self, value, name):
        """
        Adds `value` named `name` to the period as a payment. Payment attributes are included in `period.schedule` and summed in period.payment.

        Parameters
        ----------
        value
            Numerical value of attribute
        name: str
            Name of attribute
        """
        self.payment_cols.append(name)
        self.schedule_cols.append(name)
        self.__setattr__(name, value)

    def add_display_field(self, value, name):
        """
        Adds `value` named `name` to the period as a display field. Data field attributes are included in `period.schedule`.

        Parameters
        ----------
        value
            Numerical value of attribute
        name: str
            Name of attribute
        """
        self.display_field_cols.append(name)
        self.schedule_cols.append(name)
        self.__setattr__(name, value)

    def get_payment(self):
        """Returns the sum of payment attributes."""
        pmt = 0
        for v in self.payment_cols:
            pmt += self.__getattribute__(v)
        return pmt

    def schedule(self):
        """Returns the period schedule as a {name: value} dictionary."""
        return {name: self.__getattribute__(name) for name in self.schedule_cols}


class InterestPeriod(Period):
    """
    Period type used by PeriodicBorrowing and its subclasses.
    """
    # TODO: add better documentation for the date methods

    def __init__(self, i):
        super().__init__(i)
        self.start_date_col = None
        self.end_date_col = None
        self.pmt_date_col = None
        self.interest_pmt_cols = []
        self.principal_pmt_cols = []
        self.bop_principal_col = None

    def add_start_date(self, dt, name=START_DATE):
        self.start_date_col = name
        self.schedule_cols.append(name)
        self.__setattr__(name, dt)

    def add_end_date(self, dt, name=END_DATE):
        self.end_date_col = name
        self.schedule_cols.append(name)
        self.__setattr__(name, dt)

    def add_pmt_date(self, dt, name=PAYMENT_DATE):
        self.pmt_date_col = name
        self.schedule_cols.append(name)
        if not hasattr(self, PAYMENT_DATE):
            self.__setattr__(name, dt)

    def add_interest_pmt(self, amt, name=INTEREST_PAYMENT):
        self.interest_pmt_cols.append(name)
        self.payment_cols.append(name)
        self.schedule_cols.append(name)
        self.__setattr__(name, amt)

    def add_principal_pmt(self, amt, name=PRINCIPAL_PAYMENT):
        self.principal_pmt_cols.append(name)
        self.payment_cols.append(name)
        self.schedule_cols.append(name)
        self.__setattr__(name, amt)

    def add_bop_principal(self, amt, name=BOP_PRINCIPAL):
        self.bop_principal_col = name
        self.schedule_cols.append(name)
        self.__setattr__(name, amt)

    def get_start_date(self):
        return self.__getattribute__(self.start_date_col)

    def get_end_date(self):
        return self.__getattribute__(self.end_date_col)

    def get_pmt_date(self):
        return self.__getattribute__(self.pmt_date_col)

    def get_interest_pmt(self):
        return sum([self.__getattribute__(n) for n in self.interest_pmt_cols])

    def get_principal_pmt(self):
        return sum([self.__getattribute__(n) for n in self.principal_pmt_cols])

