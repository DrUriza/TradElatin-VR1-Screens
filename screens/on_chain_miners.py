from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import plotly.graph_objects as go
from dash import Input, Output, callback, ctx, dcc, html, no_update

from screen_core.components import (
    graph_card,
    reference_gallery,
    screen_header,
    screen_page,
    two_column,
    widget_cards,
)
from screen_core.contract_loader import load_contract


ROUTE = "/on-chain-miners"
LABEL = "On-Chain Miners"
CONTRACT_FILE = "on_chain_miners_screen.json"
HAS_ANALYSIS = True

REFERENCE_IMAGES = [
    "On Chain/05_On_Chain_Miners_A.png",
    "On Chain/05_On_Chain_Miners_B_Reserve.png",
    "On Chain/05_On_Chain_Miners_B_SOPRD.png",
    "On Chain/05_On_Chain_Miners_B_HashRate.png",
    "On Chain/05_On_Chain_Miners_B_Difficulty.png",
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
    "signal": "#ff5d00",
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

SELECTION_STORE_ID = "onchain-technical-selection"
ANALYSIS_CONTENT_ID = "onchain-analysis-content"

TARGETS = (
    "miner_reserve",
    "sopr_7d",
    "hashrate",
    "difficulty",
)

TARGET_LABELS = {
    "miner_reserve": "MINER RESERVE",
    "sopr_7d": "SOPR (7D)",
    "hashrate": "HASHRATE",
    "difficulty": "DIFFICULTY",
}

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
    {"label": "Bollinger Bands (20, 2)", "value": "bollinger_bands"},
    {"label": "Canal de Regresión", "value": "regression_channel"},
]

DERIVED_OPTIONS = [
    {"label": "ADX / DI+ / DI- (14)", "value": "adx"},
    {
        "label": "Bollinger Band Width (20, 2)",
        "value": "bollinger_band_width",
    },
]

MOMENTUM_OPTIONS = [
    {"label": "MACD (12, 26, 9)", "value": "macd"},
    {"label": "RSI (14)", "value": "rsi"},
    {"label": "TSI (25, 13)", "value": "tsi"},
    {"label": "Stochastic (14, 3, 3)", "value": "stochastic"},
    {"label": "Williams %R (14)", "value": "williams_r"},
    {"label": "CCI (20)", "value": "cci"},
]

