from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import plotly.graph_objects as go
from dash import Input, Output, callback, ctx, dcc, html, no_update

from screen_core.components import (
    contract_warning,
    kpi_grid,
    reference_gallery,
    screen_header,
    screen_page,
)
from screen_core.contract_loader import load_contract
from screen_core.formatting import compact_number


ROUTE = "/cvd-orderflow"
LABEL = "CVD"
CONTRACT_FILE = "cvd_volume_orderflow_screen.json"
HAS_ANALYSIS = True

REFERENCE_IMAGES = [
    "CVD/02_CVD_A.png",
    "CVD/02_CVD_B_Spot.png",
    "CVD/02_CVD_B_Futuros.png",
]

GREEN = "#17d49b"
RED = "#ff506e"
BG = "#06111d"
PLOT_BG = "#071522"
GRID = "rgba(91,126,155,.16)"
TEXT = "#d9e8f5"
MUTED = "#7f96aa"

SELECTION_STORE_ID = "cvd-technical-selection"
ANALYSIS_CONTENT_ID = "cvd-analysis-content"

TREND_OPTIONS = [
    {"label": "EMA 9", "value": "ema_9"},
    {"label": "EMA 21", "value": "ema_21"},
    {"label": "EMA 50", "value": "ema_50"},
    {"label": "SMA 20", "value": "sma_20"},
    {"label": "SMA 50", "value": "sma_50"},
    {"label": "SMA 100", "value": "sma_100"},
    {"label": "SMA 200", "value": "sma_200"},
    {"label": "WMA 20", "value": "wma_20"},
    {"label": "WMA 50", "value": "wma_50"},
]

BAND_OPTIONS = [
    {
        "label": "Bollinger Bands (20, 2)",
        "value": "bollinger_bands",
    },
    {
        "label": "Canal de Regresión",
        "value": "regression_channel",
    },
]

DERIVED_OPTIONS = [
    {
        "label": "ADX / DI+ / DI- (14)",
        "value": "adx",
    },
    {
        "label": "Bollinger Band Width (20, 2)",
        "value": "bollinger_band_width",
    },
]

MOMENTUM_OPTIONS = [
    {
        "label": "MACD (12, 26, 9)",
        "value": "macd",
    },
    {
        "label": "RSI (14)",
        "value": "rsi",
    },
    {
        "label": "TSI (25, 13)",
        "value": "tsi",
    },
    {
        "label": "Stochastic (14, 3, 3)",
        "value": "stochastic",
    },
    {
        "label": "Williams %R (14)",
        "value": "williams_r",
    },
    {
        "label": "CCI (20)",
        "value": "cci",
    },
]

VOLATILITY_OPTIONS = [
    {
        "label": "ATR (14)",
        "value": "atr",
    },
    {
        "label": "Wasserstein Distance",
        "value": "wasserstein_distance",
    },
]

DEFAULT_TREND = ["ema_9", "ema_21", "sma_50"]
DEFAULT_BANDS = ["bollinger_bands"]
DEFAULT_DERIVED: list[str] = []
DEFAULT_MOMENTUM: list[str] = []
DEFAULT_VOLATILITY: list[str] = []

ANALYSIS_ORDER = (
    "macd",
    "rsi",
    "tsi",
    "adx",
    "stochastic",
    "williams_r",
    "cci",
    "atr",
    "wasserstein_distance",
    "bollinger_band_width",
)

INDICATOR_TITLES = {
    "macd": "MACD (12, 26, 9)",
    "rsi": "RSI (14)",
    "tsi": "TSI (25, 13)",
    "adx": "ADX / DI+ / DI- (14)",
    "stochastic": "STOCHASTIC (14, 3, 3)",
    "williams_r": "WILLIAMS %R (14)",
    "cci": "CCI (20)",
    "atr": "ATR (14)",
    "wasserstein_distance": "WASSERSTEIN DISTANCE",
    "bollinger_band_width": "BOLLINGER BAND WIDTH (20, 2)",
}

TRACE_COLORS = {
    "ema_9": "#2f80ff",
    "ema_21": "#00c2ff",
    "ema_50": "#9b51e0",
    "sma_20": "#00d4ff",
    "sma_50": "#f2c94c",
    "sma_100": "#dc59d7",
    "sma_200": "#ff334f",
    "wma_20": "#a879ff",
    "wma_50": "#ff8a3d",
    "bollinger_upper": "#2d7dff",
    "bollinger_middle": "#65a8ff",
    "bollinger_lower": "#2d7dff",
    "regression_upper": "#e6a93a",
    "regression_middle": "#f4cf65",
    "regression_lower": "#e6a93a",
    "macd": "#0788e8",
    "signal": "#ff5d00",
    "rsi": "#b45bea",
    "tsi": "#1ed1dd",
    "adx": "#d3c2a8",
    "di_plus": "#20d05c",
    "di_minus": "#ff273b",
    "k": "#008fff",
    "d": "#ff6a00",
    "williams_r": "#b64fe6",
    "cci": "#14c8dc",
    "atr": "#ff9f00",
    "wasserstein_distance": "#3c94ed",
    "bollinger_band_width": "#17c8ce",
}

