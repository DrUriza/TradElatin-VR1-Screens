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
from screen_core.contextual_help import contextual_help_label
from screen_core.i18n import current_locale, locale_context, localize_component_tree, localized_href, locale_from_search
from screen_core.contract_loader import load_contract
from screen_core.figures import apply_analysis_figure_layout


ROUTE = "/etf-exchange-flows"
LABEL = "ETF Flows"
CONTRACT_FILE = "etf_exchange_flows_VR1_FINAL.json"
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
    "flow_momentum_z": "#2f80ff",
    "rolling_flow_z": "#00c2ff",
    "persistence_score": "#17d49b",
    "zscore": "#a879ff",
    "btc_return_z": "#f2c94c",
    "etf_flow_z": "#2f80ff",
    "divergence_score": "#ff8a3d",
    "pressure": "#17d49b",
    "netflow_z": "#00c2ff",
    "reserve_change_z": "#ff506e",
    "reserve_roc_z": "#f2994a",
    "capital_regime_score": "#17d49b",
    "wasserstein_distance": "#8a7dff",
}

ETF_RANGE_POINTS = {"30d": 30, "90d": 90, "360d": 360}

SELECTION_STORE_ID = "etf-technical-selection"
ANALYSIS_CONTENT_ID = "etf-analysis-content"

# Pantalla A no aplica análisis técnico clásico a ETF Flow ni Exchange Reserve.
TREND_OPTIONS: list[dict[str, str]] = []
BAND_OPTIONS: list[dict[str, str]] = []

DERIVED_OPTIONS = [
    {
        "label": "ETF Flow Momentum / Persistence",
        "value": "etf_flow_momentum_persistence",
    },
    {
        "label": "ETF Flow Z-Score",
        "value": "etf_flow_zscore",
    },
]

MOMENTUM_OPTIONS = [
    {
        "label": "BTC Price ↔ ETF Flow Divergence",
        "value": "btc_etf_flow_divergence",
    },
    {
        "label": "Exchange Flow Pressure",
        "value": "exchange_flow_pressure",
    },
    {
        "label": "Exchange Reserve Change / Z-Score",
        "value": "exchange_reserve_change",
    },
]

VOLATILITY_OPTIONS = [
    {
        "label": "ETF × Exchange Capital Regime / Wasserstein",
        "value": "capital_regime_wasserstein",
    },
]

DEFAULT_TREND: list[str] = []
DEFAULT_BANDS: list[str] = []
DEFAULT_DERIVED = [
    "etf_flow_momentum_persistence",
    "etf_flow_zscore",
]
DEFAULT_MOMENTUM = [
    "btc_etf_flow_divergence",
    "exchange_flow_pressure",
    "exchange_reserve_change",
]
DEFAULT_VOLATILITY = ["capital_regime_wasserstein"]

ANALYSIS_ORDER = (
    "etf_flow_momentum_persistence",
    "etf_flow_zscore",
    "btc_etf_flow_divergence",
    "exchange_flow_pressure",
    "exchange_reserve_change",
    "capital_regime_wasserstein",
)

INDICATOR_LABELS = {
    "etf_flow_momentum_persistence": "ETF FLOW MOMENTUM / PERSISTENCE",
    "etf_flow_zscore": "ETF FLOW Z-SCORE",
    "btc_etf_flow_divergence": "BTC PRICE ↔ ETF FLOW DIVERGENCE",
    "exchange_flow_pressure": "EXCHANGE FLOW PRESSURE",
    "exchange_reserve_change": "EXCHANGE RESERVE CHANGE / Z-SCORE",
    "capital_regime_wasserstein": "ETF × EXCHANGE CAPITAL REGIME / WASSERSTEIN",
}

SCREEN_REVISION = "ETF_RENDER_CALLBACK_CLEANUP_V2"

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
    grid-template-rows: 252px 252px;
    gap: 6px;
    height: 510px;
}

