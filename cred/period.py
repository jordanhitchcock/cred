
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
        Adds `value` as an attribute of the period object named `name` and marks it as a payment. Payment attributes are
        included in `period.schedule`.

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
        Adds `value` as an attribute named `name` to the period marks it as a display field. Display field attributes are included in `period.schedule`.

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

    def __init__(self, i):
        super().__init__(i)
        self.start_date_col = None
        self.end_date_col = None
        self.pmt_date_col = None
        self.interest_pmt_cols = []
        self.principal_pmt_cols = []
        self.bop_principal_col = None

    def add_start_date(self, dt, name=START_DATE):
        """Add an attribute to the object and mark it as the period start date. There can only be one start date. Also
        marks the attribute as a field that should be added to the period schedule."""
        self.start_date_col = name
        self.schedule_cols.append(name)
        self.__setattr__(name, dt)

    def add_end_date(self, dt, name=END_DATE):
        """Add an attribute to the object and mark it as the period end date. There can only be one end date. Also
        marks the attribute as a field that should be added to the period schedule."""
        self.end_date_col = name
        self.schedule_cols.append(name)
        self.__setattr__(name, dt)

    def add_pmt_date(self, dt, name=PAYMENT_DATE):
        """Add an attribute to the object and mark it as the period payment date. There can only be one payment date.
        Also marks the attribute as a field that should be added to the period schedule."""
        self.pmt_date_col = name
        self.schedule_cols.append(name)
        if not hasattr(self, PAYMENT_DATE):
            self.__setattr__(name, dt)

    def add_interest_pmt(self, amt, name=INTEREST_PAYMENT):
        """Adds the value as a period attribute and marks it as an interest payment. Also added as an attribute that
        should be included in the schedule."""
        self.interest_pmt_cols.append(name)
        self.payment_cols.append(name)
        self.schedule_cols.append(name)
        self.__setattr__(name, amt)

    def add_principal_pmt(self, amt, name=PRINCIPAL_PAYMENT):
        """Adds the value as a period attribute and marks it as a principal payment. Also added as an attribute that
        should be included in the schedule."""
        self.principal_pmt_cols.append(name)
        self.payment_cols.append(name)
        self.schedule_cols.append(name)
        self.__setattr__(name, amt)

    def add_bop_principal(self, amt, name=BOP_PRINCIPAL):
        """Adds the value as a period attribute and marks it as the beginning of period principal balance. Each period
        can only have one beginning principal balance attribute. Also added as an attribute that should be included in
        the schedule."""
        self.bop_principal_col = name
        self.schedule_cols.append(name)
        self.__setattr__(name, amt)

    def get_start_date(self):
        """Period start date"""
        return self.__getattribute__(self.start_date_col)

    def get_end_date(self):
        """Period end date"""
        return self.__getattribute__(self.end_date_col)

    def get_pmt_date(self):
        """Returns the sum of attributes marked as payments, interest payments, principal payments"""
        return self.__getattribute__(self.pmt_date_col)

    def get_interest_pmt(self):
        """Returns the sum of attributes marked as interest payments"""
        return sum([self.__getattribute__(n) for n in self.interest_pmt_cols])

    def get_principal_pmt(self):
        """Returns the sum of attributes marked as principal payments"""
        return sum([self.__getattribute__(n) for n in self.principal_pmt_cols])

    def get_bop_principal(self):
        """Beginning of period (BoP) principal amount"""
        return self.__getattribute__(self.bop_principal_col)

