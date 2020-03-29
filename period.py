
START_DATE = 'start_date'
END_DATE = 'end_date'
PAYMENT_DATE = 'payment_date'


class Period:

    def __init__(self, i):
        self.index = i
        self.balance_cols = []
        self.payment_cols = []
        self.display_field_cols = ['index']
        self.schedule_cols = ['index']

    def add_balance(self, value, name):
        self.balance_cols.append(name)
        self.schedule_cols.append(name)
        self.__setattr__(name, value)

    def add_payment(self, value, name):
        self.payment_cols.append(name)
        self.schedule_cols.append(name)
        self.__setattr__(name, value)

    def add_display_field(self, value, name):
        self.display_field_cols.append(name)
        self.schedule_cols.append(name)
        self.__setattr__(name, value)

    def outstanding_principal(self):
        amt = 0
        for v in self.balance_cols:
            amt += self.__getattribute__(v)
        return amt

    def payment(self):
        pmt = 0
        for v in self.payment_cols:
            pmt += self.__getattribute__(v)
        return pmt

    def schedule(self):
        return {name: self.__getattribute__(name) for name in self.schedule_cols}


class InterestPeriod(Period):

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

