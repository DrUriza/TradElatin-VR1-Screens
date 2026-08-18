from __future__ import annotations

from dash.development.base_component import Component

from screen_core.contextual_help import lookup_help
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


def _walk(node):
    if isinstance(node, Component):
        yield node
        children = getattr(node, "children", None)
        if isinstance(children, (list, tuple)):
            for child in children:
                yield from _walk(child)
        elif children is not None:
            yield from _walk(children)
    elif isinstance(node, (list, tuple)):
        for child in node:
            yield from _walk(child)


def _help_count(root) -> int:
    return sum(
        1
        for node in _walk(root)
        if getattr(node, "className", None) == "context-help-anchor"
    )


def test_screen_b_help_registry_is_complete():
    expected = {
        "prices": list(prices.ANALYSIS_GRAPH_ORDER),
        "cvd": list(cvd_volume_orderflow.ANALYSIS_ORDER),
        "open_interest": list(open_interest_and_funding.ANALYSIS_GRAPH_ORDER),
        "etf": list(etf_exchange_flows.ANALYSIS_ORDER),
        "miners": list(on_chain_miners.ANALYSIS_ORDER),
        "volatility": list(volatility_market_regimes.ANALYSIS_ORDER),
        "liquidations": list(long_short_liquidations.ANALYSIS_ORDER),
        "liquidity": [
            "depth_imbalance_pressure",
            "spread_market_impact_liquidity_stress",
            "liquidity_wall_concentration_vacuum",
            "whale_persistence_cancellation",
            "executed_liquidity_absorption",
            "liquidity_regime_hmi",
        ],
    }
    required_fields = (
        "what_measures",
        "price_relation",
        "cross_family_relation",
        "interpretation",
        "variable_type",
    )

    for family, indicator_ids in expected.items():
        for indicator_id in indicator_ids:
            entry = lookup_help(family, "screen_b", indicator_id)
            assert entry is not None, (family, indicator_id)
            for field in required_fields:
                assert str(entry.get(field) or "").strip(), (family, indicator_id, field)


def test_main_and_analysis_views_expose_context_help():
    cases = (
        (prices, None, 9, 6),
        (cvd_volume_orderflow, None, 10, 12),
        (open_interest_and_funding, None, 7, 6),
        (etf_exchange_flows, None, 12, 6),
        (on_chain_miners, None, 9, 6),
        (volatility_market_regimes, None, 10, 6),
        (long_short_liquidations, None, 15, 6),
        (liquidity_microstructure, "perpetual", 10, 6),
    )

    for module, market, expected_main, expected_analysis in cases:
        contract = load_contract(module.CONTRACT_FILE)
        main = module.render(contract, "main", market, None, None)
        analysis = module.render(contract, "analysis", market, None, None)
        assert _help_count(main) == expected_main, module.LABEL
        assert _help_count(analysis) == expected_analysis, module.LABEL