.etf-content-grid > * {
    height: 252px;
    min-height: 252px;
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
    height: 510px;
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
@media (max-width: 1179px) {
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
                    "Independent chart on Screen B; it is not overlaid on Exchange Balance."
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
                        "FLOW & CAPITAL ANALYSIS",
                        href=localized_href(f"{ROUTE}/analysis"),
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
                        href=localized_href(f"{ROUTE}/analysis"),
                        target="_blank",
                        rel="noopener noreferrer",
                        title="Open analysis in a new tab",
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
                "ETF & EXCHANGE FLOWS · SCREEN B",
                className="etf-heading",
            ),
            html.Div(
                (
                    "Native capital-flow analytics. The HMI only plots metrics precomputed by Processing; "
                    "it does not apply RSI/MACD/ATR or moving averages to reserves or flows."
                ),
                className="etf-note",
            ),
            _group(
                "INSTITUTIONAL FLOW · SCREEN B",
                _checklist("etf-derived", DERIVED_OPTIONS, DEFAULT_DERIVED),
                analysis_only=True,
            ),
            _group(
                "PRICE & EXCHANGE CAPITAL · SCREEN B",
                _checklist("etf-momentum", MOMENTUM_OPTIONS, DEFAULT_MOMENTUM),
                analysis_only=True,
            ),
            _group(
                "CAPITAL REGIME · SCREEN B",
                _checklist("etf-volatility", VOLATILITY_OPTIONS, DEFAULT_VOLATILITY),
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
    points = [
        point
        for point in _safe_list(chart.get("points"))
        if isinstance(point, dict) and point.get("timestamp") is not None
    ]
    if points:
        indices = _range_indices([int(point["timestamp"]) for point in points], range_id)
        result["points"] = [points[index] for index in indices]

    raw_series = _safe_list(chart.get("series"))
    if raw_series:
        filtered_series = []
        for raw_item in raw_series:
            if not isinstance(raw_item, dict):
                continue
            item = dict(raw_item)
            item_points = [
                point
                for point in _safe_list(raw_item.get("points"))
                if isinstance(point, dict) and point.get("timestamp") is not None
            ]
            if item_points:
                indices = _range_indices(
                    [int(point["timestamp"]) for point in item_points],
                    range_id,
                )
                item["points"] = [item_points[index] for index in indices]
            filtered_series.append(item)
        result["series"] = filtered_series

    return result

def _exchange_balance_figure(
    contract: dict[str, Any],
    selected_overlays: list[str],
    range_id: str | None = None,
) -> go.Figure:
    del selected_overlays
    chart = _safe_dict(_safe_dict(contract.get("charts")).get("exchange_balance"))
    points = [
        point
        for point in _safe_list(chart.get("points"))
        if isinstance(point, dict)
        and point.get("timestamp") is not None
        and isinstance(point.get("value"), (int, float))
    ]

    # Backward-compatible fallback for older contracts that still carry OHLC candles.
    if not points:
        points = [
            {
                "timestamp": candle.get("timestamp"),
                "value": candle.get("close"),
            }
            for candle in _safe_list(chart.get("candles"))
            if isinstance(candle, dict)
            and candle.get("timestamp") is not None
            and isinstance(candle.get("close"), (int, float))
        ]

    timestamps_all = [int(point["timestamp"]) for point in points]
    indices = _range_indices(timestamps_all, range_id)
    points = [points[index] for index in indices]
    fig = go.Figure()

    if not points:
        fig.add_annotation(
            text="EXCHANGE RESERVE UNAVAILABLE",
            x=.5,
            y=.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font={"color": MUTED, "size": 11},
        )
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
    else:
        x = [_dt(point["timestamp"]) for point in points]
        y = [float(point["value"]) for point in points]
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines",
                name="EXCHANGE RESERVE",
                line={"color": "#2f80ff", "width": 1.65},
                fill="tozeroy",
                fillcolor="rgba(47,128,255,0.08)",
                hovertemplate="Reserve: %{y:,.0f} BTC<extra></extra>",
            )
        )

    fig.update_layout(
        title={
            "text": "EXCHANGE RESERVE / BALANCE (BTC)",
            "x": .01,
            "font": {"size": 10, "color": TEXT},
        },
        height=225,
        paper_bgcolor=BG,
        plot_bgcolor=PLOT_BG,
        margin={"l": 42, "r": 10, "t": 34, "b": 24},
        font={"family": "Inter, Segoe UI, sans-serif", "color": TEXT, "size": 8},
        showlegend=False,
        hovermode="x unified",
        uirevision="etf-exchange-reserve",
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, tickformat=",.0f")
    return fig

