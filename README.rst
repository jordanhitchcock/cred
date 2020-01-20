####
cred
####
**cred** is a Python package that provides flexible data structures for commercial real estate debt. It is designed to quickly answer common loan- and portfolio-level questions related to payment schedules, prepayment costs, dates, and scenario analytics. The package includes convenience functions for common loan structures.


The **Period** class represents the atomic cash flow unit. **Periods** have a start date, end date, reference to the previous **Period**, and a collection of rules that define the cash flow attributes of the **Period**'s schedule.

Users typically will not interact with **Periods** directly. Instead, users can use **Borrowings** to automatically create and manage a set of **Periods**.

The **PeriodicBorrowing** subclasses (specifically, **FixedRateBorrowing** and **FloatingRateBorrowing**) provide built-in interfaces for working with common fixed and floating rate debt. Calling the ``Borrowing.schedule()`` method will build and return a Pandas DataFrame with the loan schedule.


Examples
=======================

**FloatingRateBorrowings** require an index rate provider function that takes a datetime argument.

In this example, random numbers around 1.5% are returned for demonstration purposes.

.. code-block::

    from datetime import datetime
    import numpy as np

    from cred import FloatingRateBorrowing, open_repayment

    def rate(dt):
        return	np.random.lognormal(0.015, 0.001) - 1

    floating_borrowing = FloatingRateBorrowing(start_date=datetime(2020, 1, 1),
                                               end_date=datetime(2021, 1, 1),
                                               spread=0.03,
                                               index_rate_provider=rate,
                                               initial_principal=100)
    floating_borrowing.schedule()

Result:

.. code-block::

       start_date   end_date  bop_principal  index_rate  interest_rate  interest_payment  principal_payment  eop_principal
    0  2020-01-01 2020-02-01            100    0.013134       0.043134          0.371428                  0            100
    1  2020-02-01 2020-03-01            100    0.014265       0.044265          0.356579                  0            100
    2  2020-03-01 2020-04-01            100    0.013389       0.043389          0.373632                  0            100
    3  2020-04-01 2020-05-01            100    0.016527       0.046527          0.387729                  0            100
    4  2020-05-01 2020-06-01            100    0.014282       0.044282          0.381317                  0            100
    5  2020-06-01 2020-07-01            100    0.015641       0.045641          0.380339                  0            100
    6  2020-07-01 2020-08-01            100    0.014892       0.044892          0.386574                  0            100
    7  2020-08-01 2020-09-01            100    0.014530       0.044530          0.383454                  0            100
    8  2020-09-01 2020-10-01            100    0.015665       0.045665          0.380543                  0            100
    9  2020-10-01 2020-11-01            100    0.017037       0.047037          0.405038                  0            100
    10 2020-11-01 2020-12-01            100    0.015731       0.045731          0.381089                  0            100
    11 2020-12-01 2021-01-01            100    0.014520       0.044520          0.383367                100              0


Schedules are not stored in order to avoid accidentally accessing stale data. Instead, each call rebuilds most schedule data.

However, periods dates are calculated when the Borrowing is created and can be accessed in the ``Borrowing.dates`` attribute.
This allows users to prepare rates more efficiently. For example, fetch forward LIBOR projections in one batch rather than make individual calls as each period is calculated.


**FixedRateBorrowing** look very similar, but do not require an interest rate provider.

The additional convenience options in the block below (e.g. ``repayment``, ``frequency``, ``day_count``) can be used for **FloatingRateBorrowings** in the same manner.

The ``percent_of_principal`` function builds a function for calculating repayment costs based on the dates and step-downs. The default is open repayment.

Default ``frequency`` is monthly, and default ``day_count`` is actual/360.

.. code-block::

    from dateutil.relativedelta import relativedelta

    from cred import FixedRateBorrowing, percent_of_principal, thirty360

    step_down = percentage_of_principal(pd.date_range('2020-08-1', '2020-12-01', freq='MS'),
                                                      [0.05, 0.04, 0.03, 0.02, 0.01])

    fixed_borrowing = FixedRateBorrowing(start_date=datetime(2020, 1, 1),
                                   end_date=datetime(2021, 1, 1),
                                   frequency=relativedelta(months=3),
                                   coupon=0.05,
                                   initial_principal=100,
                                   repayment=step_down,
                                   day_count=thirty360)
    fixed_borrowing.schedule()

Result:

.. code-block::

      start_date   end_date  bop_principal  interest_rate  interest_payment  principal_payment  eop_principal
    0 2020-01-01 2020-04-01            100           0.05              1.25                  0            100
    1 2020-04-01 2020-07-01            100           0.05              1.25                  0            100
    2 2020-07-01 2020-10-01            100           0.05              1.25                  0            100
    3 2020-10-01 2021-01-01            100           0.05              1.25                100              0

In addition to calculating schedules, **Borrowings** also has the following method:

* **scheduled_cash_flow(self, attr_names, start_date=None, end_date=None)** : Returns cash flows defined in ``attr_names`` between (optional) start and end dates

**PeriodicBorrowings** have the additional methods:

* **repayment_amount(self, date)** : Implemented in subclasses, returns total repayment amount for ``date``
* **net_cash_flows(self, exit_date, pmt_attrs=[INTEREST_PAYMENT, PRINCIPAL_PAYMENT])** : Net payments through ``date`` including initial funding and repayment costs

For example, to calculate the effective borrowing cost if the previous fixed borrowing was prepaid after three quarters:

.. code-block::

    >>> import numpy as np
    >>> cash_flows = fixed_borrowing.net_cash_flows(datetime(2020, 10, 1))
    >>> np.irr(cash_flows) * 4
    0.0670659774603255

