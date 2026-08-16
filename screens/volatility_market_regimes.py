from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

from screen_core.components import kpi_grid, reference_gallery, screen_header, screen_page
from screen_core.figures import apply_analysis_figure_layout

ROUTE = "/volatility-market-regimes"
LABEL = "Volatility"
CONTRACT_FILE = "volatility_market_regimes_VR1_FINAL.json"
HAS_ANALYSIS = True
SCREEN_REVISION = "VOL_NATIVE_V2"

REFERENCE_IMAGES = [
    "Volatility/06_Volatility_Regimes_A.png",
    "Volatility/06_Volatility_Regimes_B.png",
]

BG = "#06111d"
PLOT_BG = "#071522"
GRID = "rgba(91,126,155,.16)"
TEXT = "#d9e8f5"
MUTED = "#7f96aa"
GREEN = "#17d49b"
RED = "#ff506e"
BLUE = "#2f80ff"
PURPLE = "#a879ff"
ORANGE = "#f2994a"
CYAN = "#00c2ff"

RANGE_POINTS = {"7d": 7, "30d": 30, "90d": 90, "360d": 360}
SELECTION_STORE_ID = "vol-native-selection"
ANALYSIS_CONTENT_ID = "vol-native-analysis-content"

ANALYSIS_ORDER = [
    "volatility_zscore_percentile",
    "volatility_risk_premium",
    "term_structure_slope",
    "volatility_skew_tail_risk",
    "vol_of_vol_acceleration",
    "regime_shift_wasserstein",
]

CSS = """
.vol-native-main {display:grid;grid-template-columns:minmax(0,1fr) 286px;gap:8px;align-items:start;}
.vol-native-grid {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;}
.vol-native-card {border:1px solid #173247;background:#06111d;min-width:0;}
.vol-native-panel {border:1px solid #173247;background:#06111d;padding:10px;min-height:588px;}
.vol-native-panel h3 {font-size:11px;color:#57a8ff;margin:0 0 8px;text-transform:uppercase;}
.vol-native-section {border-top:1px solid #173247;padding-top:8px;margin-top:8px;}
.vol-native-label {font-size:8px;color:#718da3;text-transform:uppercase;margin-bottom:5px;}
.vol-native-note {font-size:8px;color:#7f96aa;line-height:1.45;margin:7px 0;}
.vol-native-check label {font-size:9px;color:#d9e8f5;margin-right:8px;display:block;margin-bottom:6px;}
.vol-native-link {display:block;text-align:center;border:1px solid #2f80ff;color:#62afff;text-decoration:none;font-size:10px;font-weight:700;padding:8px;margin-bottom:10px;}
.vol-analysis-grid {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;min-width:0;}
.vol-analysis-card {border:1px solid #173247;background:#06111d;min-width:0;}
.vol-analysis-title {height:26px;display:flex;align-items:center;padding:0 8px;font-size:8px;color:#8cb3d2;border-bottom:1px solid #173247;text-transform:uppercase;}
.vol-analysis-back {display:inline-block;border:1px solid #2f80ff;color:#62afff;text-decoration:none;padding:6px 12px;font-size:9px;font-weight:700;margin-bottom:8px;}
@media (max-width:1100px){.vol-native-main{grid-template-columns:1fr}.vol-native-panel{min-height:auto}.vol-analysis-grid{grid-template-columns:repeat(2,minmax(0,1fr));}}
@media (max-width:760px){.vol-native-grid,.vol-analysis-grid{grid-template-columns:1fr}}
"""


def _volatility_stylesheet() -> html.Link:
    """Load screen-local CSS using a Dash-supported component."""
    return html.Link(
        rel="stylesheet",
        href="data:text/css;charset=utf-8," + quote(CSS, safe=""),
    )

def _safe_dict(v: Any) -> dict[str, Any]: return v if isinstance(v, dict) else {}
def _safe_list(v: Any) -> list[Any]: return v if isinstance(v, list) else []
def _dt(value: Any) -> datetime | None:
    try: return datetime.fromtimestamp(float(value), tz=timezone.utc)
    except (TypeError, ValueError, OSError, OverflowError): return None

