

def fixed_rate(coupon_provider):
    if coupon_provider is None:
        raise ValueError('Must provide a coupon provider.')

    def rate_func(period):
        return coupon_provider.coupon(period)

    return rate_func


def floating_rate(spread_provider, index_provider):
    if (spread_provider is None) or (index_provider is None):
        raise ValueError('Must provide both a spread and index rate provider.')

    def rate_func(borrowing_period):
        spread = spread_provider.spread(borrowing_period)
        index_rate = index_provider.index_rate(borrowing_period)
        return index_rate + spread

    return rate_func

