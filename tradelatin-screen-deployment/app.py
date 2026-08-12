from __future__ import annotations

import os
from types import ModuleType
from typing import Any

from dash import Dash, Input, Output, State, ctx, dcc, html, no_update

from screen_core.contract_loader import active_badges, contract_revision, load_contract, screen_metadata, selector_spec
from screen_core.formatting import format_timestamp
from screens import (
    cvd_volume_orderflow,
    etf_exchange_flows,
    liquidity_microstructure,
    long_short_liquidations,
    on_chain_miners,
    open_interest_and_funding,
    prices,
    volatility_market_regimes,
)

SCREENS: tuple[ModuleType, ...] = (
    prices,
    cvd_volume_orderflow,
    open_interest_and_funding,
    etf_exchange_flows,
    on_chain_miners,
    volatility_market_regimes,
    long_short_liquidations,
    liquidity_microstructure,
)
SCREEN_BY_ROUTE = {module.ROUTE: module for module in SCREENS}
DEFAULT_SCREEN = prices

# Families whose data should refresh automatically according to the selected
# timeframe. All other families use the manual RELOAD button.
AUTO_REFRESH_ROUTES = {
    prices.ROUTE,
    cvd_volume_orderflow.ROUTE,
    open_interest_and_funding.ROUTE,
}

# Temporal selector policy is explicit by family. We do not infer temporal
# controls from arbitrary contract fields because snapshot-oriented families
# may contain historical context without exposing a user-facing selector.
TIMEFRAME_SELECTOR_ROUTES = {
    prices.ROUTE,
    cvd_volume_orderflow.ROUTE,
    open_interest_and_funding.ROUTE,
}
RANGE_SELECTOR_ROUTES = {
    etf_exchange_flows.ROUTE,
    on_chain_miners.ROUTE,
    volatility_market_regimes.ROUTE,
}
NO_TEMPORAL_SELECTOR_ROUTES = {
    long_short_liquidations.ROUTE,
    liquidity_microstructure.ROUTE,
}

TIMEFRAME_REFRESH_MS = {
    '1m': 60_000,
    '5m': 300_000,
    '15m': 900_000,
    '1h': 3_600_000,
    '4h': 14_400_000,
    '1d': 86_400_000,
}
DEFAULT_REFRESH_MS = 60_000


def _normalized_path(pathname: str | None) -> str:
    if not pathname or pathname == '/':
        return DEFAULT_SCREEN.ROUTE
    return pathname.rstrip('/') or '/'


def resolve_route(pathname: str | None) -> tuple[ModuleType, str]:
    """Resolve both family and view directly from the URL.

    Canonical routes:
      /family            -> Screen A
      /family/analysis   -> Screen B
      /family/reference  -> reference gallery
    """
    normalized = _normalized_path(pathname)

    for module in SCREENS:
        if normalized == module.ROUTE:
            return module, 'main'
        if module.HAS_ANALYSIS and normalized == f'{module.ROUTE}/analysis':
            return module, 'analysis'
        if normalized == f'{module.ROUTE}/reference':
            return module, 'reference'

    return DEFAULT_SCREEN, 'main'


def get_screen(pathname: str | None) -> ModuleType:
    return resolve_route(pathname)[0]


def get_route_view(pathname: str | None) -> str:
    return resolve_route(pathname)[1]


def selector_box(label: str, component_id: str) -> html.Div:
    return html.Div(
        id=f'{component_id}-box',
        className='control-group',
        children=[
            html.Label(label, className='control-label'),
            dcc.Dropdown(
                id=component_id,
                options=[],
                value=None,
                clearable=False,
                searchable=False,
                className='dark-dropdown',
            ),
        ],
    )


def selector_buttons(label: str, component_id: str) -> html.Div:
    """Compact temporal selector rendered directly in the family header."""
    return html.Div(
        id=f'{component_id}-box',
        className='header-control-group',
        children=[
            html.Span(label, className='header-control-label'),
            dcc.RadioItems(
                id=component_id,
                options=[],
                value=None,
                className='header-radio-selector',
                inline=True,
            ),
        ],
    )


