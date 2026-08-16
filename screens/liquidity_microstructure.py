from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import plotly.graph_objects as go
from dash import dcc, html

from screen_core.components import kpi_grid, reference_gallery, screen_header, screen_page
from screen_core.figures import apply_analysis_figure_layout

ROUTE = "/liquidity"
LABEL = "Liquidity"
CONTRACT_FILE = "liquidity_microstructure_VR1_FINAL.json"
HAS_ANALYSIS = True
REFERENCE_IMAGES = ["Liquidity/08_Liquidity_Micro_Structure_A.png"]
SCREEN_REVISION = "LIQUIDITY_SPOT_PERP_MARKET_VIEW_V3"


_GREEN = "#11d978"
_RED = "#ff454f"
_CYAN = "#22c7ff"
_TEXT = "#eef3f8"
_MUTED = "#9ca8b6"
_BORDER = "#22303d"
_CARD = "#0b141d"
_BG = "#071019"

_CARD_STYLE = {
    "background": _CARD,
    "border": f"1px solid {_BORDER}",
    "borderRadius": "8px",
    "overflow": "hidden",
    "minWidth": 0,
}


# ---------- Generic contract helpers ----------

def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _selected_market_contract(contract: dict[str, Any], market: str | None) -> dict[str, Any]:
    """Return the precomputed Spot or Perpetual microstructure view.

    The HMI only selects a contract view; it does not recalculate market metrics.
    """
    selectors = _dict(contract.get("selectors"))
    market_selector = _dict(selectors.get("market"))
    context = _dict(contract.get("context"))
    selected = str(
        market
        or market_selector.get("selected")
        or market_selector.get("default")
        or context.get("selected_market")
        or "perpetual"
    ).lower()
    views = _dict(contract.get("market_views"))
    view = _dict(views.get(selected))
    if not view:
        return contract

    merged = dict(contract)
    for section in ("kpis", "charts", "tables", "widgets", "liquidity_analysis"):
        if section in view:
            merged[section] = view[section]
    merged_context = dict(context)
    merged_context.update(_dict(view.get("context")))
    merged_context["selected_market"] = selected
    merged["context"] = merged_context
    return merged


def _mid_price(contract: dict[str, Any]) -> tuple[str, str]:
    for item in _list(_dict(contract.get("kpis")).get("items")):
        if _dict(item).get("metric_id") == "mid_price":
            metric = _dict(item)
            value = metric.get("value")
            unit = str(metric.get("unit") or "USD")
            if isinstance(value, (int, float)):
                return f"{value:,.0f}", unit
            display = str(metric.get("display_value") or "—").replace("$", "")
            return display, unit
    return "—", "USD"


def _status_message(component: dict[str, Any]) -> str:
    reason = component.get("reason")
    if reason:
        return str(reason).replace("_", " ").upper()
    return str(component.get("status") or "unavailable").replace("_", " ").upper()


