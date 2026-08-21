from __future__ import annotations

from screen_core.contract_loader import load_contract
from screens import cvd_volume_orderflow, long_short_liquidations


def test_cvd_flow_figure_uses_processing_percentages() -> None:
    chart = {
        "status": "available",
        "exchange": "Binance",
        "series_by_timeframe": {
            "1m": {
                "timeframe": "1m",
                "current": {
                    "buy_flow_pct": 63.0,
                    "sell_flow_pct": 37.0,
                    "net_flow_pct": 26.0,
                },
                "bars": [
                    {"timestamp": 1, "net_flow_pct": 10.0},
                    {"timestamp": 2, "net_flow_pct": 26.0},
                ],
            }
        },
    }
    figure = cvd_volume_orderflow._delta_buy_sell_figure(chart, timeframe="1m")
    bars = [trace for trace in figure.data if trace.type == "bar"]
    assert len(bars) == 2
    assert list(bars[0].x) == [63.0]
    assert list(bars[1].x) == [37.0]
    annotations = " ".join(str(item.text) for item in figure.layout.annotations)
    assert "NET +26.0%" in annotations
    assert "BINANCE" in annotations
    assert "TF 1m" in annotations


def test_cvd_legacy_delta_is_not_converted_to_flow_percentages() -> None:
    chart = {
        "series_by_timeframe": {
            "1m": {"bars": [{"timestamp": 1, "delta_buy_sell_usd": 999.0}]}
        }
    }
    figure = cvd_volume_orderflow._delta_buy_sell_figure(chart, timeframe="1m")
    assert not [trace for trace in figure.data if trace.type == "bar"]
    annotations = " ".join(str(item.text) for item in figure.layout.annotations)
    assert "UNAVAILABLE" in annotations


def test_long_short_primary_bar_uses_published_top_position_shares() -> None:
    contract = load_contract(long_short_liquidations.CONTRACT_FILE)
    figure = long_short_liquidations._long_short_positioning_figure(
        contract,
        variant="top_position",
        exchange="aggregate",
        timeframe=None,
        height=205,
    )
    bars = [trace for trace in figure.data if trace.type == "bar"]
    assert len(bars) == 2
    assert bars[0].name == "LONG"
    assert bars[1].name == "SHORT"
    assert 0 <= float(bars[0].x[0]) <= 100
    assert 0 <= float(bars[1].x[0]) <= 100


def test_long_short_does_not_derive_top_account_percent_from_ratio() -> None:
    contract = load_contract(long_short_liquidations.CONTRACT_FILE)
    figure = long_short_liquidations._long_short_positioning_figure(
        contract,
        variant="top_account",
        exchange="aggregate",
        timeframe=None,
        height=205,
    )
    assert not [trace for trace in figure.data if trace.type == "bar"]
    annotations = " ".join(str(item.text) for item in figure.layout.annotations)
    assert "UNAVAILABLE" in annotations
