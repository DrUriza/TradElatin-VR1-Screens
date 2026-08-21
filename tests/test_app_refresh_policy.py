from __future__ import annotations

import app
from screens import (
    cvd_volume_orderflow,
    etf_exchange_flows,
    liquidity_microstructure,
    long_short_liquidations,
    on_chain_miners,
    open_interest_and_funding,
    prices,
    volatility_market_regimes,
)


def test_auto_refresh_policy_is_family_fixed() -> None:
    assert app.sync_refresh_policy(prices.ROUTE)[1:] == (False, 5_000)
    assert app.sync_refresh_policy(cvd_volume_orderflow.ROUTE)[1:] == (False, 30_000)
    assert app.sync_refresh_policy(open_interest_and_funding.ROUTE)[1:] == (False, 60_000)


def test_other_families_are_manual_only() -> None:
    for module in (
        etf_exchange_flows,
        on_chain_miners,
        volatility_market_regimes,
        long_short_liquidations,
        liquidity_microstructure,
    ):
        _style, disabled, _interval = app.sync_refresh_policy(module.ROUTE)
        assert disabled is True
