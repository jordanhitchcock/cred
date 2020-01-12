####
cred
####
**cred** is a Python package that provides reliable, intuitive, and flexible data structures for commercial real estate debt. It is designed to quickly answer common loan- and portfolio-level questions related to payment schedules, prepayment costs, dates, and scenario analytics. The package includes convenience functions for common loan structures.


The **Period** class represents the atomic cash flow unit. **Periods** have a start date, end date, reference to the previous **Period**, and a collection of rules that define the cash flow attributes of the **Period**'s schedule.

Users typically will not interact with **Periods** directly. Instead, users can use **Borrowings** to automatically create and manage a set of **Periods**.

The **FixedRateBorrowing** and **FloatingRateBorrowing** subclasses provide built-in interfaces for working with most fixed and floating rate debt. Calling the ``Borrowing.schedule()`` method will build and return a Pandas DataFrame with the loan schedule.

By default, **FixedRateBorrowing** and **FloatingRateBorrowing** will assume Actual/360 day count with London and New York business days. Both these assumptions can be overridden.

Examples
=======================
Fixed rate borrowing:

.. code-block::

    from datetime import datetime
    from dateutil.relativedelta import relativedelta

    from cred.borrowing import FixedRateBorrowing

    borrowing = FixedRateBorrowing(datetime(2019, 1, 1), datetime(2020, 1, 1), relativedelta(months=1), 0.05, 100)
    borrowing.schedule()

Result:

.. code-block::

       start_date   end_date adj_start_date adj_end_date  bop_principal  interest_rate  interest_payment  principal  eop_principal
    0  2019-01-01 2019-02-01     2019-01-02   2019-02-01            100           0.05          0.430556          0            100
    1  2019-02-01 2019-03-01     2019-02-01   2019-03-01            100           0.05          0.388889          0            100
    2  2019-03-01 2019-04-01     2019-03-01   2019-04-01            100           0.05          0.430556          0            100
    3  2019-04-01 2019-05-01     2019-04-01   2019-05-01            100           0.05          0.416667          0            100
    4  2019-05-01 2019-06-01     2019-05-01   2019-06-03            100           0.05          0.430556          0            100
    5  2019-06-01 2019-07-01     2019-06-03   2019-07-01            100           0.05          0.416667          0            100
    6  2019-07-01 2019-08-01     2019-07-01   2019-08-01            100           0.05          0.430556          0            100
    7  2019-08-01 2019-09-01     2019-08-01   2019-09-03            100           0.05          0.430556          0            100
    8  2019-09-01 2019-10-01     2019-09-03   2019-10-01            100           0.05          0.416667          0            100
    9  2019-10-01 2019-11-01     2019-10-01   2019-11-01            100           0.05          0.430556          0            100
    10 2019-11-01 2019-12-01     2019-11-01   2019-12-02            100           0.05          0.416667          0            100
    11 2019-12-01 2020-01-01     2019-12-02   2020-01-02            100           0.05          0.430556        100              0


**FloatingRateBorrowings** require an index rate provider object that return the period interest when ``obj.rate(datetime)`` is called.

In this example, random decimals between 1.0% and 2.0% are returned for demonstration purposes.

.. code-block::

    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    from random import uniform

    from cred.borrowing import FloatingRateBorrowing

    class IndexProvider:
        def rate(self, date):
            return uniform(0.01, 0.02)

    borrowing = FloatingRateBorrowing(datetime(2019, 1, 1), datetime(2020, 1, 1), relativedelta(months=1), 0.03, IndexProvider(), 100)
    borrowing.schedule()

Result:

.. code-block::

       start_date   end_date adj_start_date adj_end_date  bop_principal  index_rate  interest_rate  interest_payment  principal  eop_principal
    0  2019-01-01 2019-02-01     2019-01-01   2019-02-01            100    0.019818       0.049818          0.428985          0            100
    1  2019-02-01 2019-03-01     2019-02-01   2019-03-01            100    0.018731       0.048731          0.379022          0            100
    2  2019-03-01 2019-04-01     2019-03-01   2019-04-01            100    0.016475       0.046475          0.400202          0            100
    3  2019-04-01 2019-05-01     2019-04-01   2019-05-01            100    0.018305       0.048305          0.402539          0            100
    4  2019-05-01 2019-06-01     2019-05-01   2019-06-03            100    0.016142       0.046142          0.397332          0            100
    5  2019-06-01 2019-07-01     2019-06-03   2019-07-01            100    0.017164       0.047164          0.393034          0            100
    6  2019-07-01 2019-08-01     2019-07-01   2019-08-01            100    0.016721       0.046721          0.402320          0            100
    7  2019-08-01 2019-09-01     2019-08-01   2019-09-03            100    0.014624       0.044624          0.384260          0            100
    8  2019-09-01 2019-10-01     2019-09-03   2019-10-01            100    0.014312       0.044312          0.369263          0            100
    9  2019-10-01 2019-11-01     2019-10-01   2019-11-01            100    0.015006       0.045006          0.387551          0            100
    10 2019-11-01 2019-12-01     2019-11-01   2019-12-02            100    0.012184       0.042184          0.351532          0            100
    11 2019-12-01 2020-01-01     2019-12-02   2020-01-02            100    0.017640       0.047640          0.410232        100              0