from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import plotly.graph_objects as go
from dash import Input, Output, callback, ctx, dcc, html, no_update

from screen_core.components import (
    graph_card,
    kpi_grid,
    reference_gallery,
    screen_header,
    screen_page,
    two_column,
)
from screen_core.contract_loader import load_contract


ROUTE = "/volatility-market-regimes"
LABEL = "Volatility"
CONTRACT_FILE = "volatility_market_regimes_screen.json"
HAS_ANALYSIS = True

REFERENCE_IMAGES = [
    "Volatility/06_Volatility_Regimes_A.png",
    "Volatility/06_Volatility_Regimes_B.png",
]

GREEN = "#17d49b"
RED = "#ff506e"
BG = "#06111d"
PLOT_BG = "#071522"
GRID = "rgba(91,126,155,.16)"
TEXT = "#d9e8f5"
MUTED = "#7f96aa"

SELECTION_STORE_ID = "volatility-technical-selection"
ANALYSIS_CONTENT_ID = "volatility-analysis-content"

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
    {"label": "MACD (12, 26, 9)", "value": "macd"},
    {"label": "RSI (14)", "value": "rsi"},
    {"label": "TSI (25, 13)", "value": "tsi"},
    {
        "label": "Stochastic (14, 3, 3)",
        "value": "stochastic",
    },
    {
        "label": "Williams %R (14)",
        "value": "williams_r",
    },
    {"label": "CCI (20)", "value": "cci"},
]