def _format_duration(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return "—"
    total = max(0, int(value))
    minutes, seconds = divmod(total, 60)
    if minutes:
        return f"{minutes}m {seconds:02d}s"
    return f"{seconds}s"


def _format_value(field: str, value: Any) -> str:
    if value is None:
        return "—"
    if field == "age_seconds":
        return _format_duration(value)
    if field == "side":
        return str(value).upper()
    if not isinstance(value, (int, float)):
        return str(value)
    if field == "price":
        return f"{value:,.1f}"
    if field in {"quantity_base", "cumulative_quantity_base"}:
        return f"{value:,.2f}"
    if field == "notional_quote":
        amount = float(value)
        if abs(amount) >= 1_000_000:
            return f"${amount / 1_000_000:.2f}M"
        if abs(amount) >= 1_000:
            return f"${amount / 1_000:.2f}K"
        return f"${amount:,.2f}"
    if field == "distance_percent":
        return f"{value:+.2f}%"
    return f"{value:,.2f}"


# ---------- Chart rendering ----------

def _profile_figure(chart: dict[str, Any]) -> go.Figure:
    metadata = _dict(chart.get("metadata"))
    semantic_sides = _dict(metadata.get("semantic_sides"))
    legend_labels = _dict(metadata.get("legend_labels"))
    left_side = str(semantic_sides.get("left") or "bid").lower()
    right_side = str(semantic_sides.get("right") or "ask").lower()
    records = [_dict(row) for row in _list(chart.get("records"))]

    fig = go.Figure()

    def add_side(side: str, *, left: bool, color: str, default_label: str) -> None:
        rows = [row for row in records if str(row.get("side", "")).lower() == side]
        rows.sort(key=lambda row: abs(float(row.get("distance_percent") or 0.0)))
        if not rows:
            return
        x = []
        y = []
        for row in rows:
            distance = abs(float(row.get("distance_percent") or 0.0))
            x.append(-distance if left else distance)
            y.append(float(row.get("cumulative_quantity_base") or 0.0))
        label = str(legend_labels.get(side) or default_label)
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines",
                name=label,
                line={"color": color, "width": 2, "shape": "hv"},
                fill="tozeroy",
                fillcolor="rgba(17,217,120,0.22)" if left else "rgba(255,69,79,0.22)",
                hovertemplate="%{x:.2f}%<br>%{y:.2f} BTC<extra>%{fullData.name}</extra>",
            )
        )

    add_side(left_side, left=True, color=_GREEN, default_label=left_side.upper())
    add_side(right_side, left=False, color=_RED, default_label=right_side.upper())

    fig.add_vline(x=0, line_width=1, line_dash="dash", line_color="#9aa6b2")
    fig.update_layout(
        margin={"l": 48, "r": 16, "t": 8, "b": 40},
        paper_bgcolor=_CARD,
        plot_bgcolor=_CARD,
        font={"color": _TEXT, "size": 11},
        hovermode="x unified",
        legend={
            "orientation": "h",
            "yanchor": "top",
            "y": -0.18,
            "xanchor": "center",
            "x": 0.5,
            "font": {"size": 10},
        },
        xaxis={
            "title": None,
            "ticksuffix": "%",
            "showgrid": False,
            "zeroline": False,
            "color": _MUTED,
        },
        yaxis={
            "title": "BTC (Acumulado)",
            "showgrid": True,
            "gridcolor": "rgba(255,255,255,0.05)",
            "zeroline": False,
            "color": _MUTED,
        },
    )

    if not records:
        fig.add_annotation(
            text=_status_message(chart),
            x=0.5,
            y=0.52,
            xref="paper",
            yref="paper",
            showarrow=False,
            font={"color": _MUTED, "size": 12},
        )
    return fig


def _chart_card(
    contract: dict[str, Any],
    chart: dict[str, Any],
    ordinal: int,
    panel_title: str,
    panel_subtitle: str,
    graph_id: str,
) -> html.Div:
    mid_value, mid_unit = _mid_price(contract)
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                f"{ordinal}. {panel_title}",
                                style={"fontWeight": 700, "fontSize": "16px", "color": _TEXT},
                            ),
                            html.Div(
                                panel_subtitle,
                                style={"fontSize": "11px", "color": _MUTED, "marginTop": "3px"},
                            ),
                        ]
                    ),
                    html.Div(
                        [
                            html.Div("Mid Price", style={"fontSize": "10px", "color": _MUTED}),
                            html.Div(mid_value, style={"fontSize": "18px", "fontWeight": 700, "color": _TEXT}),
                            html.Div(mid_unit, style={"fontSize": "10px", "color": _MUTED}),
                        ],
                        style={"textAlign": "right"},
                    ),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "gap": "12px",
                    "padding": "12px 14px 4px 14px",
                },
            ),
            html.Div(
                str(chart.get("title") or ""),
                style={
                    "textAlign": "center",
                    "fontSize": "11px",
                    "fontWeight": 600,
                    "color": _TEXT,
                    "paddingTop": "6px",
                },
            ),
            dcc.Graph(
                id=graph_id,
                figure=_profile_figure(chart),
                config={"displayModeBar": False, "responsive": True},
                style={"height": "280px", "minHeight": "280px"},
            ),
        ],
        style=_CARD_STYLE,
    )