VOLATILITY_OPTIONS = [
    {"label": "ATR (14)", "value": "atr"},
    {"label": "Wasserstein Distance", "value": "wasserstein_distance"},
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

.onchain-top-widgets .widget-grid {
    grid-template-columns: repeat(4, minmax(120px, 1fr));
    gap: 3px;
}
.onchain-top-widgets .widget-card {
    min-height: 36px;
    padding: 2px 7px;
}
.onchain-top-widgets .widget-label {
    margin: 0;
    line-height: 1.05;
}
.onchain-top-widgets .widget-value {
    margin: 1px 0 0;
    line-height: 1.05;
}
.onchain-top-widgets .widget-state {
    display: block;
    margin-top: 0;
    line-height: 1;
}
@media (max-width: 900px) {
    .onchain-top-widgets .widget-grid {
        grid-template-columns: repeat(2, minmax(120px, 1fr));
    }
}

.onchain-main-grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 286px;
    gap: 8px;
    align-items: stretch;
}
.onchain-candle-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    grid-template-rows: 291px 291px;
    gap: 8px;
    height: 590px;
}
.onchain-card,
.onchain-selector,
.onchain-analysis-card {
    min-width: 0;
    min-height: 180px;
    border: 1px solid #123247;
    border-radius: 4px;
    background: linear-gradient(180deg, #061522 0%, #04111c 100%);
    overflow: hidden;
    box-sizing: border-box;
}
.onchain-selector {
    height: 590px;
    padding: 8px 10px 12px;
    overflow-y: auto;
    box-sizing: border-box;
}
.onchain-button {
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
.onchain-heading {
    margin: 10px 0 7px;
    color: #dceaf5;
    font-size: 10px;
    font-weight: 700;
}
.onchain-note {
    margin-bottom: 8px;
    color: #7f96aa;
    font-size: 8px;
    line-height: 1.35;
}
.onchain-group {
    border-top: 1px solid #10283a;
    padding-top: 7px;
    margin-top: 7px;
}
.onchain-group-title {
    margin-bottom: 5px;
    color: #7f91a0;
    font-size: 8px;
    text-transform: uppercase;
}
.onchain-analysis-only {
    border: 1px dashed #235274;
    border-radius: 4px;
    padding: 7px;
    background: rgba(18,54,78,.18);
}
.onchain-analysis-only .onchain-group-title {
    color: #5aa9e6;
}
.onchain-checklist label {
    display: inline-flex !important;
    width: 50%;
    gap: 5px;
    align-items: center;
    margin: 3px 0;
    color: #c6d5df;
    font-size: 8px;
}
.onchain-checklist input {
    accent-color: #2f80ff;
}
.onchain-analysis-shell {
    display: flex;
    flex-direction: column;
    gap: 10px;
}
.onchain-analysis-target {
    border: 1px solid #123148;
    background: #06111d;
    padding: 8px;
}
.onchain-analysis-title {
    color: #4fc3ff;
    font-size: 11px;
    font-weight: 700;
    margin-bottom: 8px;
}
.onchain-analysis-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 5px;
    align-items: stretch;
}
.onchain-analysis-card {
    min-height: 180px;
}
.onchain-analysis-card-title {
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
    .onchain-analysis-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}
@media (max-width: 900px) {
    .onchain-main-grid,
    .onchain-candle-grid,
    .onchain-analysis-grid {
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


.onchain-analysis-layout {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 314px;
    gap: 8px;
    align-items: start;
}

.onchain-analysis-main {
    min-width: 0;
}

.onchain-summary-column {
    min-width: 0;
    display: grid;
    gap: 6px;
    align-content: start;
}

.onchain-summary-panel,
.onchain-strength-legend {
    border: 1px solid #123247;
    border-radius: 4px;
    background: linear-gradient(180deg, #061522 0%, #04111c 100%);
    overflow: hidden;
}

.onchain-summary-title,
.onchain-strength-title {
    min-height: 27px;
    display: flex;
    align-items: center;
    padding: 0 9px;
    border-bottom: 1px solid #102b3d;
    color: #dce6ec;
    font-size: 9px;
    font-weight: 700;
}

.onchain-summary-head {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 54px 73px 48px;
    gap: 4px;
    padding: 6px 8px;
    border-bottom: 1px solid #102b3d;
    color: #8194a4;
    font-size: 6.5px;
    text-transform: uppercase;
}

.onchain-summary-section {
    display: flex;
    align-items: center;
    gap: 5px;
    min-height: 23px;
    padding: 0 8px;
    border-bottom: 1px solid rgba(16,43,61,.8);
    font-size: 8px;
    font-weight: 700;
}

.onchain-summary-section-marker {
    width: 0;
    height: 0;
    border-top: 4px solid transparent;
    border-bottom: 4px solid transparent;
    border-left: 5px solid currentColor;
}

.onchain-summary-row {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 54px 73px 48px;
    gap: 4px;
    align-items: center;
    min-height: 24px;
    padding: 0 8px;
    border-bottom: 1px solid rgba(16,43,61,.62);
    font-size: 7.2px;
}

.onchain-summary-name {
    color: #c7d2da;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.onchain-summary-value {
    color: #dce6ec;
    text-align: right;
    font-variant-numeric: tabular-nums;
}

.onchain-summary-signal {
    text-align: right;
    font-size: 6.8px;
    font-weight: 700;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.onchain-summary-strength {
    display: inline-flex;
    justify-content: flex-end;
    gap: 2px;
}

.onchain-summary-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #46525d;
}

.onchain-strength-body {
    display: grid;
    gap: 4px;
    padding: 7px 9px 8px;
}

.onchain-strength-row {
    display: grid;
    grid-template-columns: 58px 1fr;
    align-items: center;
    color: #c0cbd2;
    font-size: 7px;
}

@media (max-width: 1320px) {
    .onchain-analysis-layout {
        grid-template-columns: minmax(0, 1fr) 290px;
    }
}

@media (max-width: 920px) {
    .onchain-analysis-layout {
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
        href="data:text/css;charset=utf-8," + quote(LOCAL_CSS, safe=""),
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
        className="onchain-checklist",
        persistence="onchain-controls-v1",
        persistence_type="memory",
    )


def _group(
    title: str,
    checklist: dcc.Checklist,
    *,
    analysis_only: bool = False,
) -> html.Div:
    return html.Div(
        className=(
            "onchain-group onchain-analysis-only"
            if analysis_only
            else "onchain-group"
        ),
        children=[
            html.Div(title, className="onchain-group-title"),
            *(
                [
                    html.Div(
                        "Gráficas independientes en Pantalla B; "
                        "no se superponen a las velas.",
                        className="onchain-note",
                    )
                ]
                if analysis_only
                else []
            ),
            checklist,
        ],
    )


def _selector_panel() -> html.Div:
    return html.Div(
        className="onchain-selector",
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
                        className="onchain-button",
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
                        className="onchain-button",
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
                        id="onchain-open-analysis",
                        n_clicks=0,
                        type="button",
                        style={"display": "none"},
                    ),
                ],
            ),
            html.Div("INDICADORES", className="onchain-heading"),
            html.Div(
                "Paquete técnico común para Miner Reserve, SOPR, "
                "Hashrate y Difficulty. Sin Volume ni MFI.",
                className="onchain-note",
            ),
            _group(
                "TENDENCIA · SOBRE VELAS",
                _checklist(
                    "onchain-trend",
                    TREND_OPTIONS,
                    DEFAULT_TREND,
                ),
            ),
            _group(
                "BANDAS Y CANALES · SOBRE VELAS",
                _checklist(
                    "onchain-bands",
                    BAND_OPTIONS,
                    DEFAULT_BANDS,
                ),
            ),
            _group(
                "ANÁLISIS DERIVADO · PANTALLA B",
                _checklist(
                    "onchain-derived",
                    DERIVED_OPTIONS,
                    DEFAULT_DERIVED,
                ),
                analysis_only=True,
            ),
            _group(
                "MOMENTUM · PANTALLA B",
                _checklist(
                    "onchain-momentum",
                    MOMENTUM_OPTIONS,
                    DEFAULT_MOMENTUM,
                ),
                analysis_only=True,
            ),
            _group(
                "VOLATILIDAD · PANTALLA B",
                _checklist(
                    "onchain-volatility",
                    VOLATILITY_OPTIONS,
                    DEFAULT_VOLATILITY,
                ),
                analysis_only=True,
            ),
        ],
    )


def _range_block(
    contract: dict[str, Any],
    chart_id: str,
    range_id: str | None,
) -> dict[str, Any]:
    chart = _safe_dict(
        _safe_dict(contract.get("charts")).get(chart_id)
    )
    by_range = _safe_dict(chart.get("series_by_range"))
    selected = (
        str(range_id)
        if str(range_id) in by_range
        else str(
            _safe_dict(contract.get("context")).get(
                "presentation_default_range"
            )
            or "30D"
        )
    )
    if selected not in by_range:
        selected = next(iter(by_range), "")
    return _safe_dict(by_range.get(selected))


def _technical_block(
    contract: dict[str, Any],
    chart_id: str,
    range_id: str | None,
) -> dict[str, Any]:
    ta = _safe_dict(contract.get("technical_analysis"))
    target = _safe_dict(
        _safe_dict(ta.get("targets_by_chart")).get(chart_id)
    )
    ranges = _safe_dict(target.get("ranges"))
    selected = (
        str(range_id)
        if str(range_id) in ranges
        else str(
            _safe_dict(contract.get("context")).get(
                "presentation_default_range"
            )
            or "30D"
        )
    )
    if selected not in ranges:
        selected = next(iter(ranges), "")
    return _safe_dict(ranges.get(selected))



def _candlestick_figure(
    contract: dict[str, Any],
    chart_id: str,
    range_id: str | None,
    overlays_selected: list[str],
) -> go.Figure:
    chart = _safe_dict(
        _safe_dict(contract.get("charts")).get(chart_id)
    )
    block = _range_block(contract, chart_id, range_id)
    candles = [
        candle
        for candle in _safe_list(block.get("candles"))
        if isinstance(candle, dict)
        and all(
            candle.get(field) is not None
            for field in ("timestamp", "open", "high", "low", "close")
        )
    ]
    selected = set(overlays_selected)
    fig = go.Figure()

    if not candles:
        fig.add_annotation(
            text=(
                "OHLC UNAVAILABLE"
                "<br><span style='font-size:9px'>"
                "Processing debe empaquetar candles[] reales"
                "</span>"
            ),
            x=.5, y=.5, xref="paper", yref="paper",
            showarrow=False,
            font={"color": MUTED, "size": 12},
        )
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
    else:
        x = [_dt(candle["timestamp"]) for candle in candles]
        fig.add_trace(
            go.Candlestick(
                x=x,
                open=[candle["open"] for candle in candles],
                high=[candle["high"] for candle in candles],
                low=[candle["low"] for candle in candles],
                close=[candle["close"] for candle in candles],
                increasing={"line": {"color": GREEN}, "fillcolor": GREEN},
                decreasing={"line": {"color": RED}, "fillcolor": RED},
                showlegend=False,
                name=chart.get("title") or chart_id,
            )
        )

        technical = _technical_block(contract, chart_id, range_id)
        overlay_root = _safe_dict(technical.get("overlays"))
        moving = _safe_dict(
            _safe_dict(overlay_root.get("moving_averages")).get("series")
        )

        for indicator_id in (
            "ema_9", "ema_21", "ema_50",
            "sma_20", "sma_50", "sma_100", "sma_200",
            "wma_20", "wma_50",
        ):
            if indicator_id not in selected:
                continue
            values = _safe_list(moving.get(indicator_id))
            if len(values) != len(x):
                continue
            fig.add_trace(
                go.Scatter(
                    x=x, y=values, mode="lines",
                    line={
                        "color": TRACE_COLORS.get(indicator_id, "#22c7e8"),
                        "width": 1.05,
                    },
                    showlegend=False,
                    connectgaps=False,
                    name=indicator_id.upper(),
                )
            )

        if "bollinger_bands" in selected:
            series = _safe_dict(
                _safe_dict(overlay_root.get("bollinger_bands")).get("series")
            )
            for name, dash in (("upper","dot"),("middle","dash"),("lower","dot")):
                values = _safe_list(series.get(name))
                if len(values) != len(x):
                    continue
                fig.add_trace(
                    go.Scatter(
                        x=x, y=values, mode="lines",
                        line={
                            "color": TRACE_COLORS[f"bollinger_{name}"],
                            "width": 1, "dash": dash,
                        },
                        showlegend=False, connectgaps=False,
                    )
                )

        if "regression_channel" in selected:
            series = _safe_dict(
                _safe_dict(overlay_root.get("regression_channel")).get("series")
            )
            for name, dash in (("upper","dot"),("middle","dash"),("lower","dot")):
                values = _safe_list(series.get(name))
                if len(values) != len(x):
                    continue
                fig.add_trace(
                    go.Scatter(
                        x=x, y=values, mode="lines",
                        line={
                            "color": TRACE_COLORS[f"regression_{name}"],
                            "width": 1, "dash": dash,
                        },
                        showlegend=False, connectgaps=False,
                    )
                )

        # Contractual arrows. To avoid an unreadable forest of markers,
        # keep only the highest-importance event for each candle/direction.
        candle_by_ts = {int(c["timestamp"]): c for c in candles}
        grouped: dict[tuple[int, str], list[dict[str, Any]]] = {}

        for event in _safe_list(technical.get("events")):
            if not isinstance(event, dict):
                continue
            if event.get("event_group") not in {
                "moving_average_cross", "channel_cross"
            }:
                continue
            requirements = {
                str(v)
                for v in _safe_list(event.get("selection_requirements"))
            }
            if requirements and not requirements.issubset(selected):
                continue
            try:
                ts = int(event.get("timestamp"))
            except (TypeError, ValueError):
                continue
            signal = str(event.get("signal") or "")
            if ts not in candle_by_ts or signal not in {"bullish","bearish"}:
                continue
            grouped.setdefault((ts,signal),[]).append(event)

        for (ts, signal), cluster in grouped.items():
            event = max(
                cluster,
                key=lambda item: float(
                    _safe_dict(item.get("importance")).get("score") or 0.0
                ),
            )
            candle = candle_by_ts[ts]
            high = float(candle["high"])
            low = float(candle["low"])
            span = max(abs(high-low), abs(float(candle["close"])) * 0.001)

            if signal == "bullish":
                symbol, color, y = "arrow-up", GREEN, low - span * .55
            else:
                symbol, color, y = "arrow-down", RED, high + span * .55

            fig.add_trace(
                go.Scatter(
                    x=[_dt(ts)], y=[y], mode="markers",
                    marker={
                        "symbol": symbol, "size": 9, "color": color,
                        "line": {"width": 1, "color": "#03101a"},
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
            "text": chart.get("title") or chart_id,
            "x": .01,
            "font": {"size": 10, "color": TEXT},
        },
        height=291,
        paper_bgcolor=BG,
        plot_bgcolor=PLOT_BG,
        margin={"l": 42, "r": 10, "t": 34, "b": 34},
        font={
            "family": "Inter, Segoe UI, sans-serif",
            "color": TEXT, "size": 8,
        },
        showlegend=False,
        hovermode="x unified",
        xaxis_rangeslider_visible=False,
        uirevision=f"onchain-{chart_id}-{range_id}",
    )
    fig.update_xaxes(
        gridcolor=GRID,
        zeroline=False,
        showticklabels=True,
        ticks="outside",
        ticklen=3,
        tickfont={"size": 7},
        nticks=5,
        tickformat="%b %d<br>%Y",
        automargin=True,
    )
    fig.update_yaxes(
        gridcolor=GRID,
        zeroline=False,
    )
    return fig




def _indicator_figure(
    contract: dict[str, Any],
    chart_id: str,
    range_id: str | None,
    indicator_id: str,
) -> go.Figure:
    technical = _technical_block(contract, chart_id, range_id)
    indicator = _safe_dict(
        _safe_dict(technical.get("indicators")).get(indicator_id)
    )
    timestamps = [int(v) for v in _safe_list(indicator.get("timestamps"))]
    series = _safe_dict(indicator.get("series"))
    fig = go.Figure()

    if not timestamps or not series:
        fig.add_annotation(
            text="UNAVAILABLE", x=.5, y=.5, xref="paper", yref="paper",
            showarrow=False, font={"color": MUTED, "size": 11},
        )
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
    else:
        x = [_dt(v) for v in timestamps]
        for name, values in series.items():
            if not isinstance(values, list) or len(values) != len(x):
                continue
            if indicator_id == "macd" and name == "histogram":
                fig.add_trace(
                    go.Bar(
                        x=x, y=values,
                        marker_color=[
                            GREEN if isinstance(v,(int,float)) and v >= 0 else RED
                            for v in values
                        ],
                        opacity=.78, showlegend=False,
                    )
                )
            else:
                fig.add_trace(
                    go.Scatter(
                        x=x, y=values, mode="lines",
                        line={
                            "width": 1.25,
                            "color": TRACE_COLORS.get(
                                name, TRACE_COLORS.get(indicator_id, "#22c7e8")
                            ),
                        },
                        showlegend=False, connectgaps=False, name=name,
                    )
                )

        for threshold in _safe_list(indicator.get("thresholds")):
            if not isinstance(threshold, dict):
                continue
            value = threshold.get("value")
            if isinstance(value, (int, float)):
                role=str(threshold.get("role") or "")
                color=(
                    "rgba(255,80,110,.62)" if role=="overbought"
                    else "rgba(23,212,155,.62)" if role=="oversold"
                    else "rgba(140,155,168,.42)"
                )
                fig.add_hline(
                    y=float(value), line_dash="dot",
                    line_width=1, line_color=color,
                    annotation_text=str(threshold.get("label") or value),
                    annotation_position="right",
                    annotation_font={"size": 6, "color": MUTED},
                )

        allowed = {
            "macd": {"macd_above_signal","macd_below_signal"},
            "adx": {"di_plus_above_di_minus","di_plus_below_di_minus"},
            "stochastic": {"k_above_d","k_below_d"},
        }.get(indicator_id,set())

        visible_ts=set(timestamps)
        if allowed:
            for event in _safe_list(technical.get("events")):
                if not isinstance(event,dict) or event.get("event_id") not in allowed:
                    continue
                try:
                    ts=int(event.get("timestamp"))
                except (TypeError,ValueError):
                    continue
                if ts not in visible_ts:
                    continue
                calc=_safe_dict(event.get("calculation"))
                a=calc.get("first_value")
                b=calc.get("second_value")
                if not isinstance(a,(int,float)) or not isinstance(b,(int,float)):
                    continue
                y=(float(a)+float(b))/2.0
                signal=str(event.get("signal") or "")
                if signal=="bullish":
                    symbol,color="arrow-up",GREEN
                elif signal=="bearish":
                    symbol,color="arrow-down",RED
                else:
                    continue
                fig.add_trace(
                    go.Scatter(
                        x=[_dt(ts)], y=[y], mode="markers",
                        marker={
                            "symbol":symbol,"size":9,"color":color,
                            "line":{"width":1,"color":"#03101a"},
                        },
                        showlegend=False, cliponaxis=False,
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
        margin={"l": 38, "r": 10, "t": 8, "b": 30},
        font={"size": 8, "color": MUTED},
        showlegend=False,
        hovermode="x unified",
        uirevision=f"onchain-analysis-{chart_id}-{range_id}-{indicator_id}",
    )
    fig.update_xaxes(
        showticklabels=True,
        gridcolor=GRID,
        tickfont={"size": 6},
        nticks=4,
        ticks="outside",
        ticklen=2,
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



def _selected_analysis(selection: Any) -> list[str]:
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


def _onchain_strength_dots(count: Any, color: str) -> html.Span:
    try:
        strength = max(1, min(5, int(count)))
    except (TypeError, ValueError):
        strength = 1

    return html.Span(
        className="onchain-summary-strength",
        children=[
            html.Span(
                className="onchain-summary-dot",
                style={"background": color if index < strength else "#46525d"},
            )
            for index in range(5)
        ],
    )


def _onchain_summary_panel(
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
            className="onchain-summary-head",
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
                    className="onchain-summary-row",
                    children=[
                        html.Span(
                            str(summary.get("label") or indicator_id.upper()),
                            className="onchain-summary-name",
                        ),
                        html.Span(
                            str(summary.get("display_value") or "—"),
                            className="onchain-summary-value",
                        ),
                        html.Span(
                            str(summary.get("signal") or "—"),
                            className="onchain-summary-signal",
                            style={"color": signal_color},
                        ),
                        _onchain_strength_dots(
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
                className="onchain-summary-section",
                style={"color": section_color},
                children=[
                    html.Span(className="onchain-summary-section-marker"),
                    html.Span(section_title),
                ],
            )
        )
        body.extend(section_rows)

    return html.Div(
        className="onchain-summary-panel",
        children=[
            html.Div(title, className="onchain-summary-title"),
            *body,
        ],
    )


def _onchain_strength_legend() -> html.Div:
    rows = (
        ("MUY FUERTE", 5, "#20d05c"),
        ("FUERTE", 4, "#20d05c"),
        ("MODERADA", 3, "#ffab00"),
        ("DÉBIL", 2, "#ff8a00"),
        ("MUY DÉBIL", 1, "#ff3d55"),
    )

    return html.Div(
        className="onchain-strength-legend",
        children=[
            html.Div("LEYENDA FUERZA", className="onchain-strength-title"),
            html.Div(
                className="onchain-strength-body",
                children=[
                    html.Div(
                        className="onchain-strength-row",
                        children=[
                            html.Span(label),
                            _onchain_strength_dots(count, color),
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
    indicators = _selected_analysis(selection)

    sections: list[Any] = []
    for chart_id in TARGETS:
        cards: list[Any] = []
        for indicator_id in indicators:
            cards.append(
                html.Div(
                    className="onchain-analysis-card",
                    children=[
                        html.Div(
                            INDICATOR_LABELS[indicator_id],
                            className="onchain-analysis-card-title",
                        ),
                        dcc.Graph(
                            figure=_indicator_figure(
                                contract,
                                chart_id,
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
            )

        sections.append(
            html.Div(
                className="onchain-analysis-target",
                children=[
                    html.Div(
                        TARGET_LABELS[chart_id],
                        className="onchain-analysis-title",
                    ),
                    (
                        html.Div(
                            cards,
                            className="onchain-analysis-grid",
                        )
                        if cards
                        else html.Div(
                            "No seleccionaste indicadores de Pantalla B.",
                            className="contract-warning",
                        )
                    ),
                ],
            )
        )

    return html.Div(
        className="onchain-analysis-shell",
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
                                    id="onchain-back-analysis",
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
                className="onchain-analysis-layout",
                children=[
                    html.Div(
                        sections,
                        className="onchain-analysis-main",
                    ),
                    html.Div(
                        className="onchain-summary-column",
                        children=[
                            *[
                                _onchain_summary_panel(
                                    _technical_block(
                                        contract,
                                        chart_id,
                                        range_id,
                                    ),
                                    indicators,
                                    f"RESUMEN · {TARGET_LABELS[chart_id]}",
                                )
                                for chart_id in TARGETS
                            ],
                            _onchain_strength_legend(),
                        ],
                    ),
                ],
            ),
        ],
    )



@callback(
    Output("screen-view", "value", allow_duplicate=True),
    Input("onchain-back-analysis", "n_clicks", allow_optional=True),
    prevent_initial_call=True,
)
def return_to_onchain_screen_a(clicks: int | None):
    return "main" if clicks else no_update


@callback(
    Output("onchain-reserve", "figure"),
    Output("onchain-sopr", "figure"),
    Output("onchain-hashrate", "figure"),
    Output("onchain-difficulty", "figure"),
    Input("onchain-trend", "value", allow_optional=True),
    Input("onchain-bands", "value", allow_optional=True),
    Input("range-selector", "value"),
    Input("reload-json", "n_clicks"),
    prevent_initial_call=True,
)
def update_main_charts(
    trend: list[str] | None,
    bands: list[str] | None,
    range_id: str | None,
    _reload: int | None,
):
    contract = load_contract(CONTRACT_FILE)
    selected = _unique([*(trend or []), *(bands or [])])

    return tuple(
        _candlestick_figure(
            contract,
            chart_id,
            range_id,
            selected,
        )
        for chart_id in TARGETS
    )


@callback(
    Output(SELECTION_STORE_ID, "data"),
    Output(
        "screen-view",
        "value",
        allow_duplicate=True,
    ),
    Input("onchain-trend", "value", allow_optional=True),
    Input("onchain-bands", "value", allow_optional=True),
    Input("onchain-derived", "value", allow_optional=True),
    Input("onchain-momentum", "value", allow_optional=True),
    Input("onchain-volatility", "value", allow_optional=True),
    Input("onchain-open-analysis", "n_clicks", allow_optional=True),
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
        "derived_analysis": _unique(derived or []),
        "momentum": _unique(momentum or []),
        "volatility": _unique(volatility or []),
    }

    if (
        ctx.triggered_id == "onchain-open-analysis"
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
    _reload: int | None,
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
            # Hidden callback targets keep the dynamic view valid.
            html.Div(
                [
                    dcc.Graph(id="onchain-reserve"),
                    dcc.Graph(id="onchain-sopr"),
                    dcc.Graph(id="onchain-hashrate"),
                    dcc.Graph(id="onchain-difficulty"),
                ],
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
    overlays = _unique([
        *initial["trend"],
        *initial["bands"],
    ])

    charts = _safe_dict(contract.get("charts"))

    main_grid = html.Div(
        className="onchain-main-grid",
        children=[
            html.Div(
                className="onchain-candle-grid",
                children=[
                    html.Div(
                        className="onchain-card",
                        children=[
                            dcc.Graph(
                                id="onchain-reserve",
                                figure=_candlestick_figure(
                                    contract,
                                    "miner_reserve",
                                    range_id,
                                    overlays,
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
                    html.Div(
                        className="onchain-card",
                        children=[
                            dcc.Graph(
                                id="onchain-sopr",
                                figure=_candlestick_figure(
                                    contract,
                                    "sopr_7d",
                                    range_id,
                                    overlays,
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
                    html.Div(
                        className="onchain-card",
                        children=[
                            dcc.Graph(
                                id="onchain-hashrate",
                                figure=_candlestick_figure(
                                    contract,
                                    "hashrate",
                                    range_id,
                                    overlays,
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
                    html.Div(
                        className="onchain-card",
                        children=[
                            dcc.Graph(
                                id="onchain-difficulty",
                                figure=_candlestick_figure(
                                    contract,
                                    "difficulty",
                                    range_id,
                                    overlays,
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
            ),
            _selector_panel(),
        ],
    )

    top_widgets = html.Div(
        widget_cards(
            contract.get("widgets"),
            max_items=4,
        ),
        className="onchain-top-widgets",
    )

    bottom = graph_card(
        charts.get("miner_net_position_change"),
        chart_id="miner-net-position",
        range_id=range_id,
        height=300,
    )

    return screen_page(
        _stylesheet(),
        dcc.Store(
            id=SELECTION_STORE_ID,
            storage_type="local",
        ),
        screen_header(contract),
        top_widgets,
        main_grid,
        bottom,
        html.Div(
            id=ANALYSIS_CONTENT_ID,
            style={"display": "none"},
        ),
    )
