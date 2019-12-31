
import pytest

from cred.borrowing import Borrowing


def test_fixed_io_schedule(borrowing):
    actual = borrowing.schedule()

    expected = {
        'period': [1, 2, 3, 4, 5, 6],
        'eop_principal': [100] * 6,
        'interest_rate': [0.05] * 6,
        'interest': [5] * 6,
        'principal': [0] * 5 + [100],
        'eop_principal': [100] * 4 + [0]
    }

    assert actual == expected


def test_floating_io_schedule(borrowing):
    actual = borrowing.schedule()

    expected = {
        'period': [1, 2, 3, 4, 5, 6],
        'eop_principal': [100] * 6,
        'index_rate': [0.02] * 3 + [0.03] * 3,
        'interest_rate': [0.05] * 3 + [0.06] * 3,
        'interest': [5] * 3 + [6] * 3,
        'principal': [0] * 5 + [100],
        'eop_principal': [100] * 4 + [0]
    }

    assert actual == expected