def _executed_operations_figure(chart: dict[str, Any]) -> go.Figure:
    timestamps = _list(chart.get("timestamps"))
    buy = _list(chart.get("buy_executed"))
    sell = _list(chart.get("sell_executed"))
    net = _list(chart.get("net_pressure"))
    size = min(len(timestamps), len(buy), len(sell), len(net))
    x = [_dt(value) for value in timestamps[:size]]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=x,
            y=buy[:size],
            name="BUY EXECUTED",
            marker_color=_GREEN,
            hovertemplate="BUY: $%{y:,.0f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            x=x,
            y=sell[:size],
            name="SELL EXECUTED",
            marker_color=_RED,
            hovertemplate="SELL: $%{y:,.0f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x,
            y=net[:size],
            mode="lines",
            name="NET PRESSURE",
            line={"color": _CYAN, "width": 1.8},
            hovertemplate="NET: $%{y:,.0f}<extra></extra>",
        )
    )
    fig.add_hline(
        y=0,
        line_width=1,
        line_dash="dot",
        line_color="rgba(200,214,226,.50)",
    )
    fig.update_layout(
        height=300,
        barmode="group",
        bargap=0.18,
        paper_bgcolor=_CARD,
        plot_bgcolor=_CARD,
        margin={"l": 56, "r": 18, "t": 16, "b": 62},
        font={"color": _TEXT, "size": 9},
        hovermode="x unified",
        legend={
            "orientation": "h",
            "yanchor": "top",
            "y": -0.20,
            "xanchor": "center",
            "x": 0.5,
            "font": {"size": 8},
            "bgcolor": "rgba(0,0,0,0)",
        },
    )
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        color=_MUTED,
        nticks=8,
        tickformat="%H:%M",
    )
    fig.update_yaxes(
        title_text="USD EXECUTED",
        showgrid=True,
        gridcolor="rgba(255,255,255,0.05)",
        zeroline=False,
        color=_MUTED,
    )
    if not size:
        fig.add_annotation(
            text=_status_message(chart),
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font={"color": _MUTED, "size": 11},
        )
    return fig


def _executed_operations_card(chart: dict[str, Any]) -> html.Div:
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        "4. EXECUTED LIQUIDITY / OPERATIONS",
                        style={"fontWeight": 700, "fontSize": "16px", "color": _TEXT},
                    ),
                    html.Div(
                        "Aggregated aggressive execution interacting with available liquidity",
                        style={"fontSize": "11px", "color": _MUTED, "marginTop": "3px"},
                    ),
                ],
                style={"padding": "12px 14px 4px"},
            ),
            dcc.Graph(
                id="liquidity-executed-operations",
                figure=_executed_operations_figure(chart),
                config={"displayModeBar": False, "responsive": True},
                style={"height": "300px", "minHeight": "300px"},
            ),
        ],
        style={**_CARD_STYLE, "marginTop": "8px"},
    )


# ---------- Table rendering ----------

def _table_cell(text: str, *, color: str | None = None, align: str = "right") -> html.Td:
    return html.Td(
        text,
        style={
            "padding": "4px 8px",
            "borderBottom": "1px solid rgba(255,255,255,0.045)",
            "fontSize": "10px",
            "fontFamily": "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
            "textAlign": align,
            "whiteSpace": "nowrap",
            "color": color or _TEXT,
        },
    )


def _display_limit(table: dict[str, Any], default: int = 16) -> int:
    metadata = _dict(table.get("metadata"))
    value = metadata.get("display_limit")
    if isinstance(value, (int, float)):
        return max(1, int(value))
    return default


def _display_columns(table: dict[str, Any], fallback: list[tuple[str, str]]) -> list[tuple[str, str]]:
    configured = _list(table.get("display_columns"))
    parsed: list[tuple[str, str]] = []
    for item in configured:
        item = _dict(item)
        field = item.get("field")
        if field:
            parsed.append((str(field), str(item.get("label") or field)))
    return parsed or fallback


