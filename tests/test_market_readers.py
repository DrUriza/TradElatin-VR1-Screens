from __future__ import annotations

import json
from pathlib import Path

from screen_core.market_readers import extract_flow_snapshot, extract_positioning_snapshot


ROOT = Path(__file__).resolve().parents[1]


def test_flow_requires_processing_published_percentages() -> None:
    chart = {
        "status": "available",
        "series_by_timeframe": {
            "1m": {
                "timeframe": "1m",
                "bars": [
                    {"timestamp": 1, "delta_buy_sell_usd": 1234.0},
                ],
            }
        },
    }
    snapshot = extract_flow_snapshot(chart, "1m")
    assert snapshot.status == "unavailable"
    assert snapshot.buy_percent is None
    assert snapshot.sell_percent is None


def test_flow_reads_published_percentages_without_deriving_from_delta() -> None:
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
                    {"timestamp": 1, "net_flow_pct": 4.0},
                    {"timestamp": 2, "net_flow_pct": 26.0},
                ],
            }
        },
    }
    snapshot = extract_flow_snapshot(chart, "1m")
    assert snapshot.status == "available"
    assert snapshot.buy_percent == 63.0
    assert snapshot.sell_percent == 37.0
    assert snapshot.net_value == 26.0
    assert snapshot.exchange == "Binance"
    assert snapshot.timeframe == "1m"
    assert snapshot.history == ((1, 4.0), (2, 26.0))


def test_explicit_missing_flow_timeframe_does_not_fallback() -> None:
    chart = {
        "series_by_timeframe": {
            "1m": {"current": {"buy_flow_pct": 60, "sell_flow_pct": 40}},
        }
    }
    snapshot = extract_flow_snapshot(chart, "30m")
    assert snapshot.status == "unavailable"
    assert snapshot.reason == "timeframe_not_published"


def test_current_liquidations_fixture_top_position_uses_published_shares() -> None:
    contract = json.loads(
        (ROOT / "data" / "contracts" / "long_short_liquidations_VR1_FINAL.json").read_text(encoding="utf-8")
    )
    snapshot = extract_positioning_snapshot(contract, variant="top_position", exchange="aggregate")
    assert snapshot.status == "available"
    assert snapshot.long_percent is not None
    assert snapshot.short_percent is not None
    assert 0 <= snapshot.long_percent <= 100
    assert 0 <= snapshot.short_percent <= 100
    assert snapshot.ratio is not None


def test_positioning_does_not_derive_percentages_from_ratio() -> None:
    contract = {
        "selectors": {"exchange": {"selected": "aggregate", "options": ["aggregate"]}},
        "charts": {
            "long_short_positioning": {
                "status": "available",
                "points": [{"timestamp": 1, "top_account_ratio": 1.2}],
            }
        },
    }
    snapshot = extract_positioning_snapshot(contract, variant="top_account", exchange="aggregate")
    assert snapshot.status == "unavailable"
    assert snapshot.long_percent is None
    assert snapshot.short_percent is None
    assert snapshot.ratio == 1.2
