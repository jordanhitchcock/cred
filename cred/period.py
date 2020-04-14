
START_DATE = 'start_date'
END_DATE = 'end_date'
PAYMENT_DATE = 'payment_date'


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
        self.balance_cols = []
        self.payment_cols = []
        self.display_field_cols = ['index']
        self.schedule_cols = ['index']

    def add_balance(self, value, name):
        """
        Adds `value` named `name` to the period as a balance. Balance attributes are included in `period.schedule` and summed in `period.outstanding_principal`.

        Parameters
        ----------
        value
            Numerical value of attribute
        name: str
            Name of attribute
        """
        self.balance_cols.append(name)
        self.schedule_cols.append(name)
        self.__setattr__(name, value)

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

    def outstanding_principal(self):
        """Returns the sum of payment attributes."""
        amt = 0
        for v in self.balance_cols:
            amt += self.__getattribute__(v)
        return amt

    def payment(self):
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
        self.__setattr__(name, dt)