def _header_status(value: Any) -> str:
    status = str(value or 'available').lower()
    if status in {'ok', 'available', 'active', 'connected', 'normal', 'positive', 'bullish', 'buying', 'expanding'}:
        return 'ok'
    if status in {'partial', 'warning', 'degraded', 'synthetic', 'demo', 'estimated', 'mixed', 'neutral'}:
        return 'warning'
    if status in {'unavailable', 'error', 'critical', 'negative', 'bearish', 'selling', 'disconnected'}:
        return 'danger'
    return 'neutral'


def _header_badges(contract: dict[str, Any]) -> list[Any]:
    meta = screen_metadata(contract)
    operational = contract.get('operational_status') if isinstance(contract.get('operational_status'), dict) else {}
    quality = contract.get('quality') if isinstance(contract.get('quality'), dict) else {}
    quality_status = operational.get('quality_status') or operational.get('status') or quality.get('status') or 'unknown'

    nodes: list[Any] = [
        html.Span(item['text'], className=f"status-badge status-{_header_status(item.get('status'))}")
        for item in active_badges(contract)
    ]
    if meta.get('data_mode'):
        nodes.append(html.Span(str(meta['data_mode']).upper(), className='status-badge status-warning'))
    nodes.append(
        html.Span(
            str(quality_status).upper(),
            className=f"status-badge status-{_header_status(quality_status)}",
        )
    )
    return nodes


def family_nav_item(module: ModuleType) -> html.Div:
    """Family name opens in current tab; arrow opens the same route in a new tab."""
    return html.Div(
        className='family-nav-item',
        style={
            'display': 'grid',
            'gridTemplateColumns': 'minmax(0, 1fr) 20px',
            'alignItems': 'center',
            'minWidth': '96px',
            'gap': '2px',
        },
        children=[
            dcc.Link(
                module.LABEL,
                href=module.ROUTE,
                className='nav-link',
                style={
                    'display': 'block',
                    'minWidth': '0',
                    'textAlign': 'center',
                    'whiteSpace': 'nowrap',
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                    'textDecoration': 'none',
                },
            ),
            html.A(
                '↗',
                href=module.ROUTE,
                target='_blank',
                rel='noopener noreferrer',
                title=f'Abrir {module.LABEL} en una nueva pestaña',
                className='nav-link nav-external-link',
                style={
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'center',
                    'textDecoration': 'none',
                    'fontSize': '10px',
                    'opacity': '.70',
                },
            ),
        ],
    )


app = Dash(
    __name__,
    suppress_callback_exceptions=True,
    title='TradELATIN Screen Deployment',
    update_title='TradELATIN · Loading...',
)
server = app.server