def _side_book(side: str, rows: list[dict[str, Any]], columns: list[tuple[str, str]], display_limit: int) -> html.Div:
    color = _GREEN if side == "bid" else _RED
    label = "BIDS" if side == "bid" else "ASKS"
    head = html.Thead(
        html.Tr(
            [
                html.Th(
                    label,
                    colSpan=len(columns),
                    style={
                        "padding": "7px 8px",
                        "textAlign": "left" if side == "bid" else "right",
                        "color": color,
                        "background": "rgba(17,217,120,0.12)" if side == "bid" else "rgba(255,69,79,0.12)",
                        "borderBottom": f"1px solid {color}",
                        "fontSize": "10px",
                    },
                )
            ]
        )
    )
    column_row = html.Tr(
        [
            html.Th(
                label_text,
                style={
                    "padding": "5px 8px",
                    "fontSize": "9px",
                    "fontWeight": 600,
                    "color": color if field == "price" else _MUTED,
                    "textAlign": "right",
                    "whiteSpace": "nowrap",
                },
            )
            for field, label_text in columns
        ]
    )
    body_rows = []
    for row in rows[:display_limit]:
        body_rows.append(
            html.Tr(
                [
                    _table_cell(
                        _format_value(field, row.get(field)),
                        color=color if field == "price" else None,
                    )
                    for field, _ in columns
                ]
            )
        )
    if not body_rows:
        body_rows.append(
            html.Tr(
                [
                    html.Td(
                        "NO DATA",
                        colSpan=len(columns),
                        style={"padding": "18px", "textAlign": "center", "color": _MUTED, "fontSize": "10px"},
                    )
                ]
            )
        )
    return html.Div(
        html.Table(
            [head, html.Thead(column_row), html.Tbody(body_rows)],
            style={"width": "100%", "borderCollapse": "collapse", "tableLayout": "fixed"},
        ),
        style={"minWidth": 0, "flex": 1},
    )


def _orderbook_table_card(table: dict[str, Any]) -> html.Div:
    columns = _display_columns(
        table,
        [
            ("price", "Precio (USDT)"),
            ("quantity_base", "Tamaño (BTC)"),
            ("cumulative_quantity_base", "Acumulado (BTC)"),
        ],
    )[:3]
    bids = [_dict(row) for row in _list(table.get("bids"))]
    asks = [_dict(row) for row in _list(table.get("asks"))]
    display_limit = _display_limit(table, 16)
    summary = _dict(table.get("summary"))
    base_summary = _dict(summary.get("base_quantity"))
    return html.Div(
        [
            html.Div(
                str(table.get("title") or "ORDER BOOK SNAPSHOT"),
                style={"padding": "10px 12px", "fontSize": "13px", "fontWeight": 700, "color": _TEXT},
            ),
            html.Div(
                [
                    _side_book("bid", bids, columns, display_limit),
                    _side_book("ask", asks, columns, display_limit),
                ],
                style={
                    "display": "flex",
                    "gap": "8px",
                    "padding": "0 8px",
                    "maxHeight": "360px",
                    "overflowY": "auto",
                },
            ),
            html.Div(
                [
                    html.Div(
                        [html.Span("Total Bids"), html.Strong(f"{float(base_summary.get('bid') or 0):,.2f} BTC")],
                        style={"display": "flex", "justifyContent": "space-between", "color": _GREEN},
                    ),
                    html.Div(
                        [html.Span("Total Asks"), html.Strong(f"{float(base_summary.get('ask') or 0):,.2f} BTC")],
                        style={"display": "flex", "justifyContent": "space-between", "color": _RED},
                    ),
                ],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "1fr 1fr",
                    "gap": "16px",
                    "padding": "10px 12px",
                    "borderTop": f"1px solid {_BORDER}",
                    "fontSize": "10px",
                    "marginTop": "8px",
                },
            ),
        ],
        style=_CARD_STYLE,
    )


