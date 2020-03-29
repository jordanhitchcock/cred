
class Borrowing:

    def __init__(self, start_date, end_date, freq, period_type, first_regular_start_date=None):
        self.start_date = start_date
        self.end_date = end_date
        self.freq = freq
        if first_regular_start_date is not None:
            self.first_regular_start_date = first_regular_start_date
        else:
            self.first_regular_start_date = start_date



    def create_periods(self, cls):
        periods = []



