


class AbstractBorrowingPeriod:

    def __init__(self, period_id, previous_period, next_period, schedule={}):
        self.period_id = period_id
        self.previous_period = previous_period
        self.next_period = next_period
        self.schedule = schedule

    def build_schedule(self):
        raise NotImplementedError


def borrowing_period_factory(name, **build_func):
    """
    Create a custom borrowing period subclass.
    :param name: Name of new subclass
    :param build_func: Keyword arguments of functions to be used in building the period schedule. Functions will be
    applied in the order that they are listed and must take a single period argument of the invoking period object.
    Return values will be added to the period's schedule dictionary with the parameter name as the key.
    :return: Custom AbstractBorrowingPeriod subclass
    """
    custom_period = type(name, (AbstractBorrowingPeriod,), {})

    def custom_build_func(self):
        for fname, func in build_func.items():
            value = func(self)
            self.schedule[fname] = value

    custom_period.build_schedule = custom_build_func

    return custom_period


# def bop_principal(interest_period):
#     if interest_period.previous_period == None:
#         return 1000
#
#     interest_period.previous_period.schedule['bop_principal']
#
#
# if __name__ == '__main__':
#     CustomPeriod = borrowing_period_factory('OnlyBOP', bop_principal=bop_principal)
#     new_period = CustomPeriod(1, None, None)
#     new_period.build_schedule()
#     print(new_period.schedule)