def _event_table_card(table: dict[str, Any], fallback_title: str) -> html.Div:
    columns = _display_columns(
        table,
        [
            ("age_seconds", "Time"),
            ("side", "Side"),
            ("price", "Price (USDT)"),
            ("quantity_base", "Size (BTC)"),
            ("notional_quote", "Notional (USD)"),
            ("distance_percent", "Distance"),
        ],
    )
    rows = [_dict(row) for row in _list(table.get("rows"))]
    display_limit = _display_limit(table, 16)

    header = html.Tr(
        [
            html.Th(
                label,
                style={
                    "padding": "7px 8px",
                    "fontSize": "9px",
                    "fontWeight": 600,
                    "color": _MUTED,
                    "textAlign": "right" if field != "side" else "center",
                    "whiteSpace": "nowrap",
                    "borderBottom": f"1px solid {_BORDER}",
                },
            )
            for field, label in columns
        ]
    )

    body = []
    for row in rows[:display_limit]:
        cells = []
        for field, _ in columns:
            value = row.get(field)
            if field == "side":
                side = str(value or "").lower()
                color = _GREEN if side == "buy" else _RED if side == "sell" else _TEXT
                cells.append(_table_cell(_format_value(field, value), color=color, align="center"))
            else:
                cells.append(_table_cell(_format_value(field, value)))
        body.append(html.Tr(cells))

    if not body:
        body.append(
            html.Tr(
                [
                    html.Td(
                        _status_message(table),
                        colSpan=max(1, len(columns)),
                        style={
                            "height": "176px",
                            "textAlign": "center",
                            "color": _MUTED,
                            "fontSize": "10px",
                            "borderBottom": f"1px solid {_BORDER}",
                        },
                    )
                ]
            )
        )

    summary = _dict(table.get("summary"))
    buy = _dict(summary.get("buy"))
    sell = _dict(summary.get("sell"))
    buy_qty = buy.get("quantity_base")
    sell_qty = sell.get("quantity_base")
    buy_text = f"{float(buy_qty):,.2f} BTC" if isinstance(buy_qty, (int, float)) else _format_value("notional_quote", buy.get("notional_quote"))
    sell_text = f"{float(sell_qty):,.2f} BTC" if isinstance(sell_qty, (int, float)) else _format_value("notional_quote", sell.get("notional_quote"))

    table_max_height = (
        "470px"
        if fallback_title == "LARGE TRADES"
        else "360px"
    )

    return html.Div(
        [
            html.Div(
                [
                    html.Span(str(table.get("title") or fallback_title)),
                    html.Span(
                        f"{min(len(rows), display_limit)} / {len(rows)} visibles",
                        style={
                            "fontSize": "8px",
                            "fontWeight": 500,
                            "color": _MUTED,
                        },
                    ),
                ],
                style={
                    "padding": "10px 12px",
                    "fontSize": "13px",
                    "fontWeight": 700,
                    "color": _TEXT,
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                    "gap": "8px",
                },
            ),
            html.Div(
                html.Table(
                    [html.Thead(header), html.Tbody(body)],
                    style={"width": "100%", "borderCollapse": "collapse", "tableLayout": "fixed"},
                ),
                style={
                    "overflowX": "auto",
                    "overflowY": "auto",
                    "maxHeight": table_max_height,
                    "padding": "0 8px",
                },
            ),
            html.Div(
                [
                    html.Div(
                        [html.Span("Buy Total"), html.Strong(buy_text)],
                        style={"display": "flex", "justifyContent": "space-between", "color": _GREEN},
                    ),
                    html.Div(
                        [html.Span("Sell Total"), html.Strong(sell_text)],
                        style={"display": "flex", "justifyContent": "space-between", "color": _RED},
                    ),
                ],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "1fr 1fr",
                    "gap": "16px",
                    "padding": "10px 12px",
                    "borderTop": f"1px solid {_BORDER}",
                    "fontSize": "10px",
                    "marginTop": "8px",
                },
            ),
        ],
        style=_CARD_STYLE,
    )




# ---------- Native Screen B rendering ----------

def _dt(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    return None


def _analysis_records(contract: dict[str, Any]) -> list[dict[str, Any]]:
    block = _dict(contract.get("liquidity_analysis"))
    records = [
        _dict(item)
        for item in _list(block.get("records"))
        if isinstance(item, dict) and item.get("timestamp") is not None
    ]
    tail = block.get("display_tail_records")
    if isinstance(tail, int) and tail > 0:
        records = records[-tail:]
    return records


def _native_line_figure(
    records: list[dict[str, Any]],
    series_spec: list[tuple[str, str, str]],
    *,
    zero_line: bool = False,
    reference_line: float | None = None,
    y_title: str = "",
) -> go.Figure:
    fig = go.Figure()
    x = [_dt(row.get("timestamp")) for row in records]
    for field, label, color in series_spec:
        y = [row.get(field) for row in records]
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines",
                name=label,
                line={"color": color, "width": 1.55},
                connectgaps=False,
                hovertemplate=f"{label}: %{{y:.4f}}<extra></extra>",
            )
        )
    if zero_line:
        fig.add_hline(y=0, line_width=1, line_dash="dot", line_color="rgba(200,214,226,.50)")
    if reference_line is not None:
        fig.add_hline(y=reference_line, line_width=1, line_dash="dot", line_color="rgba(200,214,226,.50)")
    fig.update_layout(
        height=310,
        paper_bgcolor=_BG,
        plot_bgcolor=_BG,
        margin={"l": 42, "r": 14, "t": 18, "b": 30},
        font={"family": "Arial, sans-serif", "size": 8, "color": _MUTED},
        hovermode="x unified",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "x": 0,
            "font": {"size": 7},
            "bgcolor": "rgba(0,0,0,0)",
        },
    )
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor="#173247",
        tickfont={"size": 7, "color": _MUTED},
        nticks=6,
        tickformat="%b %d\n%H:%M",
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(67,91,108,.22)",
        zeroline=False,
        linecolor="#173247",
        tickfont={"size": 7, "color": _MUTED},
        title_text=y_title,
    )
    return apply_analysis_figure_layout(fig)