CVD_LOCAL_CSS = """
.cvd-main-grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 286px;
    gap: 8px;
    align-items: stretch;
}

.cvd-market-stack-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
    height: 590px;
}

.cvd-market-stack {
    display: grid;
    min-width: 0;
    grid-template-rows: 350px 232px;
    gap: 8px;
    height: 590px;
}

.cvd-chart-card,
.cvd-indicator-panel,
.cvd-analysis-market {
    min-width: 0;
    border: 1px solid #123148;
    background: #06111d;
}

.cvd-indicator-panel {
    height: 590px;
    padding: 8px 10px 12px;
    color: #dbe7ef;
    overflow-y: auto;
    box-sizing: border-box;
}

.cvd-analysis-button {
    width: 100%;
    height: 28px;
    border: 1px solid #1766d6;
    border-radius: 4px;
    color: #3f8cff;
    background: #06111d;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: .4px;
    cursor: pointer;
}

.cvd-selector-heading {
    margin-top: 10px;
    margin-bottom: 8px;
    color: #dceaf5;
    font-size: 10px;
    font-weight: 700;
}

.cvd-selector-note {
    margin-bottom: 9px;
    color: #7f96aa;
    font-size: 8px;
    line-height: 1.35;
}

.cvd-indicator-group {
    border-top: 1px solid #10283a;
    padding-top: 8px;
    margin-top: 8px;
}

.cvd-indicator-group-title {
    margin-bottom: 5px;
    color: #7f91a0;
    font-size: 8px;
    text-transform: uppercase;
}

.cvd-analysis-only {
    border: 1px dashed #235274;
    border-radius: 4px;
    padding: 7px;
    background: rgba(18,54,78,.18);
}

.cvd-analysis-only .cvd-indicator-group-title {
    color: #5aa9e6;
}

.cvd-checklist label {
    display: inline-flex !important;
    width: 50%;
    gap: 5px;
    align-items: center;
    margin: 3px 0;
    color: #c6d5df;
    font-size: 8px;
}

.cvd-checklist input {
    accent-color: #2f80ff;
}


.cvd-analysis-shell {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.cvd-analysis-market {
    padding: 8px;
}

.cvd-analysis-market-title {
    color: #4fc3ff;
    font-size: 11px;
    font-weight: 700;
    margin: 1px 0 8px;
}

.cvd-analysis-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 5px;
    align-items: stretch;
}

.cvd-analysis-card {
    min-width: 0;
    min-height: 180px;
    border: 1px solid #123247;
    border-radius: 4px;
    background: linear-gradient(180deg, #061522 0%, #04111c 100%);
    overflow: hidden;
    box-sizing: border-box;
}

.cvd-analysis-card-title {
    height: 26px;
    display: flex;
    align-items: center;
    padding: 0 9px;
    border-bottom: 1px solid #102b3d;
    color: #dce6ec;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: .1px;
    box-sizing: border-box;
}

@media (max-width: 1200px) {
    .cvd-market-stack-grid {
        grid-template-columns: 1fr;
    }

    .cvd-analysis-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 900px) {
    .cvd-main-grid {
        grid-template-columns: 1fr;
    }

    .cvd-analysis-grid {
        grid-template-columns: 1fr;
    }
}

.analysis-back-row {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    margin: 0 0 7px;
}

.analysis-back-button {
    height: 27px;
    padding: 0 12px;
    border: 1px solid #1a5f86;
    border-radius: 4px;
    background: #06111d;
    color: #65c9ff;
    font-family: inherit;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: .25px;
    cursor: pointer;
}

.analysis-back-button:hover {
    border-color: #2ea8ff;
    background: #082033;
    color: #dff5ff;
}


.cvd-analysis-layout {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 314px;
    gap: 8px;
    align-items: start;
}

.cvd-analysis-main {
    min-width: 0;
}

.cvd-summary-column {
    min-width: 0;
    display: grid;
    gap: 6px;
    align-content: start;
}

.cvd-summary-panel,
.cvd-strength-legend {
    border: 1px solid #123247;
    border-radius: 4px;
    background: linear-gradient(180deg, #061522 0%, #04111c 100%);
    overflow: hidden;
}

.cvd-summary-title,
.cvd-strength-title {
    min-height: 27px;
    display: flex;
    align-items: center;
    padding: 0 9px;
    border-bottom: 1px solid #102b3d;
    color: #dce6ec;
    font-size: 9px;
    font-weight: 700;
}

.cvd-summary-head {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 54px 73px 48px;
    gap: 4px;
    padding: 6px 8px;
    border-bottom: 1px solid #102b3d;
    color: #8194a4;
    font-size: 6.5px;
    text-transform: uppercase;
}

.cvd-summary-section {
    display: flex;
    align-items: center;
    gap: 5px;
    min-height: 23px;
    padding: 0 8px;
    border-bottom: 1px solid rgba(16,43,61,.8);
    font-size: 8px;
    font-weight: 700;
}

.cvd-summary-section-marker {
    width: 0;
    height: 0;
    border-top: 4px solid transparent;
    border-bottom: 4px solid transparent;
    border-left: 5px solid currentColor;
}

.cvd-summary-row {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 54px 73px 48px;
    gap: 4px;
    align-items: center;
    min-height: 24px;
    padding: 0 8px;
    border-bottom: 1px solid rgba(16,43,61,.62);
    font-size: 7.2px;
}

.cvd-summary-name {
    color: #c7d2da;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.cvd-summary-value {
    color: #dce6ec;
    text-align: right;
    font-variant-numeric: tabular-nums;
}

.cvd-summary-signal {
    text-align: right;
    font-size: 6.8px;
    font-weight: 700;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.cvd-summary-strength {
    display: inline-flex;
    justify-content: flex-end;
    gap: 2px;
}

.cvd-summary-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #46525d;
}

.cvd-strength-body {
    display: grid;
    gap: 4px;
    padding: 7px 9px 8px;
}

.cvd-strength-row {
    display: grid;
    grid-template-columns: 58px 1fr;
    align-items: center;
    color: #c0cbd2;
    font-size: 7px;
}

@media (max-width: 1320px) {
    .cvd-analysis-layout {
        grid-template-columns: minmax(0, 1fr) 290px;
    }
}

@media (max-width: 920px) {
    .cvd-analysis-layout {
        grid-template-columns: 1fr;
    }
}
"""


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _dt(value: Any) -> Any:
    try:
        return datetime.fromtimestamp(
            float(value),
            tz=timezone.utc,
        )
    except (TypeError, ValueError, OSError):
        return value


def _cvd_stylesheet() -> html.Link:
    return html.Link(
        rel="stylesheet",
        href=(
            "data:text/css;charset=utf-8,"
            + quote(CVD_LOCAL_CSS, safe="")
        ),
    )


def _checklist(
    component_id: str,
    options: list[dict[str, str]],
    value: list[str],
) -> dcc.Checklist:
    return dcc.Checklist(
        id=component_id,
        options=options,
        value=value,
        className="cvd-checklist",
        persistence="cvd-controls-v1",
        persistence_type="memory",
    )