def _range_records(records: list[dict[str, Any]], range_id: str | None) -> list[dict[str, Any]]:
    n = RANGE_POINTS.get(str(range_id or "30d").lower(), 30)
    return records[-n:] if n > 0 else records

def _base_layout(fig: go.Figure, title: str, height: int = 272) -> go.Figure:
    fig.update_layout(
        title={"text": title, "x": .01, "font": {"size": 10, "color": TEXT}},
        height=height, paper_bgcolor=BG, plot_bgcolor=PLOT_BG,
        margin={"l": 44, "r": 16, "t": 36, "b": 28},
        font={"family":"Inter, Segoe UI, sans-serif","color":TEXT,"size":8},
        hovermode="x unified", legend={"orientation":"h","y":1.02,"x":0,"font":{"size":8}},
        uirevision=title,
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, tickfont={"size":8,"color":MUTED})
    fig.update_yaxes(gridcolor=GRID, zeroline=False, tickfont={"size":8,"color":MUTED})
    return fig

def _screen_a_figure(contract: dict[str, Any], chart_id: str, range_id: str | None) -> go.Figure:
    chart = _safe_dict(_safe_dict(contract.get("charts")).get(chart_id))
    rec = _range_records([r for r in _safe_list(chart.get("records")) if isinstance(r,dict)], range_id)
    fig = go.Figure()
    x = [_dt(r.get("timestamp")) for r in rec]
    if chart_id == "realized_volatility":
        fig.add_trace(go.Scatter(x=x,y=[r.get("rv_7d") for r in rec],name="RV 7D",mode="lines",line={"width":1.7,"color":CYAN}))
        fig.add_trace(go.Scatter(x=x,y=[r.get("rv_30d") for r in rec],name="RV 30D",mode="lines",line={"width":1.4,"color":BLUE}))
        fig.update_yaxes(title_text="%")
    elif chart_id == "implied_volatility":
        fig.add_trace(go.Scatter(x=x,y=[r.get("dvol") for r in rec],name="DVOL",mode="lines",line={"width":1.7,"color":PURPLE}))
        fig.add_trace(go.Scatter(x=x,y=[r.get("iv_1m") for r in rec],name="IV 1M",mode="lines",line={"width":1.35,"color":ORANGE}))
        fig.update_yaxes(title_text="%")
    elif chart_id == "implied_vs_realized":
        fig.add_trace(go.Scatter(x=x,y=[r.get("iv_1m") for r in rec],name="IV 1M",mode="lines",line={"width":1.55,"color":PURPLE}))
        fig.add_trace(go.Scatter(x=x,y=[r.get("rv_30d") for r in rec],name="RV 30D",mode="lines",line={"width":1.55,"color":CYAN}))
        fig.add_trace(go.Scatter(x=x,y=[r.get("vrp") for r in rec],name="VRP",mode="lines",line={"width":1.15,"color":GREEN,"dash":"dot"}))
        fig.add_hline(y=0,line_dash="dot",line_color="#496275",line_width=.8)
    elif chart_id == "term_structure":
        if rec:
            current=rec[-1]
            old=rec[max(0,len(rec)-min(len(rec),30))]
            tenors=["1W","1M","3M","6M"]
            keys=["iv_1w","iv_1m","iv_3m","iv_6m"]
            fig.add_trace(go.Scatter(x=tenors,y=[current.get(k) for k in keys],name="CURRENT",mode="lines+markers",line={"width":1.7,"color":PURPLE},marker={"size":6}))
            fig.add_trace(go.Scatter(x=tenors,y=[old.get(k) for k in keys],name="REFERENCE",mode="lines+markers",line={"width":1.1,"color":MUTED,"dash":"dot"},marker={"size":5}))
        fig.update_yaxes(title_text="IV %")
    return _base_layout(fig, str(chart.get("title") or chart_id).upper())

