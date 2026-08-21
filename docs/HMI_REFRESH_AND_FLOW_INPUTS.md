# TradELATIN VR1 — HMI refresh and flow input boundary

This document describes the **Screens/HMI consumption boundary only**. Screens never computes market percentages, delta normalization, positioning shares, or market classifications.

## Family refresh cadence

| Family | HMI cadence |
| --- | ---: |
| Prices | 5 s automatic + manual Reload |
| CVD | 30 s automatic + manual Reload |
| Open Interest | 60 s automatic + manual Reload |
| ETF | manual Reload only |
| On-Chain | manual Reload only |
| Volatility | manual Reload only |
| Liquidations | manual Reload only |
| Liquidity | manual Reload only |

If `TRADELATIN_PROCESSING_REFRESH_URL` is configured, HMI sends a non-blocking HTTP `POST` containing only the active family:

```json
{
  "family": "cvd",
  "reason": "auto",
  "contract_file": "cvd_volume_orderflow_VR1_FINAL.json",
  "requested_at": 0.0
}
```

The request body is an integration signal, not a market calculation. While Processing works, HMI keeps the last valid contract visible and displays `UPDATING`. HMI polls the contract revision and only swaps the visible state after the new JSON parses successfully.

If no Processing refresh endpoint is configured, the same timers/buttons simply re-read the currently active family JSON so Screens remains standalone and debuggable.

## Spot / Futures / Perpetual Flow

Preferred runtime chart names:

- `charts.spot_flow`
- `charts.perpetual_flow` or `charts.futures_flow`

Preferred per-timeframe shape:

```json
{
  "series_by_timeframe": {
    "1m": {
      "timeframe": "1m",
      "current": {
        "buy_flow_pct": 63.0,
        "sell_flow_pct": 37.0,
        "net_flow_pct": 26.0,
        "exchange": "Binance"
      },
      "bars": [
        {"timestamp": 0, "net_flow_pct": 12.0}
      ]
    }
  }
}
```

HMI does **not** derive `buy_flow_pct`/`sell_flow_pct` from `delta_buy_sell_usd`, a ratio, volume, or any other field. If the percentage shares are absent, the visual is `UNAVAILABLE` or `PARTIAL`.

The renderer supports the legacy `delta_buy_sell_spot` / `delta_buy_sell_futures` chart paths only as containers for future Processing-published flow fields; legacy delta is never converted into percentages by HMI.

## Long / Short Ratio

Preferred positioning fields are already-computed shares plus the ratio:

- Top Position: `long_share_top_position`, `short_share_top_position`, `top_position_ratio`
- Top Account: `long_share_top_account`, `short_share_top_account`, `top_account_ratio`
- Global Account: `long_share_global_account`, `short_share_global_account`, `global_account_ratio`

HMI supports exchange/timeframe nested structures when Processing publishes them, for example:

```text
charts.long_short_positioning
└── series_by_exchange
    └── Binance
        └── series_by_timeframe
            ├── 1m
            ├── 5m
            ├── 15m
            ├── 30m
            ├── 1h
            └── 4h
```

HMI never derives Long% / Short% from an L/S ratio. A variant with only a ratio but no published percentage shares remains unavailable in the 0–100% primary bar.