def _selector_group(
    title: str,
    checklist: dcc.Checklist,
    *,
    analysis_only: bool = False,
) -> html.Div:
    class_name = (
        "cvd-indicator-group cvd-analysis-only"
        if analysis_only
        else "cvd-indicator-group"
    )

    children: list[Any] = [
        html.Div(
            title,
            className="cvd-indicator-group-title",
        ),
    ]

    if analysis_only:
        children.append(
            html.Div(
                "Gráficas independientes en Pantalla B; "
                "no se superponen a las velas CVD.",
                className="cvd-selector-note",
            )
        )

    children.append(checklist)

    return html.Div(
        className=class_name,
        children=children,
    )


def _indicator_panel() -> html.Div:
    return html.Div(
        className="cvd-indicator-panel",
        children=[
            html.Div(
                className="analysis-launch-row",
                style={
                    "display": "grid",
                    "gridTemplateColumns": "minmax(0, 1fr) 34px",
                    "gap": "4px",
                    "marginBottom": "12px",
                },
                children=[
                    dcc.Link(
                        "ANÁLISIS TÉCNICO FUNDAMENTAL",
                        href=f"{ROUTE}/analysis",
                        className="cvd-analysis-button",
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "width": "auto",
                            "marginBottom": "0",
                            "textDecoration": "none",
                        },
                    ),
                    html.A(
                        "↗",
                        href=f"{ROUTE}/analysis",
                        target="_blank",
                        rel="noopener noreferrer",
                        title="Abrir análisis en una nueva pestaña",
                        className="cvd-analysis-button",
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "width": "auto",
                            "marginBottom": "0",
                            "padding": "0",
                            "textDecoration": "none",
                        },
                    ),
                    # Legacy callback target kept hidden during migration.
                    html.Button(
                        "",
                        id="cvd-open-analysis",
                        n_clicks=0,
                        type="button",
                        style={"display": "none"},
                    ),
                ],
            ),
            html.Div(
                "INDICADORES",
                className="cvd-selector-heading",
            ),
            html.Div(
                "Mismo conjunto técnico de Prices, "
                "aplicado al OHLC de cada CVD. "
                "Volumen y MFI se excluyen de esta sección.",
                className="cvd-selector-note",
            ),
            _selector_group(
                "TENDENCIA · SOBRE CVD",
                _checklist(
                    "cvd-trend-selectors",
                    TREND_OPTIONS,
                    DEFAULT_TREND,
                ),
            ),
            _selector_group(
                "BANDAS Y CANALES · SOBRE CVD",
                _checklist(
                    "cvd-band-selectors",
                    BAND_OPTIONS,
                    DEFAULT_BANDS,
                ),
            ),
            _selector_group(
                "ANÁLISIS DERIVADO · PANTALLA B",
                _checklist(
                    "cvd-derived-selectors",
                    DERIVED_OPTIONS,
                    DEFAULT_DERIVED,
                ),
                analysis_only=True,
            ),
            _selector_group(
                "MOMENTUM · PANTALLA B",
                _checklist(
                    "cvd-momentum-selectors",
                    MOMENTUM_OPTIONS,
                    DEFAULT_MOMENTUM,
                ),
                analysis_only=True,
            ),
            _selector_group(
                "VOLATILIDAD · PANTALLA B",
                _checklist(
                    "cvd-volatility-selectors",
                    VOLATILITY_OPTIONS,
                    DEFAULT_VOLATILITY,
                ),
                analysis_only=True,
            ),
        ],
    )


def _default_selection() -> dict[str, list[str]]:
    return {
        "trend": list(DEFAULT_TREND),
        "bands": list(DEFAULT_BANDS),
        "derived_analysis": list(DEFAULT_DERIVED),
        "momentum": list(DEFAULT_MOMENTUM),
        "volatility": list(DEFAULT_VOLATILITY),
    }


def _selection_payload(
    trend: list[str] | None,
    bands: list[str] | None,
    derived: list[str] | None,
    momentum: list[str] | None,
    volatility: list[str] | None,
) -> dict[str, list[str]]:
    return {
        "trend": _unique(trend or []),
        "bands": _unique(bands or []),
        "derived_analysis": _unique(derived or []),
        "momentum": _unique(momentum or []),
        "volatility": _unique(volatility or []),
    }


def _technical_block(
    contract: dict[str, Any],
    market: str,
    timeframe: str | None,
) -> dict[str, Any]:
    technical = _safe_dict(
        contract.get("technical_analysis")
    )
    market_block = _safe_dict(
        _safe_dict(technical.get("markets")).get(market)
    )
    timeframes = _safe_dict(
        market_block.get("timeframes")
    )

    selected = (
        timeframe
        if timeframe in timeframes
        else next(iter(timeframes), "")
    )

    return _safe_dict(timeframes.get(selected))


def _source_chart(
    contract: dict[str, Any],
    market: str,
) -> dict[str, Any]:
    chart_id = {
        "spot": "cvd_spot",
        "futures": "cvd_futures",
    }[market]

    return _safe_dict(
        _safe_dict(contract.get("charts")).get(chart_id)
    )


def _source_points(
    contract: dict[str, Any],
    market: str,
    timeframe: str | None,
) -> tuple[list[dict[str, Any]], str]:
    chart = _source_chart(contract, market)
    timeframes = _safe_dict(
        chart.get("series_by_timeframe")
    )

    selected = (
        timeframe
        if timeframe in timeframes
        else str(chart.get("selected_timeframe") or "")
    )

    if selected not in timeframes:
        selected = next(iter(timeframes), "")

    block = _safe_dict(timeframes.get(selected))

    candles = [
        candle
        for candle in _safe_list(block.get("candles"))
        if isinstance(candle, dict)
    ]

    # CVD charts are contractually candlestick-only. Do not reinterpret
    # line points or fabricate OHLC in the HMI.
    required_fields = (
        "timestamp",
        "open",
        "high",
        "low",
        "close",
    )

    candles = [
        candle
        for candle in candles
        if all(
            candle.get(field) is not None
            for field in required_fields
        )
    ]

    return candles, selected