app.layout = html.Div(
    className='app-shell',
    children=[
        dcc.Location(id='url', refresh=False),
        dcc.Interval(
            id='auto-refresh',
            interval=DEFAULT_REFRESH_MS,
            n_intervals=0,
            disabled=True,
        ),
        # Compatibility signal consumed by the existing screen callbacks.
        # It is never shown to the user; both auto and manual refresh increment it.
        html.Button('', id='reload-json', n_clicks=0, style={'display': 'none'}),
        html.Header(
            className='topbar',
            children=[
                html.Div(
                    className='brand-block',
                    children=[
                        html.Div('T', className='brand-mark'),
                        html.Div([
                            html.Strong('TradELATIN', className='brand-name'),
                            html.Span('VR1', className='brand-version'),
                        ]),
                    ],
                ),
                html.Nav(
                    [family_nav_item(module) for module in SCREENS],
                    className='main-nav',
                    style={
                        'flex': '1 1 auto',
                        'display': 'grid',
                        'gridTemplateColumns': 'repeat(8, minmax(96px, 1fr))',
                        'alignItems': 'center',
                        'gap': '3px',
                        'minWidth': '0',
                        'overflowX': 'auto',
                        'padding': '0 14px',
                    },
                ),
                html.Div(
                    [html.Span('DEMO', className='status-badge status-warning')],
                    className='topbar-status',
                    style={'flex': '0 0 auto'},
                ),
            ],
        ),
        # Hidden compatibility state. VIEW/MARKET stay mounted, while the
        # temporal controls are rendered in the visible compact family header below.
        html.Div(
            [
                selector_box('VIEW', 'screen-view'),
                selector_box('MARKET', 'market-selector'),
                html.Div(id='contract-revision', className='revision-text'),
            ],
            style={'display': 'none'},
        ),
        html.Div(
            className='screen-header-shell',
            children=[
                html.Div(
                    className='compact-family-header',
                    children=[
                        html.Div(
                            className='compact-family-identity',
                            children=[
                                html.Div(id='app-screen-eyebrow', className='compact-family-eyebrow'),
                                html.H1(id='app-screen-title', className='compact-family-title'),
                                html.Div(id='app-screen-subtitle', style={'display': 'none'}),
                            ],
                        ),
                        html.Div(
                            className='compact-family-controls',
                            children=[
                                selector_buttons('TIMEFRAME', 'timeframe-selector'),
                                # Range-backed families keep their contractual selector
                                # internally, but use the same compact TIMEFRAME label.
                                selector_buttons('TIMEFRAME', 'range-selector'),
                                html.Button(
                                    '↻ RELOAD',
                                    id='manual-reload',
                                    n_clicks=0,
                                    className='reload-button header-reload-button',
                                ),
                            ],
                        ),
                        html.Div(
                            className='compact-family-meta',
                            children=[
                                html.Div(id='app-badge-row', className='badge-row'),
                                html.Div(
                                    [
                                        html.Span('DATA AS OF', className='meta-label'),
                                        html.Span(id='app-data-as-of', className='meta-value'),
                                    ],
                                    className='meta-block',
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        html.Main(id='page-content', className='page-content'),
        html.Footer(
            className='app-footer',
            children=[
                html.Span('DATA SOURCE STATUS'),
                html.Span('JSON contracts loaded from data/contracts'),
                html.Span('HMI computes no market indicators'),
                html.Span('TradELATIN VR1 · Screen Deployment'),
            ],
        ),
    ],
)


@app.callback(
    Output('screen-view', 'options'),
    Output('screen-view', 'value'),
    Output('market-selector', 'options'),
    Output('market-selector', 'value'),
    Output('market-selector-box', 'style'),
    Output('timeframe-selector', 'options'),
    Output('timeframe-selector', 'value'),
    Output('timeframe-selector-box', 'style'),
    Output('range-selector', 'options'),
    Output('range-selector', 'value'),
    Output('range-selector-box', 'style'),
    Output('contract-revision', 'children'),
    Input('url', 'pathname'),
    Input('reload-json', 'n_clicks'),
    State('screen-view', 'value'),
    State('market-selector', 'value'),
    State('timeframe-selector', 'value'),
    State('range-selector', 'value'),
)
def sync_controls(
    pathname: str | None,
    _reload_clicks: int,
    _current_view: str | None,
    current_market: str | None,
    current_timeframe: str | None,
    current_range: str | None,
) -> tuple[Any, ...]:
    module, route_view = resolve_route(pathname)
    contract = load_contract(module.CONTRACT_FILE)

    view_options = [{'label': 'PANTALLA A', 'value': 'main'}]
    if module.HAS_ANALYSIS:
        view_options.append({'label': 'PANTALLA B', 'value': 'analysis'})
    view_options.append({'label': 'REFERENCIA', 'value': 'reference'})

    # URL is the canonical navigation state. screen-view remains only for
    # backwards compatibility with old per-screen callbacks.
    selected_view = route_view

    market_options, market_default = selector_spec(contract, 'market')

    # Temporal UI is route-governed, not inferred. This prevents historical
    # context stored inside Liquidity/Liquidations contracts from accidentally
    # surfacing a TIMEFRAME or RANGE selector in the toolbar.
    if module.ROUTE in TIMEFRAME_SELECTOR_ROUTES:
        timeframe_options, timeframe_default = selector_spec(contract, 'timeframe')
        range_options, range_default = [], None
    elif module.ROUTE in RANGE_SELECTOR_ROUTES:
        timeframe_options, timeframe_default = [], None
        range_options, range_default = selector_spec(contract, 'range')
    else:
        timeframe_options, timeframe_default = [], None
        range_options, range_default = [], None

    market_values = {item['value'] for item in market_options}
    timeframe_values = {item['value'] for item in timeframe_options}
    range_values = {item['value'] for item in range_options}

    selected_market = current_market if current_market in market_values else market_default
    selected_timeframe = current_timeframe if current_timeframe in timeframe_values else timeframe_default
    selected_range = current_range if current_range in range_values else range_default

    shown = {'display': 'flex'}
    hidden = {'display': 'none'}
    revision = contract_revision(module.CONTRACT_FILE)

    return (
        view_options,
        selected_view,
        market_options,
        selected_market,
        shown if market_options else hidden,
        timeframe_options,
        selected_timeframe,
        shown if timeframe_options else hidden,
        range_options,
        selected_range,
        shown if range_options else hidden,
        f'{module.CONTRACT_FILE} · {revision}',
    )


@app.callback(
    Output('app-screen-eyebrow', 'children'),
    Output('app-screen-title', 'children'),
    Output('app-screen-subtitle', 'children'),
    Output('app-badge-row', 'children'),
    Output('app-data-as-of', 'children'),
    Input('url', 'pathname'),
    Input('reload-json', 'n_clicks'),
)
def sync_compact_header(pathname: str | None, _reload_clicks: int) -> tuple[Any, ...]:
    module, route_view = resolve_route(pathname)
    contract = load_contract(module.CONTRACT_FILE)
    meta = screen_metadata(contract)

    if route_view == 'analysis':
        eyebrow = 'ANÁLISIS TÉCNICO FUNDAMENTAL'
    elif route_view == 'reference':
        eyebrow = 'REFERENCIA CONTRACTUAL'
    else:
        eyebrow = 'TRAD ELATIN TRADING TOOL'

    title = meta.get('title') or module.LABEL
    subtitle = meta.get('subtitle') or str(meta.get('family') or '')
    return (
        eyebrow,
        title,
        subtitle,
        _header_badges(contract),
        format_timestamp(meta.get('data_as_of')),
    )


@app.callback(
    Output('manual-reload', 'style'),
    Output('auto-refresh', 'disabled'),
    Output('auto-refresh', 'interval'),
    Input('url', 'pathname'),
    Input('timeframe-selector', 'value'),
)
def sync_refresh_policy(
    pathname: str | None,
    timeframe: str | None,
) -> tuple[dict[str, Any], bool, int]:
    module = get_screen(pathname)

    reload_style = {'display': 'inline-flex'}

    if module.ROUTE in AUTO_REFRESH_ROUTES:
        interval = TIMEFRAME_REFRESH_MS.get(timeframe or '', DEFAULT_REFRESH_MS)
        return reload_style, False, interval

    return reload_style, True, DEFAULT_REFRESH_MS


@app.callback(
    Output('reload-json', 'n_clicks'),
    Input('auto-refresh', 'n_intervals'),
    Input('manual-reload', 'n_clicks'),
    State('reload-json', 'n_clicks'),
    prevent_initial_call=True,
)
def dispatch_refresh(
    _auto_ticks: int | None,
    _manual_clicks: int | None,
    current_signal: int | None,
) -> Any:
    if ctx.triggered_id not in {'auto-refresh', 'manual-reload'}:
        return no_update
    return int(current_signal or 0) + 1


@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'),
    Input('screen-view', 'value'),
    Input('market-selector', 'value'),
    Input('timeframe-selector', 'value'),
    Input('range-selector', 'value'),
    Input('reload-json', 'n_clicks'),
)
def render_screen(
    pathname: str | None,
    _compat_view: str | None,
    market: str | None,
    timeframe: str | None,
    range_id: str | None,
    _reload_clicks: int,
) -> html.Div:
    module, route_view = resolve_route(pathname)
    try:
        contract = load_contract(module.CONTRACT_FILE)
        return module.render(contract, route_view, market, timeframe, range_id)
    except Exception as exc:
        return html.Div(
            className='fatal-contract-error',
            children=[
                html.H2('CONTRACT LOAD ERROR'),
                html.Div(module.CONTRACT_FILE, className='fatal-file'),
                html.Pre(str(exc)),
                html.P('Correct the JSON and press RELOAD. No fallback data is fabricated.'),
            ],
        )


if __name__ == '__main__':
    host = os.getenv('TRADELATIN_HOST', '127.0.0.1')
    port = int(os.getenv('TRADELATIN_PORT', '8050'))
    debug = os.getenv('TRADELATIN_DEBUG', '1').lower() not in {'0', 'false', 'no'}
    app.run(host=host, port=port, debug=debug)
