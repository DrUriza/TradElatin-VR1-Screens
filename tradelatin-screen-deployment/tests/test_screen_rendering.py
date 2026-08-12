from __future__ import annotations

from dash.development.base_component import Component

from screen_core.contract_loader import load_contract, selector_spec
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

MODULES = (
    prices,
    cvd_volume_orderflow,
    open_interest_and_funding,
    etf_exchange_flows,
    on_chain_miners,
    volatility_market_regimes,
    long_short_liquidations,
    liquidity_microstructure,
)


def test_each_main_screen_renders() -> None:
    for module in MODULES:
        contract = load_contract(module.CONTRACT_FILE)
        _, market = selector_spec(contract, "market")
        _, timeframe = selector_spec(contract, "timeframe")
        _, range_id = selector_spec(contract, "range")
        component = module.render(contract, "main", market, timeframe, range_id)
        assert isinstance(component, Component)
