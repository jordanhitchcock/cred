import pytest

from cred.interest_rate import fixed_rate, floating_rate



class Provider:
    def spread(self, period):
         return 0.03

    def index_rate(self, period):
        return 0.01

    def coupon(self, period):
        return 0.05

rate_provider = Provider()


@pytest.mark.parametrize(
    'spread_provider,index_provider,period,expected_value',
    [
        (rate_provider, rate_provider, None, 0.04),
        (None, rate_provider, None, pytest.raises(ValueError)),
        (rate_provider, None, None, pytest.raises(ValueError)),
        (None, None, None, pytest.raises(ValueError)),
    ]
)
def test_floating_rate(spread_provider, index_provider, period, expected_value):
    if (spread_provider is not None) & (index_provider is not None):
        actual_func = floating_rate(spread_provider, index_provider)

        assert actual_func(period) == expected_value
    else:
        with expected_value:
            assert floating_rate(spread_provider, index_provider) == expected_value


@pytest.mark.parametrize(
    'coupon_provider,period,expected_value',
    [
        (rate_provider, None, 0.05),
        (None, None, pytest.raises(ValueError))
    ]
)
def test_fixed_rate_factory(coupon_provider, period, expected_value):
    if coupon_provider is not None:
        actual_func = fixed_rate(coupon_provider)

        assert actual_func(period) == expected_value

    else:
        with expected_value:
            assert fixed_rate(coupon_provider) == expected_value