def _analysis_card(title: str, subtitle: str, figure: go.Figure) -> html.Div:
    return html.Div(
        [
            html.Div(
                [
                    html.Div(title, style={"fontSize": "11px", "fontWeight": 800, "color": _TEXT}),
                    html.Div(subtitle, style={"fontSize": "8px", "color": _MUTED, "marginTop": "2px"}),
                ],
                style={"padding": "9px 10px 4px"},
            ),
            dcc.Graph(
                figure=figure,
                config={"displayModeBar": False, "responsive": True},
                style={"height": "310px"},
            ),
        ],
        style={**_CARD_STYLE, "minHeight": "365px"},
    )


def _analysis_summary(contract: dict[str, Any]) -> html.Div:
    current = _dict(_dict(contract.get("liquidity_analysis")).get("current"))
    items = [
        ("REGIME", str(current.get("liquidity_regime") or "—")),
        ("DEPTH IMBALANCE", f"{float(current.get('depth_imbalance') or 0.0):+.3f}"),
        ("LIQUIDITY STRESS", f"{float(current.get('liquidity_stress_score') or 0.0):+.2f}"),
        ("ABSORPTION", f"{float(current.get('absorption_index') or 0.0):+.2f}"),
        ("WASSERSTEIN", f"{float(current.get('wasserstein_distance') or 0.0):.3f}"),
    ]
    return html.Div(
        [
            html.Div(
                [
                    html.Div(label, style={"fontSize": "7px", "color": _MUTED}),
                    html.Div(value, style={"fontSize": "12px", "fontWeight": 800, "color": _TEXT, "marginTop": "2px"}),
                ],
                style={"padding": "8px 10px", "borderRight": f"1px solid {_BORDER}" if i < len(items)-1 else "none"},
            )
            for i, (label, value) in enumerate(items)
        ],
        style={
            "display": "grid",
            "gridTemplateColumns": "2fr 1fr 1fr 1fr 1fr",
            "background": _CARD,
            "border": f"1px solid {_BORDER}",
            "borderRadius": "8px",
            "marginBottom": "8px",
            "overflow": "hidden",
        },
    )