def _analysis_figure(block: dict[str, Any], indicator_id: str, range_id: str | None) -> go.Figure:
    timestamps=_safe_list(block.get("timestamps")); series=_safe_dict(block.get("series"))
    n=RANGE_POINTS.get(str(range_id or "30d").lower(),30)
    timestamps=timestamps[-n:]
    fig=go.Figure(); x=[_dt(t) for t in timestamps]
    colors=[BLUE,CYAN,PURPLE,ORANGE,GREEN,RED]
    for idx,(name,values) in enumerate(series.items()):
        vals=_safe_list(values)[-n:]
        if indicator_id == "volatility_zscore_percentile" and name == "rv_percentile":
            fig.add_trace(go.Scatter(x=x,y=vals,name="PERCENTILE",mode="lines",line={"width":1.15,"color":PURPLE},yaxis="y2"))
        elif indicator_id == "regime_shift_wasserstein" and name == "transition_probability":
            fig.add_trace(go.Scatter(x=x,y=vals,name="TRANSITION %",mode="lines",line={"width":1.15,"color":RED},yaxis="y2"))
        else:
            fig.add_trace(go.Scatter(x=x,y=vals,name=name.replace("_"," ").upper(),mode="lines",line={"width":1.35,"color":colors[idx%len(colors)]}))
    fig.update_layout(yaxis2={"overlaying":"y","side":"right","showgrid":False,"tickfont":{"size":7,"color":MUTED}})
    compact = {"RV ZSCORE": "RV Z-Score", "RV PERCENTILE": "Percentile",
               "VOLATILITY RISK PREMIUM": "VRP", "VRP ZSCORE": "VRP Z-Score",
               "TERM SLOPE": "Term Slope", "TERM CURVATURE": "Term Curvature",
               "SKEW 25D": "Skew 25D", "DOWNSIDE IV": "Downside IV", "UPSIDE IV": "Upside IV",
               "VOL OF VOL": "Vol-of-Vol", "RV ACCELERATION": "RV Acceleration",
               "WASSERSTEIN DISTANCE": "Wasserstein", "TRANSITION %": "Transition %"}
    for trace in fig.data:
        trace.name = compact.get(str(trace.name), str(trace.name).title())
        if indicator_id == "volatility_skew_tail_risk" and trace.name == "Upside IV":
            trace.visible = "legendonly"
    _base_layout(fig, None, height=310)
    return apply_analysis_figure_layout(fig, right_margin=38)

def _selection_panel() -> html.Div:
    groups=[
        ("VOLATILITY LEVEL · PANTALLA B","vol-level-select",[{"label":"Volatility Z-Score / Percentile","value":"volatility_zscore_percentile"}]),
        ("VOLATILITY PRICING · PANTALLA B","vol-pricing-select",[{"label":"Volatility Risk Premium","value":"volatility_risk_premium"}]),
        ("OPTIONS STRUCTURE · PANTALLA B","vol-options-select",[{"label":"IV Term Structure / Slope","value":"term_structure_slope"},{"label":"Volatility Skew / Tail Risk","value":"volatility_skew_tail_risk"}]),
        ("VOLATILITY DYNAMICS · PANTALLA B","vol-dynamics-select",[{"label":"Vol-of-Vol / Acceleration","value":"vol_of_vol_acceleration"}]),
        ("REGIME · PANTALLA B","vol-regime-select",[{"label":"Regime Shift / Wasserstein","value":"regime_shift_wasserstein"}]),
    ]
    children=[dcc.Link("ANÁLISIS DE VOLATILIDAD Y REGÍMENES ↗",href=f"{ROUTE}/analysis",className="vol-native-link"),
              html.H3("VOLATILITY & MARKET REGIMES · PANTALLA B"),
              html.Div("Analítica nativa de volatilidad. La HMI solo grafica métricas precomputadas por Processing; no aplica RSI/MACD/ATR ni medias móviles a volatilidad.",className="vol-native-note")]
    for title,cid,opts in groups:
        children.append(html.Div(className="vol-native-section",children=[html.Div(title,className="vol-native-label"),dcc.Checklist(id=cid,options=opts,value=[o["value"] for o in opts],className="vol-native-check")]))
    return html.Div(className="vol-native-panel",children=children)