def _overlay_series(
    technical_block: dict[str, Any],
    indicator_id: str,
) -> tuple[list[Any], list[Any]]:
    timestamps = [
        _dt(value)
        for value in _safe_list(
            technical_block.get("timestamps")
        )
    ]
    overlays = _safe_dict(
        technical_block.get("overlays")
    )

    if indicator_id.startswith(("ema_", "sma_", "wma_")):
        series = _safe_dict(
            _safe_dict(
                overlays.get("moving_averages")
            ).get("series")
        )
        return timestamps, _safe_list(
            series.get(indicator_id)
        )

    return timestamps, []


def _add_main_cross_markers(
    fig: go.Figure,
    technical_block: dict[str, Any],
    selected: set[str],
    points: list[dict[str, Any]],
) -> None:
    timestamps_to_point = {
        int(point["timestamp"]): point
        for point in points
        if point.get("timestamp") is not None
    }

    events = [
        event
        for event in _safe_list(
            technical_block.get("events")
        )
        if isinstance(event, dict)
        and event.get("event_group")
        in {"moving_average_cross", "channel_cross"}
    ]

    grouped: dict[tuple[int, str], list[dict[str, Any]]] = {}

    for event in events:
        calculation = _safe_dict(
            event.get("calculation")
        )
        first = str(
            calculation.get("first_series") or ""
        )
        second = str(
            calculation.get("second_series") or ""
        )

        requirements: set[str] = set()

        for series_id in (first, second):
            if series_id.startswith("regression_channel."):
                requirements.add("regression_channel")
            elif series_id.startswith("bollinger_bands."):
                requirements.add("bollinger_bands")
            else:
                requirements.add(series_id)

        if not requirements.issubset(selected):
            continue

        timestamp = event.get("timestamp")
        signal = str(event.get("signal") or "")

        try:
            key = (int(timestamp), signal)
        except (TypeError, ValueError):
            continue

        grouped.setdefault(key, []).append(event)

    for (timestamp, signal), cluster in grouped.items():
        point = timestamps_to_point.get(timestamp)

        if not point:
            continue

        # Keep one marker per direction/candle to avoid clutter.
        event = cluster[0]

        high = point.get("high")
        low = point.get("low")

        if not isinstance(high, (int, float)) or not isinstance(low, (int, float)):
            continue

        candle_range = max(
            abs(float(high) - float(low)),
            1e-9,
        )

        if signal == "bullish":
            y = float(low) - candle_range * .45
            symbol = "arrow-up"
            color = GREEN
        elif signal == "bearish":
            y = float(high) + candle_range * .45
            symbol = "arrow-down"
            color = RED
        else:
            continue

        fig.add_trace(
            go.Scatter(
                x=[_dt(timestamp)],
                y=[y],
                mode="markers",
                marker={
                    "symbol": symbol,
                    "size": 9,
                    "color": color,
                    "line": {
                        "width": 1,
                        "color": "#03101a",
                    },
                },
                showlegend=False,
                hovertemplate=(
                    f"{event.get('event_id')}"
                    "<extra></extra>"
                ),
            )
        )


def _cvd_candlestick_figure(
    contract: dict[str, Any],
    market: str,
    timeframe: str | None,
    selected_overlays: list[str],
) -> go.Figure:
    points, selected_timeframe = _source_points(
        contract,
        market,
        timeframe,
    )
    technical = _technical_block(
        contract,
        market,
        selected_timeframe,
    )
    selected = set(selected_overlays)

    fig = go.Figure()

    if not points:
        fig.add_annotation(
            text="UNAVAILABLE",
            x=.5,
            y=.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font={"color": MUTED},
        )
        return fig

    x = [_dt(point.get("timestamp")) for point in points]

    fig.add_trace(
        go.Candlestick(
            x=x,
            open=[point.get("open") for point in points],
            high=[point.get("high") for point in points],
            low=[point.get("low") for point in points],
            close=[point.get("close") for point in points],
            increasing={
                "line": {"color": GREEN},
                "fillcolor": GREEN,
            },
            decreasing={
                "line": {"color": RED},
                "fillcolor": RED,
            },
            name="CVD",
            showlegend=False,
        )
    )

    overlays = _safe_dict(
        technical.get("overlays")
    )
    moving = _safe_dict(
        _safe_dict(
            overlays.get("moving_averages")
        ).get("series")
    )

    for indicator_id in (
        "ema_9",
        "ema_21",
        "ema_50",
        "sma_20",
        "sma_50",
        "sma_100",
        "sma_200",
        "wma_20",
        "wma_50",
    ):
        if indicator_id not in selected:
            continue

        values = _safe_list(
            moving.get(indicator_id)
        )

        if not values:
            continue

        size = min(len(x), len(values))

        fig.add_trace(
            go.Scatter(
                x=x[-size:],
                y=values[-size:],
                mode="lines",
                line={
                    "color": TRACE_COLORS[indicator_id],
                    "width": 1.05,
                },
                name=indicator_id.upper(),
                showlegend=False,
                hovertemplate=(
                    f"{indicator_id.upper()}: "
                    "%{y:,.2f}<extra></extra>"
                ),
            )
        )

    if "bollinger_bands" in selected:
        block = _safe_dict(
            overlays.get("bollinger_bands")
        )
        series = _safe_dict(block.get("series"))

        for name, dash in (
            ("upper", "dot"),
            ("middle", "dash"),
            ("lower", "dot"),
        ):
            values = _safe_list(series.get(name))
            size = min(len(x), len(values))

            fig.add_trace(
                go.Scatter(
                    x=x[-size:],
                    y=values[-size:],
                    mode="lines",
                    line={
                        "color": TRACE_COLORS[
                            f"bollinger_{name}"
                        ],
                        "width": 1,
                        "dash": dash,
                    },
                    showlegend=False,
                    hovertemplate=(
                        f"BB {name.upper()}: "
                        "%{y:,.2f}<extra></extra>"
                    ),
                )
            )

    if "regression_channel" in selected:
        block = _safe_dict(
            overlays.get("regression_channel")
        )
        series = _safe_dict(block.get("series"))

        for name, dash in (
            ("upper", "dot"),
            ("middle", "dash"),
            ("lower", "dot"),
        ):
            values = _safe_list(series.get(name))
            size = min(len(x), len(values))

            fig.add_trace(
                go.Scatter(
                    x=x[-size:],
                    y=values[-size:],
                    mode="lines",
                    line={
                        "color": TRACE_COLORS[
                            f"regression_{name}"
                        ],
                        "width": 1,
                        "dash": dash,
                    },
                    showlegend=False,
                    hovertemplate=(
                        f"REG {name.upper()}: "
                        "%{y:,.2f}<extra></extra>"
                    ),
                )
            )

    _add_main_cross_markers(
        fig,
        technical,
        selected,
        points,
    )

    title = {
        "spot": "CVD SPOT",
        "futures": "CVD FUTURES / PERPETUALS",
    }[market]

    fig.update_layout(
        title={
            "text": (
                f"{title} · {selected_timeframe.upper()}"
            ),
            "x": .01,
            "font": {
                "size": 11,
                "color": TEXT,
            },
        },
        height=350,
        paper_bgcolor=BG,
        plot_bgcolor=PLOT_BG,
        margin={
            "l": 42,
            "r": 12,
            "t": 38,
            "b": 28,
        },
        font={
            "family": "Inter, Segoe UI, sans-serif",
            "color": TEXT,
            "size": 8,
        },
        hovermode="x unified",
        showlegend=False,
        uirevision=(
            f"cvd-{market}-{selected_timeframe}"
        ),
        xaxis_rangeslider_visible=False,
    )

    fig.update_xaxes(
        gridcolor=GRID,
        zeroline=False,
        tickfont={
            "color": MUTED,
            "size": 7,
        },
    )
    fig.update_yaxes(
        gridcolor=GRID,
        zeroline=True,
        zerolinecolor="rgba(91,151,194,.42)",
        tickfont={
            "color": MUTED,
            "size": 7,
        },
    )

    return fig



