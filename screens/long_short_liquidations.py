from __future__ import annotations

from typing import Any
from urllib.parse import quote

import plotly.graph_objects as go
from dash import dcc, html

from screen_core.components import (
    reference_gallery,
    screen_header,
    screen_page,
)
from screen_core.figures import apply_analysis_figure_layout


ROUTE = "/long-short-liquidations"
LABEL = "Liquidations"
CONTRACT_FILE = "long_short_liquidations_VR1_FINAL.json"
HAS_ANALYSIS = True
SCREEN_REVISION = "LIQUIDATIONS_NATIVE_B_LONG_SHORT_V1"

REFERENCE_IMAGES = [
    "Liquidation/07_Long_Short_Liquidation_A.png",
]

BG = "#06111d"
PLOT_BG = "#071522"
TEXT = "#d9e8f5"
MUTED = "#7f96aa"
GRID = "rgba(91,126,155,.16)"

GREEN = "#17d49b"
RED = "#ff506e"
YELLOW = "#e9a900"
CYAN = "#26b8d7"
BLUE = "#328cc1"
PURPLE = "#8357d3"
ORANGE = "#ef8613"

LOCAL_CSS = """
.liq-top-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
    align-items: stretch;
}

.liq-bottom-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
    margin-top: 8px;
}

.liq-chart-card,
.liq-summary-panel {
    min-width: 0;
    border: 1px solid #173247;
    border-radius: 5px;
    background: #06111d;
}

.liq-chart-header {
    min-height: 34px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding: 7px 10px 4px;
    border-bottom: 1px solid rgba(23,50,71,.55);
}

.liq-chart-title {
    min-width: 0;
    color: #e4edf4;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .15px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.liq-summary-panel {
    padding: 8px 10px;
}

.liq-summary-title {
    padding-bottom: 7px;
    margin-bottom: 2px;
    border-bottom: 1px solid #173247;
    color: #e4edf4;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .3px;
}

.liq-summary-row {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 10px;
    padding: 7px 0;
    border-bottom: 1px solid rgba(23,50,71,.55);
    align-items: center;
}

.liq-summary-label {
    min-width: 0;
    color: #8295a6;
    font-size: 9px;
}

.liq-summary-value {
    color: #d9e8f5;
    font-size: 9px;
    font-weight: 700;
    text-align: right;
}

.liq-badge-row {
    display: flex;
    justify-content: flex-end;
    padding: 5px 8px 0;
}

.liq-proxy-badge {
    border: 1px solid rgba(233,169,0,.45);
    border-radius: 4px;
    padding: 2px 5px;
    color: #e9a900;
    background: rgba(233,169,0,.08);
    font-size: 8px;
    font-weight: 700;
}


.liq-position-card {
    min-width: 0;
    border: 1px solid #173247;
    border-radius: 5px;
    background: #06111d;
    overflow: hidden;
}

.liq-position-actions {
    display: flex;
    gap: 6px;
    align-items: center;
}

.liq-analysis-link {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border: 1px solid #1677ff;
    border-radius: 4px;
    padding: 4px 8px;
    color: #4da3ff;
    background: #071522;
    font-size: 8px;
    font-weight: 700;
    text-decoration: none;
}

.liq-analysis-shell {
    min-height: 100vh;
    background: #06111d;
}

.liq-analysis-back-row {
    padding: 8px 14px 0;
}

.liq-analysis-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
    padding: 8px 14px 18px;
}

.liq-analysis-card {
    min-width: 0;
    overflow: hidden;
    border: 1px solid #173247;
    border-radius: 5px;
    background: #071522;
}

.liq-analysis-card-title {
    min-height: 28px;
    display: flex;
    align-items: center;
    padding: 6px 8px;
    border-bottom: 1px solid #173247;
    color: #d9e8f5;
    font-size: 9px;
    font-weight: 700;
}

.liq-analysis-subtitle {
    color: #7f96aa;
    font-size: 8px;
    padding: 0 14px 6px;
}

@media (max-width: 1100px) {
    .liq-analysis-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 700px) {
    .liq-analysis-grid { grid-template-columns: 1fr; }
}

@media (max-width: 900px) {
    .liq-top-grid,
    .liq-bottom-grid {
        grid-template-columns: 1fr;
    }
}
"""


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _num(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _stylesheet() -> html.Link:
    return html.Link(
        rel="stylesheet",
        href=(
            "data:text/css;charset=utf-8,"
            + quote(LOCAL_CSS, safe="")
        ),
    )


def _reference_price(
    chart: dict[str, Any],
    contract: dict[str, Any],
) -> float | None:
    # Preferred common contract.
    direct = _num(chart.get("current_price"))
    if direct is not None:
        return direct

    reference = _safe_dict(chart.get("reference_price"))
    value = _num(reference.get("value"))
    if value is not None:
        return value

    # Current runtime also exposes it as a KPI.
    for kpi in _safe_list(contract.get("kpis")):
        if (
            isinstance(kpi, dict)
            and kpi.get("id") == "current_price"
        ):
            value = _num(kpi.get("value"))
            if value is not None:
                return value

    # Aggregate map remains the shared fallback for the lower maps.
    aggregate = _safe_dict(
        _safe_dict(contract.get("charts")).get("aggregate_map")
    )
    reference = _safe_dict(aggregate.get("reference_price"))
    return _num(reference.get("value"))


def _common_bucket_rows(
    chart: dict[str, Any],
) -> list[dict[str, Any]]:
    """Read the future common liquidation-map contract.

    Expected:
        buckets: [
            {
                "price_low": ...,
                "price_center": ...,
                "price_high": ...,
                "bars": {...},
                "cumulative_long": ...,
                "cumulative_short": ...
            }
        ]
    """

    buckets = chart.get("buckets")

    if isinstance(buckets, dict):
        items = _safe_list(buckets.get("items"))
    else:
        items = _safe_list(buckets)

    rows: list[dict[str, Any]] = []

    for item in items:
        if not isinstance(item, dict):
            continue

        center = _num(
            item.get("price_center")
            if item.get("price_center") is not None
            else item.get("center_price")
        )
        low = _num(
            item.get("price_low")
            if item.get("price_low") is not None
            else item.get("lower_price")
        )
        high = _num(
            item.get("price_high")
            if item.get("price_high") is not None
            else item.get("upper_price")
        )

        if center is None:
            continue

        row = dict(item)
        row["_center"] = center
        row["_low"] = low
        row["_high"] = high
        rows.append(row)

    return rows


def _curve_points(
    curve: Any,
) -> tuple[list[float], list[float]]:
    """Accept the final contract as well as common processing field names."""

    x: list[float] = []
    y: list[float] = []

    for point in _safe_list(curve):
        if not isinstance(point, dict):
            continue

        price = None
        for key in (
            "price_level",
            "price",
            "center_price",
            "price_center",
        ):
            price = _num(point.get(key))
            if price is not None:
                break

        value = None
        for key in (
            "value",
            "cumulative",
            "cumulative_level",
            "cumulative_liquidation",
            "liquidation_level",
            "level",
        ):
            value = _num(point.get(key))
            if value is not None:
                break

        if price is None or value is None:
            continue

        x.append(price)
        y.append(value)

    return x, y


def _bar_widths(
    rows: list[dict[str, Any]],
) -> list[float] | None:
    widths: list[float] = []

    for row in rows:
        low = row.get("_low")
        high = row.get("_high")

        if (
            isinstance(low, (int, float))
            and isinstance(high, (int, float))
            and high > low
        ):
            widths.append(float(high) - float(low))
        else:
            return None

    return widths or None


def _future_common_bar_series(
    chart: dict[str, Any],
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Parse the common bar_series[] + buckets[].bars{} contract."""

    descriptors = [
        item
        for item in _safe_list(chart.get("bar_series"))
        if isinstance(item, dict)
    ]

    if not descriptors:
        return []

    traces: list[dict[str, Any]] = []

    for descriptor in descriptors:
        series_id = str(
            descriptor.get("series_id")
            or descriptor.get("id")
            or ""
        )

        if not series_id:
            continue

        values = []
        for row in rows:
            bars = _safe_dict(row.get("bars"))
            values.append(_num(bars.get(series_id)) or 0.0)

        traces.append(
            {
                "id": series_id,
                "label": (
                    descriptor.get("label")
                    or series_id
                ),
                "values": values,
            }
        )

    return traces


def _aggregate_bar_series(
    chart: dict[str, Any],
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Adapt current aggregate_map.series_by_exchange to common traces."""

    common = _future_common_bar_series(chart, rows)
    if common:
        return common

    by_center = {
        round(float(row["_center"]), 8): index
        for index, row in enumerate(rows)
    }

    traces: list[dict[str, Any]] = []

    for exchange_block in _safe_list(
        chart.get("series_by_exchange")
    ):
        if not isinstance(exchange_block, dict):
            continue

        label = str(
            exchange_block.get("exchange")
            or "Exchange"
        )
        values = [0.0] * len(rows)

        for point in _safe_list(
            exchange_block.get("points")
        ):
            if not isinstance(point, dict):
                continue

            center = _num(
                point.get("center_price")
                if point.get("center_price") is not None
                else point.get("price_center")
            )
            value = _num(
                point.get("level_total")
                if point.get("level_total") is not None
                else point.get("value")
            )

            if center is None or value is None:
                continue

            index = by_center.get(round(center, 8))
            if index is not None:
                values[index] = value

        traces.append(
            {
                "id": label.lower(),
                "label": label,
                "values": values,
            }
        )

    return traces


def _binance_bar_series(
    chart: dict[str, Any],
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Adapt leverage breakdowns to 10x/25x/50x/100x traces."""

    common = _future_common_bar_series(chart, rows)
    if common:
        return common

    desired = ("10x", "25x", "50x", "100x")
    values_by_leverage = {
        leverage: [0.0] * len(rows)
        for leverage in desired
    }

    # First source: leverage_breakdown stored on buckets.
    for index, row in enumerate(rows):
        breakdown = _safe_dict(
            row.get("leverage_breakdown")
        )

        for leverage in desired:
            value = _num(breakdown.get(leverage))
            if value is not None:
                values_by_leverage[leverage][index] = value

    # Second source: stacked_buckets[].leverage_levels[].
    by_center = {
        round(float(row["_center"]), 8): index
        for index, row in enumerate(rows)
    }

    for stacked in _safe_list(
        chart.get("stacked_buckets")
    ):
        if not isinstance(stacked, dict):
            continue

        center = _num(
            stacked.get("price")
            if stacked.get("price") is not None
            else stacked.get("center_price")
        )

        if center is None:
            continue

        index = by_center.get(round(center, 8))
        if index is None:
            continue

        for level in _safe_list(
            stacked.get("leverage_levels")
        ):
            if not isinstance(level, dict):
                continue

            leverage = str(
                level.get("leverage")
                or level.get("label")
                or level.get("id")
                or ""
            )

            if leverage not in values_by_leverage:
                continue

            value = None
            for key in (
                "value",
                "level",
                "liquidation_level",
                "total_level",
            ):
                value = _num(level.get(key))
                if value is not None:
                    break

            if value is not None:
                values_by_leverage[leverage][index] = value

    return [
        {
            "id": leverage,
            "label": leverage,
            "values": values,
        }
        for leverage, values
        in values_by_leverage.items()
        if any(value != 0.0 for value in values)
    ]


def _hyperliquid_bar_series(
    chart: dict[str, Any],
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Support the final common contract and a simple long/short series form."""

    common = _future_common_bar_series(chart, rows)
    if common:
        return common

    series = [
        item
        for item in _safe_list(chart.get("series"))
        if isinstance(item, dict)
    ]

    if not series:
        return []

    by_center = {
        round(float(row["_center"]), 8): index
        for index, row in enumerate(rows)
    }

    traces = []

    for item in series:
        label = str(
            item.get("label")
            or item.get("side")
            or item.get("id")
            or "Series"
        )
        values = [0.0] * len(rows)

        for point in _safe_list(item.get("points")):
            if not isinstance(point, dict):
                continue

            center = None
            for key in (
                "price_level",
                "price",
                "center_price",
                "price_center",
            ):
                center = _num(point.get(key))
                if center is not None:
                    break

            value = None
            for key in (
                "value",
                "level",
                "liquidation_level",
            ):
                value = _num(point.get(key))
                if value is not None:
                    break

            if center is None or value is None:
                continue

            index = by_center.get(round(center, 8))
            if index is not None:
                values[index] = value

        traces.append(
            {
                "id": label.lower(),
                "label": label,
                "values": values,
            }
        )

    return traces


def _common_curves_from_buckets(
    rows: list[dict[str, Any]],
) -> tuple[
    list[float],
    list[float],
    list[float],
    list[float],
]:
    long_x: list[float] = []
    long_y: list[float] = []
    short_x: list[float] = []
    short_y: list[float] = []

    for row in rows:
        center = float(row["_center"])

        long_value = _num(
            row.get("cumulative_long")
        )
        short_value = _num(
            row.get("cumulative_short")
        )

        if long_value is not None:
            long_x.append(center)
            long_y.append(long_value)

        if short_value is not None:
            short_x.append(center)
            short_y.append(short_value)

    return long_x, long_y, short_x, short_y


def _curve_payload(
    chart: dict[str, Any],
    rows: list[dict[str, Any]],
) -> tuple[
    list[float],
    list[float],
    list[float],
    list[float],
]:
    from_buckets = _common_curves_from_buckets(rows)

    if (
        from_buckets[0]
        or from_buckets[2]
    ):
        return from_buckets

    long_x, long_y = _curve_points(
        chart.get("estimated_long_curve")
        or chart.get("cumulative_long_curve")
    )
    short_x, short_y = _curve_points(
        chart.get("estimated_short_curve")
        or chart.get("cumulative_short_curve")
    )

    return long_x, long_y, short_x, short_y


def _trace_color(
    map_kind: str,
    index: int,
    label: str,
) -> str:
    normalized = label.lower()

    if normalized == "long":
        return GREEN
    if normalized == "short":
        return RED

    if map_kind == "binance":
        palette = [
            "#315aa8",
            PURPLE,
            "#b95c32",
            ORANGE,
        ]
    else:
        palette = [
            YELLOW,
            CYAN,
            BLUE,
            PURPLE,
            ORANGE,
        ]

    return palette[index % len(palette)]


def _liquidation_map_figure(
    contract: dict[str, Any],
    chart: dict[str, Any] | None,
    *,
    map_kind: str,
    height: int,
) -> go.Figure:
    """One renderer for Aggregate, Hyperliquid and Binance leverage maps."""

    fig = go.Figure()

    if not isinstance(chart, dict):
        chart = {}

    rows = _common_bucket_rows(chart)
    current_price = _reference_price(
        chart,
        contract,
    )

    if map_kind == "aggregate":
        bar_series = _aggregate_bar_series(
            chart,
            rows,
        )
    elif map_kind == "binance":
        bar_series = _binance_bar_series(
            chart,
            rows,
        )
    else:
        bar_series = _hyperliquid_bar_series(
            chart,
            rows,
        )

    x = [
        float(row["_center"])
        for row in rows
    ]
    widths = _bar_widths(rows)

    for index, series in enumerate(bar_series):
        values = _safe_list(series.get("values"))

        if len(values) != len(x):
            continue

        fig.add_trace(
            go.Bar(
                x=x,
                y=values,
                width=widths,
                name=str(
                    series.get("label")
                    or series.get("id")
                    or f"Series {index + 1}"
                ),
                marker={
                    "color": _trace_color(
                        map_kind,
                        index,
                        str(series.get("label") or ""),
                    ),
                    "line": {"width": 0},
                },
                opacity=.86,
                yaxis="y",
                hovertemplate=(
                    "<b>%{x:,.2f}</b>"
                    "<br>%{fullData.name}: %{y:,.3f}"
                    "<extra></extra>"
                ),
            )
        )

    long_x, long_y, short_x, short_y = (
        _curve_payload(chart, rows)
    )

    if long_x and long_y:
        fig.add_trace(
            go.Scatter(
                x=long_x,
                y=long_y,
                mode="lines",
                name="Cum. Long Liq Lev",
                line={
                    "color": GREEN,
                    "width": 1.7,
                },
                fill="tozeroy",
                fillcolor="rgba(23,212,155,.12)",
                yaxis="y2",
                hovertemplate=(
                    "<b>%{x:,.2f}</b>"
                    "<br>Cum. Long: %{y:,.3f}"
                    "<extra></extra>"
                ),
            )
        )

    if short_x and short_y:
        fig.add_trace(
            go.Scatter(
                x=short_x,
                y=short_y,
                mode="lines",
                name="Cum. Short Liq Lev",
                line={
                    "color": RED,
                    "width": 1.7,
                },
                fill="tozeroy",
                fillcolor="rgba(255,80,110,.12)",
                yaxis="y2",
                hovertemplate=(
                    "<b>%{x:,.2f}</b>"
                    "<br>Cum. Short: %{y:,.3f}"
                    "<extra></extra>"
                ),
            )
        )

    if current_price is not None:
        fig.add_vline(
            x=current_price,
            line={
                "color": RED,
                "width": 1.5,
                "dash": "dot",
            },
        )

        fig.add_annotation(
            x=current_price,
            y=0,
            xref="x",
            yref="paper",
            text=f"{current_price:,.0f}",
            showarrow=False,
            yshift=-13,
            bgcolor=RED,
            bordercolor=RED,
            font={
                "color": "#ffffff",
                "size": 8,
            },
        )

        fig.add_annotation(
            x=current_price,
            y=1,
            xref="x",
            yref="paper",
            text="▲",
            showarrow=False,
            yshift=2,
            font={
                "color": RED,
                "size": 11,
            },
        )

    status = str(
        chart.get("status")
        or (
            "available"
            if rows
            else "unavailable"
        )
    )

    if not rows or not bar_series:
        reason = (
            chart.get("reason")
            or "map_series_not_packaged"
        )

        fig.add_annotation(
            x=.5,
            y=.5,
            xref="paper",
            yref="paper",
            text=(
                "UNAVAILABLE"
                f"<br><span style='font-size:9px'>"
                f"{reason}"
                "</span>"
            ),
            showarrow=False,
            font={
                "color": MUTED,
                "size": 11,
            },
        )

    title = (
        chart.get("title")
        or {
            "aggregate": (
                "BITCOIN EXCHANGE LIQUIDATION MAP"
            ),
            "hyperliquid": (
                "HYPERLIQUID LIQUIDATION MAP"
            ),
            "binance": (
                "BINANCE BTC/USDT LIQUIDATION MAP"
            ),
        }[map_kind]
    )

    unit = (
        chart.get("unit")
        or _safe_dict(chart.get("axes"))
        .get("bar_axis", {})
        .get("unit")
        or "level"
    )

    fig.update_layout(
        height=height,
        paper_bgcolor=BG,
        plot_bgcolor=PLOT_BG,
        margin={
            "l": 48,
            "r": 46,
            "t": 34,
            "b": 42,
        },
        font={
            "family": (
                "Inter, Segoe UI, "
                "Arial, sans-serif"
            ),
            "size": 8,
            "color": TEXT,
        },
        barmode="stack",
        bargap=.08,
        hovermode="x unified",
        showlegend=True,
        legend={
            "orientation": "h",
            "x": 0,
            "y": 1.025,
            "xanchor": "left",
            "yanchor": "bottom",
            "font": {
                "size": 8,
                "color": MUTED,
            },
            "bgcolor": "rgba(0,0,0,0)",
        },
        xaxis={
            "type": "linear",
            "title": None,
            "gridcolor": GRID,
            "zeroline": False,
            "tickfont": {
                "size": 8,
                "color": MUTED,
            },
            "tickformat": "~s",
            "fixedrange": True,
        },
        yaxis={
            "title": None,
            "gridcolor": GRID,
            "zeroline": True,
            "zerolinecolor": (
                "rgba(91,151,194,.45)"
            ),
            "tickfont": {
                "size": 8,
                "color": MUTED,
            },
            "fixedrange": True,
        },
        yaxis2={
            "title": None,
            "overlaying": "y",
            "side": "right",
            "showgrid": False,
            "zeroline": False,
            "tickfont": {
                "size": 8,
                "color": MUTED,
            },
            "fixedrange": True,
        },
        uirevision=(
            f"liquidation-map-{map_kind}"
        ),
    )

    return fig


def _summary_display(
    item: dict[str, Any],
) -> str:
    display = item.get("display_value")

    if display not in (None, "", "—"):
        return str(display)

    value = item.get("value")
    if isinstance(value, (int, float)):
        return f"{value:,.4g}"

    classification = item.get("classification")
    if classification:
        return str(classification).replace("_", " ").title()

    label = item.get("label")
    if (
        label
        and label != "—"
        and item.get("id") in {
            "selected_realized_side",
            "realized_side_24h",
            "estimated_side",
        }
    ):
        return str(label)

    if item.get("status") == "unavailable":
        return "—"

    return "—"


def _summary_label(
    item: dict[str, Any],
) -> str:
    explicit = item.get("label")

    if explicit and explicit != "—":
        return str(explicit)

    return str(
        item.get("id")
        or "Metric"
    ).replace("_", " ").title()


def _side_panel(
    contract: dict[str, Any],
) -> html.Div:
    panel = _safe_dict(
        contract.get("side_panel")
    )
    items = [
        item
        for item in _safe_list(
            panel.get("items")
        )
        if isinstance(item, dict)
    ]

    # Keep the compact summary focused on scalar/classification rows.
    excluded = {
        "provider_confirmations",
        "screen_quality_summary",
    }

    rows = []

    for item in items:
        if item.get("id") in excluded:
            continue

        rows.append(
            html.Div(
                className="liq-summary-row",
                children=[
                    html.Span(
                        _summary_label(item),
                        className=(
                            "liq-summary-label"
                        ),
                    ),
                    html.Strong(
                        _summary_display(item),
                        className=(
                            "liq-summary-value"
                        ),
                    ),
                ],
            )
        )

    return html.Div(
        className="liq-summary-panel",
        children=[
            html.Div(
                panel.get("title")
                or "LIQUIDITY TARGET SUMMARY",
                className="liq-summary-title",
            ),
            *rows,
        ],
    )


def _map_card(
    contract: dict[str, Any],
    chart: dict[str, Any] | None,
    *,
    map_kind: str,
    graph_id: str,
    height: int,
) -> html.Div:
    chart_dict = (
        chart
        if isinstance(chart, dict)
        else {}
    )

    proxy = bool(chart_dict.get("proxy"))

    chart_title = (
        chart_dict.get("title")
        or {
            "aggregate": (
                "BITCOIN EXCHANGE LIQUIDATION MAP"
            ),
            "hyperliquid": (
                "HYPERLIQUID LIQUIDATION MAP"
            ),
            "binance": (
                "BINANCE BTC/USDT LIQUIDATION MAP"
            ),
        }[map_kind]
    )

    header_children: list[Any] = [
        html.Div(
            str(chart_title).upper(),
            className="liq-chart-title",
            title=str(chart_title).upper(),
        )
    ]

    if proxy:
        header_children.append(
            html.Span(
                "PROXY",
                className="liq-proxy-badge",
            )
        )

    return html.Div(
        className="liq-chart-card",
        style={
            "minHeight": f"{height + 34}px",
        },
        children=[
            html.Div(
                className="liq-chart-header",
                children=header_children,
            ),
            dcc.Graph(
                id=graph_id,
                figure=_liquidation_map_figure(
                    contract,
                    chart_dict,
                    map_kind=map_kind,
                    height=height,
                ),
                config={
                    "displaylogo": False,
                    "responsive": True,
                    "scrollZoom": False,
                    "modeBarButtonsToRemove": [
                        "lasso2d",
                        "select2d",
                    ],
                },
                style={
                    "height": f"{height}px",
                    "minHeight": f"{height}px",
                    "width": "100%",
                },
            ),
        ],
    )


def _dt(value: Any):
    from datetime import datetime, timezone

    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    except (TypeError, ValueError, OSError, OverflowError):
        return None


def _long_short_positioning_figure(contract: dict[str, Any], height: int = 365) -> go.Figure:
    chart = _safe_dict(_safe_dict(contract.get("charts")).get("long_short_positioning"))
    points = [
        item for item in _safe_list(chart.get("points"))
        if isinstance(item, dict) and item.get("timestamp") is not None
    ]
    fig = go.Figure()

    if points:
        x = [_dt(item.get("timestamp")) for item in points]
        series_specs = (
            ("top_position_ratio", "TOP POSITION L/S", CYAN, 1.8),
            ("top_account_ratio", "TOP ACCOUNT L/S", PURPLE, 1.15),
            ("global_account_ratio", "GLOBAL ACCOUNT L/S", YELLOW, 1.15),
        )
        for field, name, color, width in series_specs:
            y = [item.get(field) for item in points]
            fig.add_trace(go.Scatter(
                x=x, y=y, mode="lines", name=name,
                line={"color": color, "width": width},
                connectgaps=False,
                hovertemplate=f"{name}: %{{y:.3f}}<extra></extra>",
            ))
        fig.add_hline(
            y=1.0, line_dash="dot", line_width=1.0,
            line_color="#8295a6", annotation_text="NEUTRAL 1.0",
            annotation_position="right",
            annotation_font={"size": 7, "color": MUTED},
        )
    else:
        fig.add_annotation(
            text="LONG / SHORT POSITIONING UNAVAILABLE",
            x=.5, y=.5, xref="paper", yref="paper", showarrow=False,
            font={"color": MUTED, "size": 10},
        )

    fig.update_layout(
        height=height, paper_bgcolor=BG, plot_bgcolor=PLOT_BG,
        margin={"l": 44, "r": 20, "t": 30, "b": 42},
        font={"family": "Inter, Segoe UI, Arial, sans-serif", "size": 8, "color": TEXT},
        hovermode="x unified",
        legend={
            "orientation": "h", "x": 0, "y": 1.02,
            "xanchor": "left", "yanchor": "bottom",
            "font": {"size": 7, "color": MUTED},
            "bgcolor": "rgba(0,0,0,0)",
        },
        uirevision="liq-long-short-positioning",
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, tickfont={"size": 8, "color": MUTED})
    fig.update_yaxes(gridcolor=GRID, zeroline=False, tickfont={"size": 8, "color": MUTED}, title_text="L/S Ratio")
    return fig


def _positioning_card(contract: dict[str, Any], height: int = 365) -> html.Div:
    return html.Div(
        className="liq-position-card",
        children=[
            html.Div(
                className="liq-chart-header",
                children=[
                    html.Div("LONG / SHORT POSITIONING", className="liq-chart-title"),
                    html.Div(
                        className="liq-position-actions",
                        children=[
                            dcc.Link("ANÁLISIS", href=f"{ROUTE}/analysis", className="liq-analysis-link"),
                            html.A("↗", href=f"{ROUTE}/analysis", target="_blank", rel="noopener noreferrer", className="liq-analysis-link"),
                        ],
                    ),
                ],
            ),
            dcc.Graph(
                id="long-short-positioning-chart",
                figure=_long_short_positioning_figure(contract, height=height),
                config={"displaylogo": False, "responsive": True, "scrollZoom": False},
                style={"height": f"{height}px", "minHeight": f"{height}px", "width": "100%"},
            ),
        ],
    )


ANALYSIS_LABELS = {
    "liquidation_intensity_zscore": "LIQUIDATION INTENSITY / Z-SCORE",
    "long_short_liquidation_imbalance": "LONG VS SHORT LIQUIDATION IMBALANCE",
    "cascade_acceleration": "LIQUIDATION CASCADE / ACCELERATION",
    "price_liquidation_regime": "PRICE × LIQUIDATION REGIME",
    "crowding_liquidation_pressure": "LONG/SHORT CROWDING × LIQUIDATION PRESSURE",
    "liquidation_regime_hmi": "LIQUIDATION REGIME / HMI",
}

ANALYSIS_ORDER = tuple(ANALYSIS_LABELS)


def _analysis_block(contract: dict[str, Any], indicator_id: str) -> dict[str, Any]:
    root = _safe_dict(contract.get("liquidation_analysis"))
    return _safe_dict(_safe_dict(root.get("indicators")).get(indicator_id))


def _analysis_figure(contract: dict[str, Any], indicator_id: str, height: int = 310) -> go.Figure:
    block = _analysis_block(contract, indicator_id)
    points = [
        item for item in _safe_list(block.get("points"))
        if isinstance(item, dict) and item.get("timestamp") is not None
    ]
    fig = go.Figure()
    color_cycle = [CYAN, GREEN, RED, YELLOW, PURPLE, ORANGE, BLUE]

    if not points:
        fig.add_annotation(
            text="UNAVAILABLE", x=.5, y=.5, xref="paper", yref="paper",
            showarrow=False, font={"color": MUTED, "size": 10},
        )
    else:
        x = [_dt(item.get("timestamp")) for item in points]
        series = _safe_list(block.get("series"))
        if not series:
            ignored = {"timestamp", "state", "regime", "classification"}
            fields = [k for k, v in points[-1].items() if k not in ignored and isinstance(v, (int, float))]
            series = [{"field": field, "label": field.replace("_", " ").upper()} for field in fields[:3]]

        for index, spec_raw in enumerate(series):
            spec = _safe_dict(spec_raw)
            field = str(spec.get("field") or "")
            if not field:
                continue
            labels = {"total_liquidations_usd": "Total Liq", "total_liq_usd": "Total Liq",
                      "total_liquidations_musd": "Total Liq", "liquidation_imbalance": "L/S Imbalance",
                      "liquidation_regime_score": "HMI Score", "hmi_regime_score": "HMI Score",
                      "wasserstein_distance": "Wasserstein", "capitulation_probability_pct": "Capitulation %"}
            label = labels.get(field, str(spec.get("label") or field.replace("_", " ").title()))
            color = str(spec.get("color") or color_cycle[index % len(color_cycle)])
            mode = str(spec.get("mode") or "lines")
            y = [item.get(field) for item in points]
            if mode == "bar":
                fig.add_trace(go.Bar(x=x, y=y, name=label, marker_color=color, opacity=.72))
            else:
                fig.add_trace(go.Scatter(
                    x=x, y=y, mode="lines", name=label,
                    line={"color": color, "width": 1.45}, connectgaps=False,
                ))

        for ref in _safe_list(block.get("reference_lines")):
            if not isinstance(ref, dict) or not isinstance(ref.get("value"), (int, float)):
                continue
            fig.add_hline(
                y=float(ref["value"]),
                line_dash=str(ref.get("dash") or "dot"),
                line_width=.9,
                line_color=str(ref.get("color") or MUTED),
            )

    fig.update_layout(
        height=height, paper_bgcolor=BG, plot_bgcolor=PLOT_BG,
        margin={"l": 38, "r": 12, "t": 18, "b": 30},
        font={"family": "Inter, Segoe UI, Arial, sans-serif", "size": 8, "color": TEXT},
        hovermode="x unified",
        legend={"orientation": "h", "x": 0, "y": 1.02, "font": {"size": 7, "color": MUTED}},
        showlegend=True,
        uirevision=f"liq-analysis-{indicator_id}",
    )
    secondary = {"crowding_liquidation_pressure": {"crowding_liquidation_score"}}
    for trace, spec_raw in zip(fig.data, _safe_list(block.get("series"))):
        if str(_safe_dict(spec_raw).get("field")) in secondary.get(indicator_id, set()):
            trace.visible = "legendonly"
    apply_analysis_figure_layout(fig)
    fig.update_xaxes(gridcolor=GRID, zeroline=False, tickfont={"size": 7, "color": MUTED})
    fig.update_yaxes(gridcolor=GRID, zeroline=False, tickfont={"size": 7, "color": MUTED})
    return fig


def _analysis_screen(contract: dict[str, Any]) -> html.Div:
    cards = []
    for indicator_id in ANALYSIS_ORDER:
        cards.append(html.Div(
            className="liq-analysis-card",
            children=[
                html.Div(ANALYSIS_LABELS[indicator_id], className="liq-analysis-card-title"),
                dcc.Graph(
                    figure=_analysis_figure(contract, indicator_id),
                    config={"displaylogo": False, "responsive": True, "scrollZoom": False},
                    style={"height": "310px", "width": "100%"},
                ),
            ],
        ))

    return html.Div(
        className="liq-analysis-shell",
        children=[
            html.Div(className="liq-analysis-back-row", children=[
                dcc.Link("← REGRESAR", href=ROUTE, className="liq-analysis-link"),
            ]),
            html.Div(
                "Pantalla B nativa: liquidaciones realizadas, cascadas, crowding y régimen. Long/Short Ratio es posicionamiento; no se interpreta como liquidación realizada.",
                className="liq-analysis-subtitle",
            ),
            html.Div(cards, className="liq-analysis-grid"),
        ],
    )


def render(
    contract: dict[str, Any],
    view: str,
    market: str | None,
    timeframe: str | None,
    range_id: str | None,
) -> html.Div:
    del market, timeframe, range_id

    if view == "analysis":
        return screen_page(
            _stylesheet(),
            _analysis_screen(contract),
        )

    if view == "reference":
        return screen_page(
            _stylesheet(),
            screen_header(contract),
            reference_gallery(
                REFERENCE_IMAGES
            ),
        )

    charts = _safe_dict(
        contract.get("charts")
    )

    top = html.Div(
        className="liq-top-grid",
        children=[
            _map_card(
                contract,
                charts.get("aggregate_map"),
                map_kind="aggregate",
                graph_id=(
                    "aggregate-liquidation-map"
                ),
                height=365,
            ),
            _positioning_card(contract, height=365),
        ],
    )

    lower = html.Div(
        className="liq-bottom-grid",
        children=[
            _map_card(
                contract,
                charts.get("hyperliquid_map"),
                map_kind="hyperliquid",
                graph_id="hyperliquid-map",
                height=365,
            ),
            _map_card(
                contract,
                charts.get(
                    "binance_leverage_map"
                ),
                map_kind="binance",
                graph_id="binance-leverage-map",
                height=365,
            ),
        ],
    )

    return screen_page(
        _stylesheet(),
        screen_header(contract),
        top,
        _side_panel(contract),
        lower,
    )
