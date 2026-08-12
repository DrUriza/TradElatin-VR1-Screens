from __future__ import annotations

from screen_core.contract_loader import load_contract
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


def test_all_eight_contracts_load() -> None:
    assert len(MODULES) == 8
    for module in MODULES:
        contract = load_contract(module.CONTRACT_FILE)
        assert isinstance(contract, dict)
        assert contract


def test_routes_are_unique() -> None:
    routes = [module.ROUTE for module in MODULES]
    assert len(routes) == len(set(routes))
