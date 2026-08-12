from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import plotly.graph_objects as go
from dash import Input, Output, callback, ctx, dcc, html, no_update

from screen_core.components import (
    data_table_card,
    graph_card,
    kpi_grid,
    reference_gallery,
    screen_header,
    screen_page,
)
from screen_core.contract_loader import load_contract


ROUTE = "/etf-exchange-flows"
LABEL = "ETF Flows"
CONTRACT_FILE = "etf_exchange_flows_screen.json"
HAS_ANALYSIS = True

REFERENCE_IMAGES = [
    "ETF/04_ETF_Exchange_Flows_A.png",
    "ETF/04_ETF_Exchange_Flows_B_ExchangeBalance.png",
]

GREEN = "#17d49b"
RED = "#ff506e"
BG = "#06111d"
PLOT_BG = "#071522"
GRID = "rgba(91,126,155,.16)"
TEXT = "#d9e8f5"
MUTED = "#7f96aa"

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
    "signal": "#ff6a00",
    "histogram": "#17d49b",
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

ETF_RANGE_POINTS = {"30d": 30, "90d": 90, "360d": 360}

SELECTION_STORE_ID = "etf-technical-selection"
ANALYSIS_CONTENT_ID = "etf-analysis-content"

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

INDICATOR_LABELS = {
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

LOCAL_CSS = """
.etf-main-grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 286px;
    gap: 8px;
    align-items: stretch;
}
.etf-content-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    grid-template-rows: 291px 291px;
    gap: 8px;
    height: 590px;
}

.etf-content-grid > * {
    height: 291px;
    min-height: 291px;
    overflow: hidden;
    box-sizing: border-box;
}
.etf-card,
.etf-selector,
.etf-analysis-card {
    min-width: 0;
    min-height: 180px;
    border: 1px solid #123247;
    border-radius: 4px;
    background: linear-gradient(180deg, #061522 0%, #04111c 100%);
    overflow: hidden;
    box-sizing: border-box;
}
.etf-selector {
    height: 590px;
    padding: 8px 10px 12px;
    overflow-y: auto;
    box-sizing: border-box;
}
.etf-button {
    width: 100%;
    height: 28px;
    border: 1px solid #1766d6;
    border-radius: 4px;
    color: #3f8cff;
    background: #06111d;
    font-size: 9px;
    font-weight: 700;
    cursor: pointer;
}
.etf-heading {
    margin: 10px 0 7px;
    color: #dceaf5;
    font-size: 10px;
    font-weight: 700;
}
.etf-note {
    margin-bottom: 8px;
    color: #7f96aa;
    font-size: 8px;
    line-height: 1.35;
}
.etf-group {
    border-top: 1px solid #10283a;
    padding-top: 7px;
    margin-top: 7px;
}
.etf-group-title {
    margin-bottom: 5px;
    color: #7f91a0;
    font-size: 8px;
    text-transform: uppercase;
}
.etf-analysis-only {
    border: 1px dashed #235274;
    border-radius: 4px;
    padding: 7px;
    background: rgba(18,54,78,.18);
}
.etf-analysis-only .etf-group-title {
    color: #5aa9e6;
}
.etf-checklist label {
    display: inline-flex !important;
    width: 50%;
    gap: 5px;
    align-items: center;
    margin: 3px 0;
    color: #c6d5df;
    font-size: 8px;
}
.etf-checklist input {
    accent-color: #2f80ff;
}
.etf-analysis-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 5px;
    align-items: stretch;
}
.etf-analysis-card {
    min-height: 180px;
}

.etf-analysis-card-title {
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
    .etf-analysis-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}
@media (max-width: 900px) {
    .etf-main-grid,
    .etf-content-grid,
    .etf-analysis-grid {
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


.etf-analysis-layout {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 314px;
    gap: 8px;
    align-items: start;
}

.etf-analysis-main {
    min-width: 0;
}

.etf-summary-column {
    min-width: 0;
    display: grid;
    gap: 6px;
    align-content: start;
}

.etf-summary-panel,
.etf-strength-legend {
    border: 1px solid #123247;
    border-radius: 4px;
    background: linear-gradient(180deg, #061522 0%, #04111c 100%);
    overflow: hidden;
}

.etf-summary-title,
.etf-strength-title {
    min-height: 27px;
    display: flex;
    align-items: center;
    padding: 0 9px;
    border-bottom: 1px solid #102b3d;
    color: #dce6ec;
    font-size: 9px;
    font-weight: 700;
}

.etf-summary-head {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 54px 73px 48px;
    gap: 4px;
    padding: 6px 8px;
    border-bottom: 1px solid #102b3d;
    color: #8194a4;
    font-size: 6.5px;
    text-transform: uppercase;
}

.etf-summary-section {
    display: flex;
    align-items: center;
    gap: 5px;
    min-height: 23px;
    padding: 0 8px;
    border-bottom: 1px solid rgba(16,43,61,.8);
    font-size: 8px;
    font-weight: 700;
}

.etf-summary-section-marker {
    width: 0;
    height: 0;
    border-top: 4px solid transparent;
    border-bottom: 4px solid transparent;
    border-left: 5px solid currentColor;
}

.etf-summary-row {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 54px 73px 48px;
    gap: 4px;
    align-items: center;
    min-height: 24px;
    padding: 0 8px;
    border-bottom: 1px solid rgba(16,43,61,.62);
    font-size: 7.2px;
}

.etf-summary-name {
    color: #c7d2da;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.etf-summary-value {
    color: #dce6ec;
    text-align: right;
    font-variant-numeric: tabular-nums;
}

.etf-summary-signal {
    text-align: right;
    font-size: 6.8px;
    font-weight: 700;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.etf-summary-strength {
    display: inline-flex;
    justify-content: flex-end;
    gap: 2px;
}

.etf-summary-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #46525d;
}

.etf-strength-body {
    display: grid;
    gap: 4px;
    padding: 7px 9px 8px;
}

.etf-strength-row {
    display: grid;
    grid-template-columns: 58px 1fr;
    align-items: center;
    color: #c0cbd2;
    font-size: 7px;
}

@media (max-width: 1320px) {
    .etf-analysis-layout {
        grid-template-columns: minmax(0, 1fr) 290px;
    }
}

@media (max-width: 920px) {
    .etf-analysis-layout {
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
            + quote(LOCAL_CSS, safe="")
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


def _checklist(
    component_id: str,
    options: list[dict[str, str]],
    values: list[str],
) -> dcc.Checklist:
    return dcc.Checklist(
        id=component_id,
        options=options,
        value=values,
        className="etf-checklist",
        persistence="etf-controls-v1",
        persistence_type="memory",
    )


def _group(
    title: str,
    checklist: dcc.Checklist,
    *,
    analysis_only: bool = False,
) -> html.Div:
    children: list[Any] = [
        html.Div(
            title,
            className="etf-group-title",
        )
    ]

    if analysis_only:
        children.append(
            html.Div(
                (
                    "Gráfica independiente en Pantalla B; "
                    "no se superpone a Exchange Balance."
                ),
                className="etf-note",
            )
        )

    children.append(checklist)

    return html.Div(
        className=(
            "etf-group etf-analysis-only"
            if analysis_only
            else "etf-group"
        ),
        children=children,
    )


def _selector_panel() -> html.Div:
    return html.Div(
        className="etf-selector",
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
                        className="etf-button",
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
                        className="etf-button",
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
                        id="etf-open-analysis",
                        n_clicks=0,
                        type="button",
                        style={"display": "none"},
                    ),
                ],
            ),
            html.Div(
                "EXCHANGE BALANCE · INDICADORES",
                className="etf-heading",
            ),
            html.Div(
                (
                    "Único objetivo técnico de la familia ETF. "
                    "ETF Flow y Exchange Net Flow permanecen "
                    "como barras. Sin Volume ni MFI."
                ),
                className="etf-note",
            ),
            _group(
                "TENDENCIA · SOBRE EXCHANGE BALANCE",
                _checklist(
                    "etf-trend",
                    TREND_OPTIONS,
                    DEFAULT_TREND,
                ),
            ),
            _group(
                "BANDAS Y CANALES · SOBRE EXCHANGE BALANCE",
                _checklist(
                    "etf-bands",
                    BAND_OPTIONS,
                    DEFAULT_BANDS,
                ),
            ),
            _group(
                "ANÁLISIS DERIVADO · PANTALLA B",
                _checklist(
                    "etf-derived",
                    DERIVED_OPTIONS,
                    DEFAULT_DERIVED,
                ),
                analysis_only=True,
            ),
            _group(
                "MOMENTUM · PANTALLA B",
                _checklist(
                    "etf-momentum",
                    MOMENTUM_OPTIONS,
                    DEFAULT_MOMENTUM,
                ),
                analysis_only=True,
            ),
            _group(
                "VOLATILIDAD · PANTALLA B",
                _checklist(
                    "etf-volatility",
                    VOLATILITY_OPTIONS,
                    DEFAULT_VOLATILITY,
                ),
                analysis_only=True,
            ),
        ],
    )


def _range_indices(timestamps: list[int], range_id: str | None) -> list[int]:
    if not timestamps:
        return []
    points = ETF_RANGE_POINTS.get(str(range_id or "30d").lower(), 30)
    start = max(0, len(timestamps) - points)
    return list(range(start, len(timestamps)))

def _filtered_point_chart(chart: dict[str, Any], range_id: str | None) -> dict[str, Any]:
    result = dict(chart)
    points = [p for p in _safe_list(chart.get("points")) if isinstance(p, dict) and p.get("timestamp") is not None]
    if points:
        indices = _range_indices([int(p["timestamp"]) for p in points], range_id)
        result["points"] = [points[i] for i in indices]
    return result

def _exchange_balance_figure(
    contract: dict[str, Any],
    selected_overlays: list[str],
    range_id: str | None = None,
) -> go.Figure:
    chart = _safe_dict(
        _safe_dict(contract.get("charts")).get(
            "exchange_balance"
        )
    )
    candles = [
        candle
        for candle in _safe_list(chart.get("candles"))
        if isinstance(candle, dict)
        and all(
            candle.get(field) is not None
            for field in (
                "timestamp",
                "open",
                "high",
                "low",
                "close",
            )
        )
    ]

    all_candles = candles
    all_timestamps = [int(candle["timestamp"]) for candle in all_candles]
    range_indices = _range_indices(all_timestamps, range_id)
    candles = [all_candles[index] for index in range_indices]

    fig = go.Figure()

    if not candles:
        fig.add_annotation(
            text=(
                "OHLC UNAVAILABLE"
                "<br><span style='font-size:9px'>"
                "Processing debe empaquetar candles[] reales"
                "</span>"
            ),
            x=.5,
            y=.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font={
                "color": MUTED,
                "size": 12,
            },
        )
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
    else:
        selected = set(selected_overlays)
        x = [
            _dt(candle["timestamp"])
            for candle in candles
        ]

        fig.add_trace(
            go.Candlestick(
                x=x,
                open=[candle["open"] for candle in candles],
                high=[candle["high"] for candle in candles],
                low=[candle["low"] for candle in candles],
                close=[candle["close"] for candle in candles],
                increasing={
                    "line": {"color": GREEN},
                    "fillcolor": GREEN,
                },
                decreasing={
                    "line": {"color": RED},
                    "fillcolor": RED,
                },
                showlegend=False,
                name="EXCHANGE BALANCE",
            )
        )

        technical = _safe_dict(
            contract.get("technical_analysis")
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

            values_all = _safe_list(moving.get(indicator_id))
            if len(values_all) != len(all_candles):
                continue
            values = [values_all[index] for index in range_indices]

            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=values,
                    mode="lines",
                    line={
                        "color": TRACE_COLORS[indicator_id],
                        "width": 1.05,
                    },
                    showlegend=False,
                    connectgaps=False,
                    name=indicator_id.upper(),
                    hovertemplate=(
                        f"{indicator_id.upper()}: "
                        "%{y:,.4f}<extra></extra>"
                    ),
                )
            )

        if "bollinger_bands" in selected:
            bb = _safe_dict(
                overlays.get("bollinger_bands")
            )
            series = _safe_dict(bb.get("series"))

            for name, dash in (
                ("upper", "dot"),
                ("middle", "dash"),
                ("lower", "dot"),
            ):
                values_all = _safe_list(series.get(name))
                if len(values_all) != len(all_candles):
                    continue
                values = [values_all[index] for index in range_indices]

                fig.add_trace(
                    go.Scatter(
                        x=x,
                        y=values,
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
            regression = _safe_dict(
                overlays.get("regression_channel")
            )
            series = _safe_dict(regression.get("series"))

            for name, dash in (
                ("upper", "dot"),
                ("middle", "dash"),
                ("lower", "dot"),
            ):
                values_all = _safe_list(series.get(name))
                if len(values_all) != len(all_candles):
                    continue
                values = [values_all[index] for index in range_indices]

                fig.add_trace(
                    go.Scatter(
                        x=x,
                        y=values,
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

        # All contractual moving-average/channel crosses.
        candle_by_timestamp = {
            int(candle["timestamp"]): candle
            for candle in candles
        }

        grouped: dict[
            tuple[int, str],
            list[dict[str, Any]],
        ] = {}

        for event in _safe_list(
            technical.get("events")
        ):
            if not isinstance(event, dict):
                continue

            if event.get("event_group") not in {
                "moving_average_cross",
                "channel_cross",
            }:
                continue

            requirements = set(
                str(value)
                for value in _safe_list(
                    event.get("selection_requirements")
                )
            )

            if requirements and not requirements.issubset(selected):
                continue

            try:
                timestamp = int(event.get("timestamp"))
            except (TypeError, ValueError):
                continue

            if timestamp not in candle_by_timestamp:
                continue

            signal = str(event.get("signal") or "")
            if signal not in {"bullish", "bearish"}:
                continue

            grouped.setdefault(
                (timestamp, signal),
                [],
            ).append(event)

        for (timestamp, signal), cluster in grouped.items():
            candle = candle_by_timestamp[timestamp]
            high = float(candle["high"])
            low = float(candle["low"])
            candle_range = max(abs(high - low), 0.25)

            # Draw every event. Events on the same candle are vertically
            # staggered instead of hidden on top of one another.
            for rank, event in enumerate(cluster):
                offset = candle_range * (
                    0.55 + 0.28 * rank
                )

                if signal == "bullish":
                    y_value = low - offset
                    symbol = "arrow-up"
                    color = GREEN
                else:
                    y_value = high + offset
                    symbol = "arrow-down"
                    color = RED

                fig.add_trace(
                    go.Scatter(
                        x=[_dt(timestamp)],
                        y=[y_value],
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
                        cliponaxis=False,
                        hovertemplate=(
                            f"{event.get('label') or event.get('event_id')}"
                            "<extra></extra>"
                        ),
                    )
                )

    fig.update_layout(
        title={
            "text": "EXCHANGE BALANCE (BTC)",
            "x": .01,
            "font": {
                "size": 10,
                "color": TEXT,
            },
        },
        height=291,
        paper_bgcolor=BG,
        plot_bgcolor=PLOT_BG,
        margin={
            "l": 42,
            "r": 10,
            "t": 34,
            "b": 24,
        },
        font={
            "family": "Inter, Segoe UI, sans-serif",
            "color": TEXT,
            "size": 8,
        },
        showlegend=False,
        hovermode="x unified",
        xaxis_rangeslider_visible=False,
        uirevision="etf-exchange-balance",
    )
    fig.update_xaxes(
        gridcolor=GRID,
        zeroline=False,
    )
    fig.update_yaxes(
        gridcolor=GRID,
        zeroline=False,
    )

    return fig

def _indicator_figure(
    contract: dict[str, Any],
    indicator_id: str,
    range_id: str | None = None,
) -> go.Figure:
    technical = _safe_dict(
        contract.get("technical_analysis")
    )
    indicator = _safe_dict(
        _safe_dict(
            technical.get("indicators")
        ).get(indicator_id)
    )
    timestamps_all = [int(v) for v in _safe_list(indicator.get("timestamps"))]
    series_all = _safe_dict(indicator.get("series"))
    indices = _range_indices(timestamps_all, range_id)
    timestamps = [timestamps_all[index] for index in indices]
    series = {
        name: [values[index] for index in indices]
        for name, values in series_all.items()
        if isinstance(values, list) and len(values) == len(timestamps_all)
    }

    fig = go.Figure()

    if not timestamps or not series:
        fig.add_annotation(
            text="UNAVAILABLE",
            x=.5,
            y=.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font={
                "color": MUTED,
                "size": 11,
            },
        )
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
    else:
        x = [_dt(value) for value in timestamps]

        for name, values in series.items():
            if not isinstance(values, list):
                continue

            if indicator_id == "macd" and name == "histogram":
                fig.add_trace(
                    go.Bar(
                        x=x,
                        y=values,
                        marker_color=[
                            GREEN
                            if isinstance(value, (int, float)) and value >= 0
                            else RED
                            for value in values
                        ],
                        opacity=.78,
                        showlegend=False,
                        name=name,
                    )
                )
                continue

            # Every technical series receives an explicit color.  TSI now has
            # both oscillator and signal line in the JSON.
            line_color = TRACE_COLORS.get(
                name,
                TRACE_COLORS.get(indicator_id, "#22c7e8"),
            )

            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=values,
                    mode="lines",
                    line={
                        "width": 1.25,
                        "color": line_color,
                    },
                    showlegend=False,
                    connectgaps=False,
                    name=name,
                )
            )

        for threshold in _safe_list(
            indicator.get("thresholds")
        ):
            if not isinstance(threshold, dict):
                continue

            value = threshold.get("value")

            if isinstance(value, (int, float)):
                role = str(threshold.get("role") or "")
                line_color = (
                    "rgba(255,80,110,.62)" if role == "overbought"
                    else "rgba(23,212,155,.62)" if role == "oversold"
                    else "rgba(140,155,168,.52)"
                )
                fig.add_hline(
                    y=float(value),
                    line_dash="dot",
                    line_width=1,
                    line_color=line_color,
                    annotation_text=str(threshold.get("label") or value),
                    annotation_position="right",
                    annotation_font={"size": 6, "color": MUTED},
                )

    # Contractual Screen-B arrows: MACD, ADX/DI and Stochastic.
    allowed_events = {
        "macd": {
            "macd_above_signal",
            "macd_below_signal",
        },
        "adx": {
            "di_plus_above_di_minus",
            "di_plus_below_di_minus",
        },
        "stochastic": {
            "k_above_d",
            "k_below_d",
        },
    }.get(indicator_id, set())

    visible_timestamps = set(timestamps)

    if allowed_events:
        for event in _safe_list(
            technical.get("events")
        ):
            if not isinstance(event, dict):
                continue

            if event.get("event_group") not in {
                "indicator_cross", "macd_cross", "adx_cross", "stochastic_cross"
            }:
                continue

            if event.get("event_id") not in allowed_events:
                continue

            try:
                timestamp = int(event.get("timestamp"))
            except (TypeError, ValueError):
                continue

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
                    cliponaxis=False,
                    hovertemplate=(
                        f"{event.get('label') or event.get('event_id')}"
                        "<extra></extra>"
                    ),
                )
            )

    fig.update_layout(
        height=152,
        paper_bgcolor=BG,
        plot_bgcolor=PLOT_BG,
        margin={
            "l": 34,
            "r": 8,
            "t": 5,
            "b": 29,
        },
        font={
            "size": 7,
            "color": MUTED,
        },
        showlegend=False,
    )
    fig.update_xaxes(
        showticklabels=True,
        gridcolor=GRID,
        tickfont={"size": 6},
        nticks=4,
        automargin=True,
    )

    if indicator_id in {"rsi", "stochastic"}:
        fig.update_yaxes(
            gridcolor=GRID,
            zeroline=False,
            range=[0, 100],
            ticksuffix="%",
            tickfont={"size": 6},
        )
    elif indicator_id == "tsi":
        fig.update_yaxes(
            gridcolor=GRID,
            zeroline=False,
            range=[-100, 100],
            tickfont={"size": 6},
        )
    else:
        fig.update_yaxes(
            gridcolor=GRID,
            zeroline=False,
        )

    return fig


def _selected_analysis(
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


def _etf_strength_dots(count: Any, color: str) -> html.Span:
    try:
        strength = max(1, min(5, int(count)))
    except (TypeError, ValueError):
        strength = 1

    return html.Span(
        className="etf-summary-strength",
        children=[
            html.Span(
                className="etf-summary-dot",
                style={"background": color if index < strength else "#46525d"},
            )
            for index in range(5)
        ],
    )


def _etf_summary_panel(
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
            className="etf-summary-head",
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
                    className="etf-summary-row",
                    children=[
                        html.Span(
                            str(summary.get("label") or indicator_id.upper()),
                            className="etf-summary-name",
                        ),
                        html.Span(
                            str(summary.get("display_value") or "—"),
                            className="etf-summary-value",
                        ),
                        html.Span(
                            str(summary.get("signal") or "—"),
                            className="etf-summary-signal",
                            style={"color": signal_color},
                        ),
                        _etf_strength_dots(
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
                className="etf-summary-section",
                style={"color": section_color},
                children=[
                    html.Span(className="etf-summary-section-marker"),
                    html.Span(section_title),
                ],
            )
        )
        body.extend(section_rows)

    return html.Div(
        className="etf-summary-panel",
        children=[
            html.Div(title, className="etf-summary-title"),
            *body,
        ],
    )


def _etf_strength_legend() -> html.Div:
    rows = (
        ("MUY FUERTE", 5, "#20d05c"),
        ("FUERTE", 4, "#20d05c"),
        ("MODERADA", 3, "#ffab00"),
        ("DÉBIL", 2, "#ff8a00"),
        ("MUY DÉBIL", 1, "#ff3d55"),
    )

    return html.Div(
        className="etf-strength-legend",
        children=[
            html.Div("LEYENDA FUERZA", className="etf-strength-title"),
            html.Div(
                className="etf-strength-body",
                children=[
                    html.Div(
                        className="etf-strength-row",
                        children=[
                            html.Span(label),
                            _etf_strength_dots(count, color),
                        ],
                    )
                    for label, count, color in rows
                ],
            ),
        ],
    )

def _analysis_screen(
    contract: dict[str, Any],
    selection: Any,
    range_id: str | None = None,
) -> html.Div:
    selected = _selected_analysis(selection)

    if not selected:
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
                                    id="etf-back-analysis",
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
                        "No seleccionaste indicadores "
                        "de Pantalla B."
                    ),
                    className="contract-warning",
                ),
            ]
        )

    cards = []

    for indicator_id in selected:
        cards.append(
            html.Div(
                className="etf-analysis-card",
                children=[
                    html.Div(
                        INDICATOR_LABELS[
                            indicator_id
                        ],
                        className=(
                            "etf-analysis-card-title"
                        ),
                    ),
                    dcc.Graph(
                        figure=_indicator_figure(
                            contract,
                            indicator_id,
                            range_id,
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
                                    id="etf-back-analysis",
                                    n_clicks=0,
                                    style={"display": "none"},
                                ),
                            ],
                        )
                ],
            ),
            screen_header(
                contract,
                (
                    "ANÁLISIS TÉCNICO FUNDAMENTAL "
                    "· EXCHANGE BALANCE"
                ),
            ),
            html.Div(
                className="etf-analysis-layout",
                children=[
                    html.Div(
                        cards,
                        className="etf-analysis-grid etf-analysis-main",
                    ),
                    html.Div(
                        className="etf-summary-column",
                        children=[
                            _etf_summary_panel(
                                _safe_dict(contract.get("technical_analysis")),
                                selected,
                            ),
                            _etf_strength_legend(),
                        ],
                    ),
                ],
            ),
        ]
    )



@callback(
    Output("screen-view", "value", allow_duplicate=True),
    Input("etf-back-analysis", "n_clicks", allow_optional=True),
    prevent_initial_call=True,
)
def return_to_etf_screen_a(clicks: int | None):
    return "main" if clicks else no_update


@callback(
    Output(
        "etf-exchange-balance",
        "figure",
    ),
    Input("etf-trend", "value"),
    Input("etf-bands", "value"),
    Input("range-selector", "value"),
    Input("reload-json", "n_clicks"),
    prevent_initial_call=True,
)
def update_exchange_balance(
    trend: list[str] | None,
    bands: list[str] | None,
    range_id: str | None,
    _reload: int | None,
):
    contract = load_contract(CONTRACT_FILE)

    return _exchange_balance_figure(
        contract,
        _unique(
            [
                *(trend or []),
                *(bands or []),
            ]
        ),
        range_id,
    )


@callback(
    Output(
        SELECTION_STORE_ID,
        "data",
    ),
    Output(
        "screen-view",
        "value",
        allow_duplicate=True,
    ),
    Input("etf-trend", "value"),
    Input("etf-bands", "value"),
    Input("etf-derived", "value"),
    Input("etf-momentum", "value"),
    Input("etf-volatility", "value"),
    Input(
        "etf-open-analysis",
        "n_clicks",
    ),
    prevent_initial_call=True,
)
def persist_selection(
    trend: list[str] | None,
    bands: list[str] | None,
    derived: list[str] | None,
    momentum: list[str] | None,
    volatility: list[str] | None,
    open_clicks: int | None,
):
    payload = {
        "trend": _unique(trend or []),
        "bands": _unique(bands or []),
        "derived_analysis": _unique(
            derived or []
        ),
        "momentum": _unique(
            momentum or []
        ),
        "volatility": _unique(
            volatility or []
        ),
    }

    if (
        ctx.triggered_id
        == "etf-open-analysis"
        and open_clicks
    ):
        return payload, "analysis"

    return payload, no_update


@callback(
    Output(
        ANALYSIS_CONTENT_ID,
        "children",
    ),
    Input(
        SELECTION_STORE_ID,
        "data",
    ),
    Input(
        "reload-json",
        "n_clicks",
    ),
    Input("range-selector", "value"),
    prevent_initial_call=False,
)
def update_analysis(
    selection: Any,
    _reload: int | None,
    range_id: str | None,
):
    contract = load_contract(CONTRACT_FILE)

    return _analysis_screen(
        contract,
        selection or _default_selection(),
        range_id,
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
            reference_gallery(
                REFERENCE_IMAGES
            ),
        )

    if view == "analysis":
        return screen_page(
            _stylesheet(),
            dcc.Store(
                id=SELECTION_STORE_ID,
                storage_type="local",
            ),
            # Hidden target keeps callback valid.
            html.Div(
                dcc.Graph(
                    id="etf-exchange-balance"
                ),
                style={"display": "none"},
            ),
            html.Div(
                id=ANALYSIS_CONTENT_ID,
                children=_analysis_screen(
                    contract,
                    _default_selection(),
                    range_id,
                ),
            ),
        )

    charts = _safe_dict(
        contract.get("charts")
    )
    tables = _safe_dict(
        contract.get("tables")
    )

    initial = _default_selection()

    content = html.Div(
        className="etf-content-grid",
        children=[
            graph_card(
                _filtered_point_chart(
                    _safe_dict(charts.get("etf_flow_daily")),
                    range_id,
                ),
                chart_id="etf-flow-daily",
                range_id=range_id,
                height=291,
            ),
            data_table_card(
                tables.get("etf_funds"),
                "etf-funds",
                title=(
                    "ETF Flow by Provider"
                ),
                max_rows=10,
            ),
            graph_card(
                _filtered_point_chart(
                    _safe_dict(charts.get("exchange_net_flow")),
                    range_id,
                ),
                chart_id=(
                    "exchange-net-flow"
                ),
                range_id=range_id,
                height=291,
            ),
            html.Div(
                className="etf-card",
                children=[
                    dcc.Graph(
                        id=(
                            "etf-exchange-balance"
                        ),
                        figure=(
                            _exchange_balance_figure(
                                contract,
                                _unique(
                                    [
                                        *initial["trend"],
                                        *initial["bands"],
                                    ]
                                ),
                                range_id,
                            )
                        ),
                        config={
                            "displaylogo": False,
                            "responsive": True,
                            "scrollZoom": True,
                        },
                        style={
                            "height": "291px",
                            "minHeight": "291px",
                            "width": "100%",
                        },
                    )
                ],
            ),
        ],
    )

    return screen_page(
        _stylesheet(),
        dcc.Store(
            id=SELECTION_STORE_ID,
            storage_type="local",
        ),
        screen_header(contract),
        kpi_grid(
            contract.get("kpis")
        ),
        html.Div(
            className="etf-main-grid",
            children=[
                content,
                _selector_panel(),
            ],
        ),
        html.Div(
            id=ANALYSIS_CONTENT_ID,
            style={"display": "none"},
        ),
    )