def _analysis_screen(contract: dict[str, Any], range_id: str | None, selection: list[str] | None) -> html.Div:
    selected=set(selection or ANALYSIS_ORDER)
    ind=_safe_dict(_safe_dict(contract.get("volatility_analysis")).get("indicators"))
    cards=[]
    for iid in ANALYSIS_ORDER:
        if iid not in selected: continue
        block=_safe_dict(ind.get(iid))
        cards.append(html.Div(className="vol-analysis-card",children=[html.Div([
            html.Span(str(block.get("section") or "ANALYSIS")),
            html.Span(" · "),
            html.Span(str(block.get("label") or iid).upper()),
        ],className="vol-analysis-title"),dcc.Graph(figure=_analysis_figure(block,iid,range_id),config={"displaylogo":False,"responsive":True},style={"height":"310px"})]))
    return html.Div(children=[dcc.Link("← REGRESAR",href=ROUTE,className="vol-analysis-back"),html.Div(className="vol-analysis-grid",children=cards)])

@callback(
    Output(SELECTION_STORE_ID,"data"),
    Input("vol-level-select","value"),Input("vol-pricing-select","value"),Input("vol-options-select","value"),Input("vol-dynamics-select","value"),Input("vol-regime-select","value"),
    prevent_initial_call=True,
)
def _save_selection(*groups: Any) -> list[str]:
    out=[]
    for g in groups:
        for item in (g or []):
            if item not in out: out.append(item)
    return out

@callback(Output(ANALYSIS_CONTENT_ID,"children"),Input(SELECTION_STORE_ID,"data"),Input("range-selector","value"),prevent_initial_call=False)
def _refresh_analysis(selection: list[str] | None, range_id: str | None) -> html.Div:
    from screen_core.contract_loader import load_contract
    return _analysis_screen(load_contract(CONTRACT_FILE),range_id,selection)

def render(contract: dict[str, Any], view: str, market: str | None, timeframe: str | None, range_id: str | None) -> html.Div:
    del market,timeframe
    if view == "reference":
        return screen_page(_volatility_stylesheet(),screen_header(contract),reference_gallery(REFERENCE_IMAGES))
    if view == "analysis":
        return screen_page(_volatility_stylesheet(),dcc.Store(id=SELECTION_STORE_ID,storage_type="local"),html.Div(id=ANALYSIS_CONTENT_ID,children=_analysis_screen(contract,range_id,None)))
    charts=_safe_dict(contract.get("charts"))
    return screen_page(
        _volatility_stylesheet(),dcc.Store(id=SELECTION_STORE_ID,storage_type="local"),screen_header(contract),kpi_grid(contract.get("kpis")),
        html.Div(className="vol-native-main",children=[
            html.Div(className="vol-native-grid",children=[
                html.Div(className="vol-native-card",children=[dcc.Graph(figure=_screen_a_figure(contract,"realized_volatility",range_id),config={"displaylogo":False,"responsive":True})]),
                html.Div(className="vol-native-card",children=[dcc.Graph(figure=_screen_a_figure(contract,"implied_volatility",range_id),config={"displaylogo":False,"responsive":True})]),
                html.Div(className="vol-native-card",children=[dcc.Graph(figure=_screen_a_figure(contract,"implied_vs_realized",range_id),config={"displaylogo":False,"responsive":True})]),
                html.Div(className="vol-native-card",children=[dcc.Graph(figure=_screen_a_figure(contract,"term_structure",range_id),config={"displaylogo":False,"responsive":True})]),
            ]),
            _selection_panel(),
        ]),
        html.Div(id=ANALYSIS_CONTENT_ID,style={"display":"none"}),
    )