VOLATILITY_OPTIONS = [
    {"label": "ATR (14)", "value": "atr"},
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

RANGE_POINTS = {
    "7D": 7,
    "30D": 30,
    "90D": 90,
    "360D": 360,
}

VOLATILITY_LOCAL_CSS = """
.vol-main-grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 286px;
    gap: 8px;
    align-items: stretch;
}

.vol-left-stack {
    min-width: 0;
    display: grid;
    grid-template-rows: 350px 232px;
    gap: 8px;
    height: 590px;
}

.vol-chart-card,
.vol-indicator-panel,
.vol-analysis-card {
    min-width: 0;
    min-height: 180px;
    border: 1px solid #123247;
    border-radius: 4px;
    background: linear-gradient(180deg, #061522 0%, #04111c 100%);
    overflow: hidden;
    box-sizing: border-box;
}

.vol-indicator-panel {
    height: 590px;
    padding: 8px 10px 12px;
    color: #dbe7ef;
    overflow-y: auto;
    box-sizing: border-box;
}

.vol-analysis-button {
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

.vol-selector-heading {
    margin-top: 10px;
    margin-bottom: 8px;
    color: #dceaf5;
    font-size: 10px;
    font-weight: 700;
}

.vol-selector-note {
    margin-bottom: 9px;
    color: #7f96aa;
    font-size: 8px;
    line-height: 1.35;
}

.vol-indicator-group {
    border-top: 1px solid #10283a;
    padding-top: 8px;
    margin-top: 8px;
}

.vol-indicator-group-title {
    margin-bottom: 5px;
    color: #7f91a0;
    font-size: 8px;
    text-transform: uppercase;
}

.vol-analysis-only {
    border: 1px dashed #235274;
    border-radius: 4px;
    padding: 7px;
    background: rgba(18,54,78,.18);
}

.vol-analysis-only .vol-indicator-group-title {
    color: #5aa9e6;
}

.vol-checklist label {
    display: inline-flex !important;
    width: 50%;
    gap: 5px;
    align-items: center;
    margin: 3px 0;
    color: #c6d5df;
    font-size: 8px;
}

.vol-checklist input {
    accent-color: #2f80ff;
}

.vol-bottom-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 8px;
    margin-top: 8px;
}

.vol-analysis-shell {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.vol-analysis-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 5px;
    align-items: stretch;
}

.vol-analysis-card {
    min-height: 180px;
}
.vol-analysis-card-title {
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
    .vol-analysis-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 900px) {
    .vol-main-grid {
        grid-template-columns: 1fr;
    }

    .vol-bottom-grid,
    .vol-analysis-grid {
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


.vol-analysis-layout {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 314px;
    gap: 8px;
    align-items: start;
}

.vol-analysis-main {
    min-width: 0;
}

.vol-summary-column {
    min-width: 0;
    display: grid;
    gap: 6px;
    align-content: start;
}

.vol-summary-panel,
.vol-strength-legend {
    border: 1px solid #123247;
    border-radius: 4px;
    background: linear-gradient(180deg, #061522 0%, #04111c 100%);
    overflow: hidden;
}

.vol-summary-title,
.vol-strength-title {
    min-height: 27px;
    display: flex;
    align-items: center;
    padding: 0 9px;
    border-bottom: 1px solid #102b3d;
    color: #dce6ec;
    font-size: 9px;
    font-weight: 700;
}

.vol-summary-head {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 54px 73px 48px;
    gap: 4px;
    padding: 6px 8px;
    border-bottom: 1px solid #102b3d;
    color: #8194a4;
    font-size: 6.5px;
    text-transform: uppercase;
}

.vol-summary-section {
    display: flex;
    align-items: center;
    gap: 5px;
    min-height: 23px;
    padding: 0 8px;
    border-bottom: 1px solid rgba(16,43,61,.8);
    font-size: 8px;
    font-weight: 700;
}

.vol-summary-section-marker {
    width: 0;
    height: 0;
    border-top: 4px solid transparent;
    border-bottom: 4px solid transparent;
    border-left: 5px solid currentColor;
}

.vol-summary-row {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 54px 73px 48px;
    gap: 4px;
    align-items: center;
    min-height: 24px;
    padding: 0 8px;
    border-bottom: 1px solid rgba(16,43,61,.62);
    font-size: 7.2px;
}

.vol-summary-name {
    color: #c7d2da;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.vol-summary-value {
    color: #dce6ec;
    text-align: right;
    font-variant-numeric: tabular-nums;
}

.vol-summary-signal {
    text-align: right;
    font-size: 6.8px;
    font-weight: 700;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.vol-summary-strength {
    display: inline-flex;
    justify-content: flex-end;
    gap: 2px;
}

.vol-summary-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #46525d;
}

.vol-strength-body {
    display: grid;
    gap: 4px;
    padding: 7px 9px 8px;
}

.vol-strength-row {
    display: grid;
    grid-template-columns: 58px 1fr;
    align-items: center;
    color: #c0cbd2;
    font-size: 7px;
}

@media (max-width: 1320px) {
    .vol-analysis-layout {
        grid-template-columns: minmax(0, 1fr) 290px;
    }
}

@media (max-width: 920px) {
    .vol-analysis-layout {
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


def _stylesheet() -> html.Link:
    return html.Link(
        rel="stylesheet",
        href=(
            "data:text/css;charset=utf-8,"
            + quote(VOLATILITY_LOCAL_CSS, safe="")
        ),
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


def _checklist(
    component_id: str,
    options: list[dict[str, str]],
    value: list[str],
) -> dcc.Checklist:
    return dcc.Checklist(
        id=component_id,
        options=options,
        value=value,
        className="vol-checklist",
        persistence="volatility-controls-v1",
        persistence_type="memory",
    )


def _selector_group(
    title: str,
    checklist: dcc.Checklist,
    *,
    analysis_only: bool = False,
) -> html.Div:
    class_name = (
        "vol-indicator-group vol-analysis-only"
        if analysis_only
        else "vol-indicator-group"
    )

    children: list[Any] = [
        html.Div(
            title,
            className="vol-indicator-group-title",
        ),
    ]

    if analysis_only:
        children.append(
            html.Div(
                "Gráficas independientes en Pantalla B; "
                "no se superponen a las velas.",
                className="vol-selector-note",
            )
        )

    children.append(checklist)

    return html.Div(
        className=class_name,
        children=children,
    )


def _indicator_panel() -> html.Div:
    return html.Div(
        className="vol-indicator-panel",
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
                        className="vol-analysis-button",
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
                        className="vol-analysis-button",
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
                        id="volatility-open-analysis",
                        n_clicks=0,
                        type="button",
                        style={"display": "none"},
                    ),
                ],
            ),
            html.Div(
                "INDICADORES",
                className="vol-selector-heading",
            ),
            html.Div(
                "Paquete técnico general aplicado a "
                "Realized Volatility. Sin Volumen ni MFI.",
                className="vol-selector-note",
            ),
            _selector_group(
                "TENDENCIA · SOBRE VOLATILIDAD",
                _checklist(
                    "volatility-trend-selectors",
                    TREND_OPTIONS,
                    DEFAULT_TREND,
                ),
            ),
            _selector_group(
                "BANDAS Y CANALES · SOBRE VOLATILIDAD",
                _checklist(
                    "volatility-band-selectors",
                    BAND_OPTIONS,
                    DEFAULT_BANDS,
                ),
            ),
            _selector_group(
                "ANÁLISIS DERIVADO · PANTALLA B",
                _checklist(
                    "volatility-derived-selectors",
                    DERIVED_OPTIONS,
                    DEFAULT_DERIVED,
                ),
                analysis_only=True,
            ),
            _selector_group(
                "MOMENTUM · PANTALLA B",
                _checklist(
                    "volatility-momentum-selectors",
                    MOMENTUM_OPTIONS,
                    DEFAULT_MOMENTUM,
                ),
                analysis_only=True,
            ),
            _selector_group(
                "VOLATILIDAD · PANTALLA B",
                _checklist(
                    "volatility-volatility-selectors",
                    VOLATILITY_OPTIONS,
                    DEFAULT_VOLATILITY,
                ),
                analysis_only=True,
            ),
        ],
    )


def _filtered_indices(
    timestamps: list[int],
    range_id: str | None,
) -> list[int]:
    if not timestamps:
        return []

    points = RANGE_POINTS.get(str(range_id or ""))

    if points is None:
        return list(range(len(timestamps)))

    start = max(0, len(timestamps) - points)
    return list(range(start, len(timestamps)))


def _filtered_record_chart(chart: dict[str, Any], range_id: str | None) -> dict[str, Any]:
    result = dict(chart)
    records = [
        record for record in _safe_list(chart.get("records"))
        if isinstance(record, dict) and record.get("timestamp") is not None
    ]
    if records:
        indices = _filtered_indices(
            [int(record["timestamp"]) for record in records],
            range_id,
        )
        result["records"] = [records[index] for index in indices]
    return result


def _technical(contract: dict[str, Any]) -> dict[str, Any]:
    return _safe_dict(
        contract.get("technical_analysis")
    )


def _main_chart(contract: dict[str, Any]) -> dict[str, Any]:
    return _safe_dict(
        _safe_dict(contract.get("charts")).get(
            "volatility_comparison"
        )
    )


def _main_figure(
    contract: dict[str, Any],
    range_id: str | None,
    selected_overlays: list[str],
) -> go.Figure:
    chart = _main_chart(contract)
    technical = _technical(contract)

    candles = [
        candle
        for candle in _safe_list(chart.get("candles"))
        if isinstance(candle, dict)
    ]
    timestamps = [
        int(candle["timestamp"])
        for candle in candles
        if candle.get("timestamp") is not None
    ]
    indices = _filtered_indices(
        timestamps,
        range_id,
    )
    selected = set(selected_overlays)

    fig = go.Figure()

    if not indices:
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

    visible = [candles[index] for index in indices]
    x = [_dt(candle["timestamp"]) for candle in visible]

    fig.add_trace(
        go.Candlestick(
            x=x,
            open=[candle["open"] for candle in visible],
            high=[candle["high"] for candle in visible],
            low=[candle["low"] for candle in visible],
            close=[candle["close"] for candle in visible],
            increasing={
                "line": {"color": GREEN},
                "fillcolor": GREEN,
            },
            decreasing={
                "line": {"color": RED},
                "fillcolor": RED,
            },
            showlegend=False,
            name="REALIZED VOL",
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

        values = _safe_list(moving.get(indicator_id))

        if not values:
            continue

        fig.add_trace(
            go.Scatter(
                x=x,
                y=[values[index] for index in indices],
                mode="lines",
                line={
                    "color": TRACE_COLORS[indicator_id],
                    "width": 1.05,
                },
                showlegend=False,
                connectgaps=False,
                hovertemplate=(
                    f"{indicator_id.upper()}: "
                    "%{y:.3f}%<extra></extra>"
                ),
            )
        )

    if "bollinger_bands" in selected:
        series = _safe_dict(
            _safe_dict(
                overlays.get("bollinger_bands")
            ).get("series")
        )

        for name, dash in (
            ("upper", "dot"),
            ("middle", "dash"),
            ("lower", "dot"),
        ):
            values = _safe_list(series.get(name))

            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=[values[index] for index in indices],
                    mode="lines",
                    line={
                        "color": TRACE_COLORS[
                            f"bollinger_{name}"
                        ],
                        "width": 1,
                        "dash": dash,
                    },
                    showlegend=False,
                    connectgaps=False,
                )
            )

    if "regression_channel" in selected:
        series = _safe_dict(
            _safe_dict(
                overlays.get("regression_channel")
            ).get("series")
        )

        for name, dash in (
            ("upper", "dot"),
            ("middle", "dash"),
            ("lower", "dot"),
        ):
            values = _safe_list(series.get(name))

            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=[values[index] for index in indices],
                    mode="lines",
                    line={
                        "color": TRACE_COLORS[
                            f"regression_{name}"
                        ],
                        "width": 1,
                        "dash": dash,
                    },
                    showlegend=False,
                    connectgaps=False,
                )
            )

    # One contractual cross marker per candle/direction.
    events = [
        event
        for event in _safe_list(technical.get("events"))
        if isinstance(event, dict)
        and event.get("event_group")
        in {"moving_average_cross", "channel_cross"}
    ]

    visible_by_timestamp = {
        int(candle["timestamp"]): candle
        for candle in visible
    }
    grouped: dict[tuple[int, str], list[dict[str, Any]]] = {}

    for event in events:
        calculation = _safe_dict(event.get("calculation"))
        first = str(calculation.get("first_series") or "")
        second = str(calculation.get("second_series") or "")

        if not first or not second:
            event_id = str(event.get("event_id") or "")
            for separator in ("_above_", "_below_"):
                if separator in event_id:
                    first, second = event_id.split(separator, 1)
                    break

        requirements: set[str] = set()

        for series_id in (first, second):
            if not series_id:
                continue
            if series_id.startswith("regression_channel.") or series_id.startswith("regression_"):
                requirements.add("regression_channel")
            elif series_id.startswith("bollinger_bands.") or series_id.startswith("bollinger_"):
                requirements.add("bollinger_bands")
            else:
                requirements.add(series_id)

        if not requirements or not requirements.issubset(selected):
            continue

        timestamp = event.get("timestamp")
        signal = str(event.get("signal") or "")

        try:
            key = (int(timestamp), signal)
        except (TypeError, ValueError):
            continue

        if key[0] not in visible_by_timestamp:
            continue

        grouped.setdefault(key, []).append(event)

    for (timestamp, signal), cluster in grouped.items():
        candle = visible_by_timestamp[timestamp]
        high = float(candle["high"])
        low = float(candle["low"])
        candle_range = max(abs(high - low), .02)

        if signal == "bullish":
            symbol = "arrow-up"
            color = GREEN
            y = low - candle_range * .55
        elif signal == "bearish":
            symbol = "arrow-down"
            color = RED
            y = high + candle_range * .55
        else:
            continue

        event = cluster[0]

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

    fig.update_layout(
        title={
            "text": "REALIZED VOLATILITY (7D) · GLASSNODE",
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
            "l": 45,
            "r": 12,
            "t": 40,
            "b": 30,
        },
        font={
            "family": "Inter, Segoe UI, sans-serif",
            "color": TEXT,
            "size": 8,
        },
        hovermode="x unified",
        showlegend=False,
        xaxis_rangeslider_visible=False,
        uirevision=f"volatility-{range_id}",
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
        zeroline=False,
        ticksuffix="%",
        tickfont={
            "color": MUTED,
            "size": 7,
        },
    )

    return fig


def _indicator_figure(
    contract: dict[str, Any],
    range_id: str | None,
    indicator_id: str,
) -> go.Figure:
    technical = _technical(contract)
    block = _safe_dict(
        _safe_dict(
            technical.get("indicators")
        ).get(indicator_id)
    )
    timestamps = [
        int(value)
        for value in _safe_list(
            block.get("timestamps")
        )
    ]
    indices = _filtered_indices(timestamps, range_id)
    x = [
        _dt(timestamps[index])
        for index in indices
    ]
    series = _safe_dict(block.get("series"))
    fig = go.Figure()

    for name, values_raw in series.items():
        values = _safe_list(values_raw)
        visible_y = [
            values[index]
            for index in indices
        ]

        if indicator_id == "macd" and name == "histogram":
            fig.add_trace(
                go.Bar(
                    x=x,
                    y=visible_y,
                    marker_color=[
                        GREEN
                        if isinstance(value, (int, float))
                        and value >= 0
                        else RED
                        for value in visible_y
                    ],
                    showlegend=False,
                    opacity=.8,
                )
            )
            continue

        fig.add_trace(
            go.Scatter(
                x=x,
                y=visible_y,
                mode="lines",
                line={
                    "color": TRACE_COLORS.get(
                        name,
                        TRACE_COLORS.get(
                            indicator_id,
                            "#22c7e8",
                        ),
                    ),
                    "width": 1.15,
                },
                showlegend=False,
                connectgaps=False,
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

    allowed_events = {
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
    }.get(indicator_id, set())

    visible_timestamps = set(
        timestamps[index]
        for index in indices
    )

    if allowed_events:
        for event in _safe_list(
            technical.get("events")
        ):
            if not isinstance(event, dict):
                continue

            if event.get("event_id") not in allowed_events:
                continue

            timestamp = event.get("timestamp")

            if timestamp not in visible_timestamps:
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

            if event.get("signal") == "bullish":
                symbol = "arrow-up"
                color = GREEN
            elif event.get("signal") == "bearish":
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
                        "size": 8,
                        "color": color,
                        "line": {
                            "width": 1,
                            "color": "#03101a",
                        },
                    },
                    showlegend=False,
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
            f"volatility-analysis-{range_id}-{indicator_id}"
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


def _selected_analysis_ids(selection: Any) -> list[str]:
    payload = _safe_dict(selection)

    chosen = set(
        _safe_list(payload.get("derived_analysis"))
        + _safe_list(payload.get("momentum"))
        + _safe_list(payload.get("volatility"))
    )

    return [
        indicator_id
        for indicator_id in ANALYSIS_ORDER
        if indicator_id in chosen
    ]


def _vol_strength_dots(count: Any, color: str) -> html.Span:
    try:
        strength = max(1, min(5, int(count)))
    except (TypeError, ValueError):
        strength = 1

    return html.Span(
        className="vol-summary-strength",
        children=[
            html.Span(
                className="vol-summary-dot",
                style={"background": color if index < strength else "#46525d"},
            )
            for index in range(5)
        ],
    )


def _vol_summary_panel(
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
            className="vol-summary-head",
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
                    className="vol-summary-row",
                    children=[
                        html.Span(
                            str(summary.get("label") or indicator_id.upper()),
                            className="vol-summary-name",
                        ),
                        html.Span(
                            str(summary.get("display_value") or "—"),
                            className="vol-summary-value",
                        ),
                        html.Span(
                            str(summary.get("signal") or "—"),
                            className="vol-summary-signal",
                            style={"color": signal_color},
                        ),
                        _vol_strength_dots(
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
                className="vol-summary-section",
                style={"color": section_color},
                children=[
                    html.Span(className="vol-summary-section-marker"),
                    html.Span(section_title),
                ],
            )
        )
        body.extend(section_rows)

    return html.Div(
        className="vol-summary-panel",
        children=[
            html.Div(title, className="vol-summary-title"),
            *body,
        ],
    )


def _vol_strength_legend() -> html.Div:
    rows = (
        ("MUY FUERTE", 5, "#20d05c"),
        ("FUERTE", 4, "#20d05c"),
        ("MODERADA", 3, "#ffab00"),
        ("DÉBIL", 2, "#ff8a00"),
        ("MUY DÉBIL", 1, "#ff3d55"),
    )

    return html.Div(
        className="vol-strength-legend",
        children=[
            html.Div("LEYENDA FUERZA", className="vol-strength-title"),
            html.Div(
                className="vol-strength-body",
                children=[
                    html.Div(
                        className="vol-strength-row",
                        children=[
                            html.Span(label),
                            _vol_strength_dots(count, color),
                        ],
                    )
                    for label, count, color in rows
                ],
            ),
        ],
    )

def _analysis_screen(
    contract: dict[str, Any],
    range_id: str | None,
    selection: Any,
) -> html.Div:
    selected_ids = _selected_analysis_ids(selection)

    if not selected_ids:
        return html.Div(
            className="vol-analysis-shell",
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
                                    id="volatility-back-analysis",
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
                    "No seleccionaste indicadores de análisis "
                    "en Pantalla A.",
                    className="contract-warning",
                ),
            ],
        )

    cards = [
        html.Div(
            className="vol-analysis-card",
            children=[
                html.Div(
                    INDICATOR_TITLES[indicator_id],
                    className="vol-analysis-card-title",
                ),
                dcc.Graph(
                    figure=_indicator_figure(
                        contract,
                        range_id,
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
        for indicator_id in selected_ids
    ]

    return html.Div(
        className="vol-analysis-shell",
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
                                    id="volatility-back-analysis",
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
                    "Análisis técnico de Realized Volatility. "
                    "Volumen y MFI están excluidos."
                ),
                className="contract-warning",
            ),
            html.Div(
                className="vol-analysis-layout",
                children=[
                    html.Div(
                        cards,
                        className="vol-analysis-grid vol-analysis-main",
                    ),
                    html.Div(
                        className="vol-summary-column",
                        children=[
                            _vol_summary_panel(
                                _technical(contract),
                                selected_ids,
                            ),
                            _vol_strength_legend(),
                        ],
                    ),
                ],
            ),
        ],
    )



@callback(
    Output("screen-view", "value", allow_duplicate=True),
    Input("volatility-back-analysis", "n_clicks", allow_optional=True),
    prevent_initial_call=True,
)
def return_to_volatility_screen_a(clicks: int | None):
    return "main" if clicks else no_update


@callback(
    Output("volatility-main-graph", "figure"),
    Input("volatility-trend-selectors", "value", allow_optional=True),
    Input("volatility-band-selectors", "value", allow_optional=True),
    Input("range-selector", "value"),
    Input("reload-json", "n_clicks"),
    prevent_initial_call=True,
)
def update_volatility_main(
    trend: list[str] | None,
    bands: list[str] | None,
    range_id: str | None,
    _reload_clicks: int | None,
):
    contract = load_contract(CONTRACT_FILE)

    return _main_figure(
        contract,
        range_id,
        _unique(
            [
                *(trend or []),
                *(bands or []),
            ]
        ),
    )


@callback(
    Output(SELECTION_STORE_ID, "data"),
    Output(
        "screen-view",
        "value",
        allow_duplicate=True,
    ),
    Input("volatility-trend-selectors", "value", allow_optional=True),
    Input("volatility-band-selectors", "value", allow_optional=True),
    Input("volatility-derived-selectors", "value", allow_optional=True),
    Input("volatility-momentum-selectors", "value", allow_optional=True),
    Input("volatility-volatility-selectors", "value", allow_optional=True),
    Input("volatility-open-analysis", "n_clicks", allow_optional=True),
    prevent_initial_call=True,
)
def persist_selection_and_open_analysis(
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
        ctx.triggered_id == "volatility-open-analysis"
        and open_clicks
    ):
        return payload, "analysis"

    return payload, no_update


@callback(
    Output(ANALYSIS_CONTENT_ID, "children"),
    Input(SELECTION_STORE_ID, "data"),
    Input("range-selector", "value"),
    Input("reload-json", "n_clicks"),
    prevent_initial_call=False,
)
def update_analysis(
    selection: Any,
    range_id: str | None,
    _reload_clicks: int | None,
):
    contract = load_contract(CONTRACT_FILE)

    return _analysis_screen(
        contract,
        range_id,
        selection or _default_selection(),
    )


def render(
    contract: dict[str, Any],
    view: str,
    market: str | None,
    timeframe: str | None,
    range_id: str | None,
) -> html.Div:
    del market, timeframe

    if view == "reference":
        return screen_page(
            _stylesheet(),
            screen_header(contract),
            reference_gallery(REFERENCE_IMAGES),
        )

    if view == "analysis":
        return screen_page(
            _stylesheet(),
            dcc.Store(
                id=SELECTION_STORE_ID,
                storage_type="local",
            ),
            # Hidden main target keeps Dash callbacks valid across views.
            html.Div(
                dcc.Graph(
                    id="volatility-main-graph",
                    style={"display": "none"},
                ),
                style={"display": "none"},
            ),
            html.Div(
                id=ANALYSIS_CONTENT_ID,
                children=_analysis_screen(
                    contract,
                    range_id,
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

    charts = _safe_dict(contract.get("charts"))

    return screen_page(
        _stylesheet(),
        dcc.Store(
            id=SELECTION_STORE_ID,
            storage_type="local",
        ),
        screen_header(contract),
        kpi_grid(contract.get("kpis")),
        html.Div(
            className="vol-main-grid",
            children=[
                html.Div(
                    className="vol-left-stack",
                    children=[
                        html.Div(
                            className="vol-chart-card",
                            children=[
                                dcc.Graph(
                                    id="volatility-main-graph",
                                    figure=_main_figure(
                                        contract,
                                        range_id,
                                        selected_overlays,
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
                        graph_card(
                            _filtered_record_chart(
                                _safe_dict(charts.get("positioning_ratio")),
                                range_id,
                            ),
                            chart_id="positioning-ratio",
                            range_id=range_id,
                            height=232,
                        ),
                    ],
                ),
                _indicator_panel(),
            ],
        ),
        # Hidden target allows the analysis callback to exist in Pantalla A.
        html.Div(
            id=ANALYSIS_CONTENT_ID,
            style={"display": "none"},
        ),
    )