def _analysis_view(contract: dict[str, Any]) -> html.Div:
    records = _analysis_records(contract)
    if not records:
        return screen_page(
            html.Div(
                "LIQUIDITY SCREEN B UNAVAILABLE",
                style={"padding": "40px", "textAlign": "center", "color": _MUTED},
            ),
        )

    depth = _native_line_figure(
        records,
        [
            ("depth_imbalance", "IMBALANCE", _CYAN),
            ("depth_imbalance_zscore", "Z-SCORE", "#a879ff"),
            ("bid_ask_depth_ratio", "BID/ASK RATIO", _GREEN),
        ],
        zero_line=True,
    )
    stress = _native_line_figure(
        records,
        [
            ("spread_bps", "SPREAD BPS", "#f2c94c"),
            ("market_impact_1btc_bps", "IMPACT 1 BTC", "#ff8a3d"),
            ("liquidity_stress_score", "STRESS SCORE", _RED),
        ],
        zero_line=True,
    )
    walls = _native_line_figure(
        records,
        [
            ("bid_wall_score", "BID WALL", _GREEN),
            ("ask_wall_score", "ASK WALL", _RED),
            ("upside_vacuum_score", "UPSIDE VACUUM", _CYAN),
            ("downside_vacuum_score", "DOWNSIDE VACUUM", "#a879ff"),
        ],
    )
    whale = _native_line_figure(
        records,
        [
            ("whale_persistence_score", "PERSISTENCE", _GREEN),
            ("cancellation_activity", "CANCELLATION", _RED),
            ("cancellation_activity_zscore", "CANCEL Z", "#f2c94c"),
        ],
        zero_line=True,
    )
    absorption = _native_line_figure(
        records,
        [
            ("buy_absorption_score", "BUY ABSORPTION", _GREEN),
            ("sell_absorption_score", "SELL ABSORPTION", _RED),
            ("absorption_index", "NET ABSORPTION", _CYAN),
        ],
        zero_line=True,
    )
    regime = _native_line_figure(
        records,
        [
            ("liquidity_hmi_score", "LIQUIDITY HMI", _CYAN),
            ("wasserstein_distance", "WASSERSTEIN", "#a879ff"),
        ],
        zero_line=True,
    )
    for figure, hidden_names in (
        (depth, {"BID/ASK RATIO"}),
        (stress, {"SPREAD BPS"}),
        (walls, {"UPSIDE VACUUM", "DOWNSIDE VACUUM"}),
        (whale, {"CANCEL Z"}),
        (absorption, {"SELL ABSORPTION"}),
    ):
        for trace in figure.data:
            if trace.name in hidden_names:
                trace.visible = "legendonly"

    grid = html.Div(
        [
            _analysis_card("DEPTH IMBALANCE / PRESSURE", "Bid/ask depth asymmetry and normalized pressure", depth),
            _analysis_card("SPREAD × MARKET IMPACT / LIQUIDITY STRESS", "Execution friction and deterioration of available liquidity", stress),
            _analysis_card("LIQUIDITY WALL / CONCENTRATION + VACUUM", "Resting walls and thin-book directional gaps", walls),
            _analysis_card("WHALE PERSISTENCE / CANCELLATION ACTIVITY", "Persistence of large resting orders versus rapid withdrawal", whale),
            _analysis_card("EXECUTED LIQUIDITY / ABSORPTION", "Aggressive flow absorbed by visible opposing liquidity", absorption),
            _analysis_card("LIQUIDITY REGIME / HMI + WASSERSTEIN", "Composite microstructure state and regime displacement", regime),
        ],
        className="analysis-grid",
    )

    return screen_page(
        _analysis_summary(contract),
        grid,
    )


# ---------- Screen ----------

def render(
    contract: dict[str, Any],
    view: str,
    market: str | None,
    timeframe: str | None,
    range_id: str | None,
) -> html.Div:
    selected_contract = _selected_market_contract(contract, market)

    if view == "reference":
        return screen_page(screen_header(selected_contract), reference_gallery(REFERENCE_IMAGES))
    if view == "analysis":
        return _analysis_view(selected_contract)

    charts = _dict(selected_contract.get("charts"))
    tables = _dict(selected_contract.get("tables"))

    chart_row = html.Div(
        [
            _chart_card(
                selected_contract,
                _dict(charts.get("order_depth")),
                1,
                "ORDER BOOK",
                "Profundidad acumulada del libro",
                "liquidity-order-depth",
            ),
            _chart_card(
                selected_contract,
                _dict(charts.get("whale_liquidity_profile")),
                2,
                "WHALE ORDERS",
                "Órdenes de tamaño extraordinario y liquidez asociada",
                "liquidity-whale-profile",
            ),
            _chart_card(
                selected_contract,
                _dict(charts.get("executed_liquidity_profile")),
                3,
                "LARGE TRADES",
                "Operaciones grandes ejecutadas y liquidez consumida",
                "liquidity-executed-profile",
            ),
        ],
        className="three-panel-grid",
        style={"gap": "8px"},
    )

    table_row = html.Div(
        [
            _orderbook_table_card(_dict(tables.get("orderbook_snapshot"))),
            _event_table_card(_dict(tables.get("whale_orders")), "WHALE ORDERS"),
            _event_table_card(_dict(tables.get("large_trades")), "LARGE TRADES"),
        ],
        className="three-panel-grid",
        style={"gap": "8px"},
    )

    executed_operations = _executed_operations_card(
        _dict(charts.get("executed_operations"))
    )

    return screen_page(
        screen_header(selected_contract),
        kpi_grid(selected_contract.get("kpis")),
        chart_row,
        table_row,
        executed_operations,
    )