def _indicator_figure(
    contract: dict[str, Any],
    indicator_id: str,
    range_id: str | None = None,
) -> go.Figure:
    analysis = _safe_dict(contract.get("capital_flow_analysis"))
    indicator = _safe_dict(_safe_dict(analysis.get("indicators")).get(indicator_id))
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
            font={"color": MUTED, "size": 11},
        )
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
    else:
        x = [_dt(value) for value in timestamps]
        for name, values in series.items():
            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=values,
                    mode="lines",
                    line={
                        "width": 1.3,
                        "color": TRACE_COLORS.get(name, "#22c7e8"),
                    },
                    showlegend=True,
                    connectgaps=False,
                    name=name.replace("_", " ").upper(),
                    hovertemplate=(
                        name.replace("_", " ").upper()
                        + ": %{y:.3f}<extra></extra>"
                    ),
                )
            )

        for threshold in _safe_list(indicator.get("thresholds")):
            if not isinstance(threshold, dict):
                continue
            value = threshold.get("value")
            if isinstance(value, (int, float)):
                role = str(threshold.get("role") or "")
                line_color = (
                    "rgba(255,80,110,.62)" if role in {"high", "distribution", "extreme_positive"}
                    else "rgba(23,212,155,.62)" if role in {"low", "accumulation", "extreme_negative"}
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

    fig.update_layout(
        height=215,
        paper_bgcolor=BG,
        plot_bgcolor=PLOT_BG,
        margin={"l": 34, "r": 8, "t": 5, "b": 24},
        font={"size": 7, "color": MUTED},
        showlegend=True,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.01,
            "xanchor": "left",
            "x": 0,
            "font": {"size": 6},
        },
    )
    fig.update_xaxes(
        showticklabels=True,
        gridcolor=GRID,
        tickfont={"size": 6},
        nticks=4,
        automargin=True,
    )
    fig.update_yaxes(gridcolor=GRID, zeroline=True, zerolinecolor="rgba(140,155,168,.25)")
    return apply_analysis_figure_layout(fig)

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
    title: str = "FLOW & CAPITAL SUMMARY",
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
                html.Span("METRIC"),
                html.Span("VALUE", style={"textAlign": "right"}),
                html.Span("STATE", style={"textAlign": "right"}),
                html.Span("STRENGTH", style={"textAlign": "right"}),
            ],
        )
    ]

    sections = (
        ("institutional", "INSTITUTIONAL FLOW", "#2ea8ff"),
        ("confirmation", "PRICE CONFIRMATION", "#a65cff"),
        ("exchange", "EXCHANGE CAPITAL", "#ffab00"),
        ("regime", "CAPITAL REGIME", "#20d05c"),
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
                        _etf_strength_dots(summary.get("strength"), signal_color),
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
        ("VERY STRONG", 5, "#20d05c"),
        ("STRONG", 4, "#20d05c"),
        ("MODERATE", 3, "#ffab00"),
        ("WEAK", 2, "#ff8a00"),
        ("VERY WEAK", 1, "#ff3d55"),
    )

    return html.Div(
        className="etf-strength-legend",
        children=[
            html.Div("STRENGTH LEGEND", className="etf-strength-title"),
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
                                    "← BACK",
                                    href=localized_href(ROUTE),
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
                html.Div(
                    (
                        "No indicators selected "
                        "for Screen B."
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
                        contextual_help_label(
                            INDICATOR_LABELS[indicator_id],
                            family="etf",
                            section="screen_b",
                            key=indicator_id,
                        ),
                        className="etf-analysis-card-title",
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
                            "height": "215px",
                            "minHeight": "215px",
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
                                    "← BACK",
                                    href=localized_href(ROUTE),
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
                                _safe_dict(contract.get("capital_flow_analysis")),
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
        SELECTION_STORE_ID,
        "data",
    ),
    Output(
        "screen-view",
        "value",
        allow_duplicate=True,
    ),
    Input("etf-derived", "value", allow_optional=True),
    Input("etf-momentum", "value", allow_optional=True),
    Input("etf-volatility", "value", allow_optional=True),
    Input(
        "etf-open-analysis",
        "n_clicks",
        allow_optional=True,
    ),
    prevent_initial_call=True,
)
def persist_selection(
    derived: list[str] | None,
    momentum: list[str] | None,
    volatility: list[str] | None,
    open_clicks: int | None,
):
    payload = {
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
    Input("url", "search"),
    prevent_initial_call=False,
)
def update_analysis(
    selection: Any,
    _reload: int | None,
    range_id: str | None,
    search: str | None,
):
    locale = locale_from_search(search)
    contract = load_contract(CONTRACT_FILE)

    with locale_context(locale):
        return localize_component_tree(
            _analysis_screen(
                contract,
                selection or _default_selection(),
                range_id,
            ),
            locale,
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
                title="ETF Daily Net Flow",
                range_id=range_id,
                height=225,
                help_family="etf",
                help_section="screen_a",
                help_key="etf_flow_daily",
                show_card_title=True,
            ),
            data_table_card(
                tables.get("etf_funds"),
                "etf-funds",
                title=(
                    "ETF Flow by Provider"
                ),
                max_rows=10,
                help_family="etf",
                help_section="screen_a",
            ),
            graph_card(
                _filtered_point_chart(
                    _safe_dict(charts.get("exchange_net_flow")),
                    range_id,
                ),
                chart_id=(
                    "exchange-net-flow"
                ),
                title="Exchange Net Flow",
                range_id=range_id,
                height=225,
                help_family="etf",
                help_section="screen_a",
                help_key="exchange_net_flow",
                show_card_title=True,
            ),
            html.Div(
                className="etf-card",
                children=[
                    html.Div(
                        contextual_help_label(
                            "Exchange Balance / Reserve",
                            family="etf",
                            section="screen_a",
                            key="exchange_balance",
                        ),
                        className="panel-title",
                    ),
                    dcc.Graph(
                        id=(
                            "etf-exchange-balance"
                        ),
                        figure=(
                            _exchange_balance_figure(
                                contract,
                                [],
                                range_id,
                            )
                        ),
                        config={
                            "displaylogo": False,
                            "responsive": True,
                            "scrollZoom": True,
                        },
                        style={
                            "height": "225px",
                            "minHeight": "225px",
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
            contract.get("kpis"), help_family="etf"
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