def _delta_buy_sell_figure(
    chart: dict[str, Any] | None,
    *,
    timeframe: str | None,
    height: int = 232,
) -> go.Figure:
    fig = go.Figure()

    if not isinstance(chart, dict):
        return fig

    by_timeframe = _safe_dict(
        chart.get("series_by_timeframe")
    )

    selected = (
        timeframe
        if timeframe in by_timeframe
        else str(chart.get("selected_timeframe") or "")
    )

    if selected not in by_timeframe:
        selected = next(iter(by_timeframe), "")

    block = _safe_dict(
        by_timeframe.get(selected)
    )
    bars = [
        bar
        for bar in _safe_list(block.get("bars"))
        if isinstance(bar, dict)
    ]

    if not bars:
        fig.add_annotation(
            text="UNAVAILABLE",
            x=.5,
            y=.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font={"color": MUTED},
        )
        return fig

    x = [
        _dt(bar.get("timestamp"))
        for bar in bars
    ]
    delta_values = [
        float(
            bar.get("delta_buy_sell_usd")
            or 0.0
        )
        for bar in bars
    ]
    ma_values = [
        bar.get("delta_ma_21")
        for bar in bars
    ]

    fig.add_trace(
        go.Bar(
            x=x,
            y=delta_values,
            name="Delta",
            marker_color=[
                GREEN
                if value >= 0
                else RED
                for value in delta_values
            ],
            showlegend=False,
            hovertemplate=(
                "DELTA: %{y:,.2f}"
                "<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=x,
            y=ma_values,
            mode="lines",
            name="Delta MA(21)",
            line={
                "color": "#f2a900",
                "width": 1.4,
            },
            connectgaps=False,
            showlegend=False,
            hovertemplate=(
                "MA(21): %{y:,.2f}"
                "<extra></extra>"
            ),
        )
    )

    maximum = max(
        [
            abs(value)
            for value in delta_values
        ]
        + [1.0]
    )

    fig.update_layout(
        title={
            "text": (
                f"{chart.get('title') or ''}"
                f" · {selected.upper()}"
            ),
            "x": .01,
            "font": {
                "size": 9,
                "color": TEXT,
            },
        },
        height=height,
        paper_bgcolor=BG,
        plot_bgcolor=PLOT_BG,
        margin={
            "l": 42,
            "r": 10,
            "t": 32,
            "b": 24,
        },
        font={
            "family": (
                "Inter, Segoe UI, sans-serif"
            ),
            "color": TEXT,
            "size": 7,
        },
        hovermode="x unified",
        showlegend=False,
        bargap=.14,
        uirevision=(
            f"{chart.get('chart_id')}-{selected}"
        ),
    )

    fig.update_xaxes(
        gridcolor=GRID,
        zeroline=False,
        tickfont={
            "color": MUTED,
            "size": 7,
        },
    )
    fig.update_yaxes(
        range=[
            -maximum * 1.12,
            maximum * 1.12,
        ],
        gridcolor=GRID,
        zeroline=True,
        zerolinecolor=(
            "rgba(91,151,194,.62)"
        ),
        zerolinewidth=1,
        tickfont={
            "color": MUTED,
            "size": 7,
        },
        tickformat="~s",
    )

    return fig


def _indicator_figure(
    contract: dict[str, Any],
    market: str,
    timeframe: str | None,
    indicator_id: str,
) -> go.Figure:
    technical = _technical_block(
        contract,
        market,
        timeframe,
    )
    indicators = _safe_dict(
        technical.get("indicators")
    )
    block = _safe_dict(
        indicators.get(indicator_id)
    )
    timestamps = [
        _dt(value)
        for value in _safe_list(block.get("timestamps"))
    ]
    series = _safe_dict(block.get("series"))
    fig = go.Figure()

    for name, values_raw in series.items():
        values = _safe_list(values_raw)
        size = min(len(timestamps), len(values))

        if size <= 0:
            continue

        current_x = timestamps[-size:]
        current_y = values[-size:]

        if (
            indicator_id == "macd"
            and name == "histogram"
        ):
            fig.add_trace(
                go.Bar(
                    x=current_x,
                    y=current_y,
                    marker_color=[
                        GREEN
                        if isinstance(value, (int, float))
                        and value >= 0
                        else RED
                        for value in current_y
                    ],
                    showlegend=False,
                    opacity=.8,
                )
            )
            continue

        color = TRACE_COLORS.get(
            name,
            TRACE_COLORS.get(
                indicator_id,
                "#22c7e8",
            ),
        )

        fig.add_trace(
            go.Scatter(
                x=current_x,
                y=current_y,
                mode="lines",
                line={
                    "color": color,
                    "width": 1.15,
                },
                showlegend=False,
                connectgaps=False,
                hovertemplate=(
                    f"{name.upper()}: "
                    "%{y:.5f}<extra></extra>"
                ),
            )
        )

    for threshold in _safe_list(
        block.get("thresholds")
    ):
        if not isinstance(threshold, dict):
            continue

        value = threshold.get("value")

        if not isinstance(value, (int, float)):
            continue

        role = str(threshold.get("role") or "")
        color = (
            "rgba(255,80,110,.58)"
            if role == "overbought"
            else "rgba(23,212,155,.58)"
            if role == "oversold"
            else "rgba(140,155,168,.42)"
        )

        fig.add_hline(
            y=float(value),
            line_color=color,
            line_dash="dot",
            line_width=1,
        )

    # Contractual buy/sell arrows for MACD, Stochastic and ADX.
    event_pairs = {
        "macd": {
            "macd_above_signal",
            "macd_below_signal",
        },
        "stochastic": {
            "k_above_d",
            "k_below_d",
        },
        "adx": {
            "di_plus_above_di_minus",
            "di_plus_below_di_minus",
        },
    }

    allowed = event_pairs.get(indicator_id, set())

    if allowed:
        for event in _safe_list(
            technical.get("events")
        ):
            if not isinstance(event, dict):
                continue

            if event.get("event_id") not in allowed:
                continue

            calculation = _safe_dict(
                event.get("calculation")
            )
            first_value = calculation.get("first_value")
            second_value = calculation.get("second_value")

            if not isinstance(first_value, (int, float)):
                continue

            if not isinstance(second_value, (int, float)):
                continue

            y = (
                float(first_value)
                + float(second_value)
            ) / 2.0

            signal = event.get("signal")

            if signal == "bullish":
                symbol = "arrow-up"
                color = GREEN
            elif signal == "bearish":
                symbol = "arrow-down"
                color = RED
            else:
                continue

            fig.add_trace(
                go.Scatter(
                    x=[_dt(event.get("timestamp"))],
                    y=[y],
                    mode="markers",
                    marker={
                        "symbol": symbol,
                        "size": 8,
                        "color": color,
                        "line": {
                            "width": 1,
                            "color": "#03101a",
                        },
                    },
                    showlegend=False,
                    hovertemplate=(
                        f"{event.get('event_id')}"
                        "<extra></extra>"
                    ),
                )
            )

    fig.update_layout(
        height=152,
        paper_bgcolor=BG,
        plot_bgcolor=PLOT_BG,
        margin={
            "l": 32,
            "r": 8,
            "t": 6,
            "b": 20,
        },
        font={
            "family": "Inter, Segoe UI, sans-serif",
            "size": 8,
            "color": MUTED,
        },
        hovermode="x unified",
        showlegend=False,
        barmode="relative",
        uirevision=(
            f"cvd-analysis-{market}-"
            f"{timeframe}-{indicator_id}"
        ),
    )

    fig.update_xaxes(
        showticklabels=False,
        gridcolor=GRID,
        zeroline=False,
    )
    if indicator_id in {"rsi", "stochastic"}:
        fig.update_yaxes(
            gridcolor=GRID,
            zeroline=False,
            range=[0, 100],
            ticksuffix="%",
        )
    elif indicator_id == "tsi":
        fig.update_yaxes(
            gridcolor=GRID,
            zeroline=True,
            zerolinecolor="rgba(91,151,194,.35)",
            range=[-100, 100],
        )
    else:
        fig.update_yaxes(
            gridcolor=GRID,
            zeroline=True,
            zerolinecolor="rgba(91,151,194,.35)",
        )

    return fig


def _selected_analysis_ids(
    selection: Any,
) -> list[str]:
    payload = _safe_dict(selection)

    chosen = set(
        _safe_list(
            payload.get("derived_analysis")
        )
        + _safe_list(payload.get("momentum"))
        + _safe_list(payload.get("volatility"))
    )

    return [
        indicator_id
        for indicator_id in ANALYSIS_ORDER
        if indicator_id in chosen
    ]


def _cvd_strength_dots(count: Any, color: str) -> html.Span:
    try:
        strength = max(1, min(5, int(count)))
    except (TypeError, ValueError):
        strength = 1

    return html.Span(
        className="cvd-summary-strength",
        children=[
            html.Span(
                className="cvd-summary-dot",
                style={"background": color if index < strength else "#46525d"},
            )
            for index in range(5)
        ],
    )


def _cvd_summary_panel(
    block: dict[str, Any],
    selected_ids: list[str],
    title: str = "RESUMEN DE INDICADORES",
) -> html.Div:
    indicators = _safe_dict(block.get("indicators"))
    chosen = [
        indicator_id
        for indicator_id in ANALYSIS_ORDER
        if indicator_id in set(selected_ids)
    ]

    body: list[Any] = [
        html.Div(
            className="cvd-summary-head",
            children=[
                html.Span("INDICADOR"),
                html.Span("VALOR", style={"textAlign": "right"}),
                html.Span("SEÑAL", style={"textAlign": "right"}),
                html.Span("FUERZA", style={"textAlign": "right"}),
            ],
        )
    ]

    sections = (
        ("trend", "TENDENCIA", "#20d05c"),
        ("momentum", "MOMENTUM", "#a65cff"),
        ("volatility", "VOLATILIDAD", "#ffab00"),
        ("distribution", "DISTRIBUCIÓN", "#2ea8ff"),
    )

    for section_id, section_title, section_color in sections:
        section_rows = []

        for indicator_id in chosen:
            indicator = _safe_dict(indicators.get(indicator_id))
            summary = _safe_dict(indicator.get("summary"))

            if summary.get("section") != section_id:
                continue

            signal_color = str(summary.get("signal_color") or "#93a2ad")

            section_rows.append(
                html.Div(
                    className="cvd-summary-row",
                    children=[
                        html.Span(
                            str(summary.get("label") or indicator_id.upper()),
                            className="cvd-summary-name",
                        ),
                        html.Span(
                            str(summary.get("display_value") or "—"),
                            className="cvd-summary-value",
                        ),
                        html.Span(
                            str(summary.get("signal") or "—"),
                            className="cvd-summary-signal",
                            style={"color": signal_color},
                        ),
                        _cvd_strength_dots(
                            summary.get("strength"),
                            signal_color,
                        ),
                    ],
                )
            )

        if not section_rows:
            continue

        body.append(
            html.Div(
                className="cvd-summary-section",
                style={"color": section_color},
                children=[
                    html.Span(className="cvd-summary-section-marker"),
                    html.Span(section_title),
                ],
            )
        )
        body.extend(section_rows)

    return html.Div(
        className="cvd-summary-panel",
        children=[
            html.Div(title, className="cvd-summary-title"),
            *body,
        ],
    )


def _cvd_strength_legend() -> html.Div:
    rows = (
        ("MUY FUERTE", 5, "#20d05c"),
        ("FUERTE", 4, "#20d05c"),
        ("MODERADA", 3, "#ffab00"),
        ("DÉBIL", 2, "#ff8a00"),
        ("MUY DÉBIL", 1, "#ff3d55"),
    )

    return html.Div(
        className="cvd-strength-legend",
        children=[
            html.Div("LEYENDA FUERZA", className="cvd-strength-title"),
            html.Div(
                className="cvd-strength-body",
                children=[
                    html.Div(
                        className="cvd-strength-row",
                        children=[
                            html.Span(label),
                            _cvd_strength_dots(count, color),
                        ],
                    )
                    for label, count, color in rows
                ],
            ),
        ],
    )

def build_analysis_screen(
    contract: dict[str, Any],
    timeframe: str | None,
    selection: Any,
) -> html.Div:
    selected_ids = _selected_analysis_ids(
        selection
    )

    if not selected_ids:
        empty = html.Div(
            "No seleccionaste indicadores de análisis "
            "en Pantalla A.",
            className="contract-warning",
        )
        return html.Div(
            [
                html.Div(
                className="analysis-back-row",
                children=[
                    html.Div(
                            children=[
                                dcc.Link(
                                    "← REGRESAR",
                                    href=ROUTE,
                                    className="analysis-back-button",
                                    style={"textDecoration": "none"},
                                ),
                                html.Button(
                                    "",
                                    id="cvd-back-analysis",
                                    n_clicks=0,
                                    style={"display": "none"},
                                ),
                            ],
                        )
                ],
            ),
                screen_header(
                    contract,
                    "ANÁLISIS TÉCNICO FUNDAMENTAL",
                ),
                empty,
            ]
        )

    market_sections: list[Any] = []

    for market, title in (
        ("spot", "CVD SPOT"),
        ("futures", "CVD FUTURES / PERPETUALS"),
    ):
        cards: list[Any] = []

        for indicator_id in selected_ids:
            cards.append(
                html.Div(
                    className="cvd-analysis-card",
                    children=[
                        html.Div(
                            INDICATOR_TITLES[
                                indicator_id
                            ],
                            className=(
                                "cvd-analysis-card-title"
                            ),
                        ),
                        dcc.Graph(
                            figure=_indicator_figure(
                                contract,
                                market,
                                timeframe,
                                indicator_id,
                            ),
                            config={
                                "displaylogo": False,
                                "responsive": True,
                            },
                            style={
                                "height": "152px",
                                "minHeight": "152px",
                                "width": "100%",
                            },
                        ),
                    ],
                )
            )

        market_sections.append(
            html.Div(
                className="cvd-analysis-market",
                children=[
                    html.Div(
                        title,
                        className=(
                            "cvd-analysis-market-title"
                        ),
                    ),
                    html.Div(
                        cards,
                        className="cvd-analysis-grid",
                    ),
                ],
            )
        )

    return html.Div(
        className="cvd-analysis-shell",
        children=[
            html.Div(
                className="analysis-back-row",
                children=[
                    html.Div(
                            children=[
                                dcc.Link(
                                    "← REGRESAR",
                                    href=ROUTE,
                                    className="analysis-back-button",
                                    style={"textDecoration": "none"},
                                ),
                                html.Button(
                                    "",
                                    id="cvd-back-analysis",
                                    n_clicks=0,
                                    style={"display": "none"},
                                ),
                            ],
                        )
                ],
            ),
            screen_header(
                contract,
                "ANÁLISIS TÉCNICO FUNDAMENTAL",
            ),
            html.Div(
                (
                    "La misma selección se aplica a "
                    "Spot y Futures. "
                    "Volumen y MFI no forman parte "
                    "de esta pantalla."
                ),
                className="contract-warning",
            ),
            html.Div(
                className="cvd-analysis-layout",
                children=[
                    html.Div(
                        market_sections,
                        className="cvd-analysis-main",
                    ),
                    html.Div(
                        className="cvd-summary-column",
                        children=[
                            _cvd_summary_panel(
                                _technical_block(contract, "spot", timeframe),
                                selected_ids,
                                "RESUMEN · CVD SPOT",
                            ),
                            _cvd_summary_panel(
                                _technical_block(contract, "futures", timeframe),
                                selected_ids,
                                "RESUMEN · CVD FUTURES",
                            ),
                            _cvd_strength_legend(),
                        ],
                    ),
                ],
            ),
        ],
    )


def _main_candle_grid(
    contract: dict[str, Any],
    timeframe: str | None,
    selected_overlays: list[str],
) -> html.Div:
    charts = _safe_dict(
        contract.get("charts")
    )

    market_specs = (
        (
            "spot",
            "cvd-spot-candle",
            "delta_buy_sell_spot",
            "cvd-spot-delta",
        ),
        (
            "futures",
            "cvd-futures-candle",
            "delta_buy_sell_futures",
            "cvd-futures-delta",
        ),
    )

    columns: list[Any] = []

    for (
        market,
        candle_component_id,
        delta_chart_id,
        delta_component_id,
    ) in market_specs:
        columns.append(
            html.Div(
                className="cvd-market-stack",
                children=[
                    html.Div(
                        className="cvd-chart-card",
                        children=[
                            dcc.Graph(
                                id=candle_component_id,
                                figure=(
                                    _cvd_candlestick_figure(
                                        contract,
                                        market,
                                        timeframe,
                                        selected_overlays,
                                    )
                                ),
                                config={
                                    "displaylogo": False,
                                    "responsive": True,
                                    "scrollZoom": True,
                                    "modeBarButtonsToRemove": [
                                        "lasso2d",
                                        "select2d",
                                    ],
                                },
                                style={
                                    "height": "350px",
                                    "minHeight": "350px",
                                    "width": "100%",
                                },
                            )
                        ],
                    ),
                    html.Div(
                        className="cvd-chart-card",
                        children=[
                            dcc.Graph(
                                id=delta_component_id,
                                figure=(
                                    _delta_buy_sell_figure(
                                        _safe_dict(
                                            charts.get(
                                                delta_chart_id
                                            )
                                        ),
                                        timeframe=timeframe,
                                    )
                                ),
                                config={
                                    "displaylogo": False,
                                    "responsive": True,
                                },
                                style={
                                    "height": "232px",
                                    "minHeight": "232px",
                                    "width": "100%",
                                },
                            )
                        ],
                    ),
                ],
            )
        )

    return html.Div(
        columns,
        className="cvd-market-stack-grid",
    )



@callback(
    Output("screen-view", "value", allow_duplicate=True),
    Input("cvd-back-analysis", "n_clicks", allow_optional=True),
    prevent_initial_call=True,
)
def return_to_cvd_screen_a(clicks: int | None):
    return "main" if clicks else no_update


@callback(
    Output("cvd-spot-candle", "figure"),
    Output("cvd-futures-candle", "figure"),
    Output("cvd-spot-delta", "figure"),
    Output("cvd-futures-delta", "figure"),
    Input("cvd-trend-selectors", "value"),
    Input("cvd-band-selectors", "value"),
    Input("timeframe-selector", "value"),
    Input("reload-json", "n_clicks"),
    prevent_initial_call=True,
)
def update_cvd_candles(
    trend: list[str] | None,
    bands: list[str] | None,
    timeframe: str | None,
    _reload_clicks: int | None,
):
    selected = _unique(
        [
            *(trend or []),
            *(bands or []),
        ]
    )
    contract = load_contract(CONTRACT_FILE)

    charts = _safe_dict(
        contract.get("charts")
    )

    return (
        _cvd_candlestick_figure(
            contract,
            "spot",
            timeframe,
            selected,
        ),
        _cvd_candlestick_figure(
            contract,
            "futures",
            timeframe,
            selected,
        ),
        _delta_buy_sell_figure(
            _safe_dict(
                charts.get(
                    "delta_buy_sell_spot"
                )
            ),
            timeframe=timeframe,
        ),
        _delta_buy_sell_figure(
            _safe_dict(
                charts.get(
                    "delta_buy_sell_futures"
                )
            ),
            timeframe=timeframe,
        ),
    )


@callback(
    Output(SELECTION_STORE_ID, "data"),
    Output(
        "screen-view",
        "value",
        allow_duplicate=True,
    ),
    Input("cvd-trend-selectors", "value"),
    Input("cvd-band-selectors", "value"),
    Input("cvd-derived-selectors", "value"),
    Input("cvd-momentum-selectors", "value"),
    Input("cvd-volatility-selectors", "value"),
    Input("cvd-open-analysis", "n_clicks"),
    prevent_initial_call=True,
)
def persist_cvd_selection_and_open_analysis(
    trend: list[str] | None,
    bands: list[str] | None,
    derived: list[str] | None,
    momentum: list[str] | None,
    volatility: list[str] | None,
    open_clicks: int | None,
):
    payload = _selection_payload(
        trend,
        bands,
        derived,
        momentum,
        volatility,
    )

    if (
        ctx.triggered_id == "cvd-open-analysis"
        and open_clicks
    ):
        return payload, "analysis"

    return payload, no_update


@callback(
    Output(
        ANALYSIS_CONTENT_ID,
        "children",
    ),
    Input(SELECTION_STORE_ID, "data"),
    Input("timeframe-selector", "value"),
    Input("reload-json", "n_clicks"),
    prevent_initial_call=False,
)
def update_cvd_analysis_screen(
    selection: Any,
    timeframe: str | None,
    _reload_clicks: int | None,
):
    contract = load_contract(CONTRACT_FILE)

    return build_analysis_screen(
        contract,
        timeframe,
        selection or _default_selection(),
    )


def render(
    contract: dict[str, Any],
    view: str,
    market: str | None,
    timeframe: str | None,
    range_id: str | None,
) -> html.Div:
    del market, range_id

    if view == "reference":
        return screen_page(
            _cvd_stylesheet(),
            screen_header(contract),
            reference_gallery(REFERENCE_IMAGES),
        )

    if view == "analysis":
        return screen_page(
            _cvd_stylesheet(),
            dcc.Store(
                id=SELECTION_STORE_ID,
                storage_type="local",
            ),
            html.Div(
                id=ANALYSIS_CONTENT_ID,
                children=build_analysis_screen(
                    contract,
                    timeframe,
                    _default_selection(),
                ),
            ),
        )

    initial = _default_selection()
    selected_overlays = _unique(
        [
            *initial["trend"],
            *initial["bands"],
        ]
    )

    return screen_page(
        _cvd_stylesheet(),
        dcc.Store(
            id=SELECTION_STORE_ID,
            storage_type="local",
        ),
        screen_header(contract),
        kpi_grid(contract.get("kpis")),
        html.Div(
            className="cvd-main-grid",
            children=[
                _main_candle_grid(
                    contract,
                    timeframe,
                    selected_overlays,
                ),
                _indicator_panel(),
            ],
        )
    )