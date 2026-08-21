from __future__ import annotations

import os
import time
from types import ModuleType
from typing import Any

from dash import Dash, Input, Output, State, ctx, dcc, html, no_update

from screen_core.contract_loader import active_badges, contract_revision, load_contract, screen_metadata, selector_spec
from screen_core.formatting import format_timestamp
from screen_core.refresh import FAMILY_AUTO_REFRESH_MS, refresh_timeout_seconds, request_family_refresh_async
from screen_core.i18n import (
    locale_context,
    locale_from_search,
    localize_component_tree,
    localize_options,
    tr,
)
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

# Processing cadence is family-owned and independent from chart timeframe.
FAMILY_KEY_BY_ROUTE = {
    prices.ROUTE: "prices",
    cvd_volume_orderflow.ROUTE: "cvd",
    open_interest_and_funding.ROUTE: "open_interest",
    etf_exchange_flows.ROUTE: "etf",
    on_chain_miners.ROUTE: "on_chain",
    volatility_market_regimes.ROUTE: "volatility",
    long_short_liquidations.ROUTE: "liquidations",
    liquidity_microstructure.ROUTE: "liquidity",
}
AUTO_REFRESH_ROUTES = {
    route for route, family in FAMILY_KEY_BY_ROUTE.items()
    if family in FAMILY_AUTO_REFRESH_MS
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

DEFAULT_REFRESH_MS = 60_000
REFRESH_POLL_MS = 1_000

TRACE_I18N = os.getenv("TRADELATIN_TRACE_I18N", "0").lower() in {"1", "true", "yes"}

def _trace_i18n(event: str, *, locale: str, pathname: str | None = None, search: str | None = None) -> None:
    if TRACE_I18N:
        print(f"[I18N] event={event} locale={locale} pathname={pathname or '-'} search={search or '-'}", flush=True)



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
            html.Label(label, id=f'{component_id}-label', className='control-label'),
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
            html.Span(label, id=f'{component_id}-label', className='header-control-label'),
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


def family_nav_item(module: ModuleType, locale: str = "en") -> html.Div:
    """Navigation item preserving the explicit URL locale."""
    label = tr(module.LABEL, locale)
    route = f"{module.ROUTE}?lang={locale}"
    open_title = (
        f"Abrir {label} en una nueva pestaña"
        if locale == "es"
        else f"Open {label} in a new tab"
    )
    return html.Div(
        className="family-nav-item",
        style={
            "display": "grid",
            "gridTemplateColumns": "minmax(0, 1fr) 20px",
            "alignItems": "center",
            "minWidth": "96px",
            "gap": "2px",
        },
        children=[
            dcc.Link(
                label,
                href=route,
                refresh=False,
                className="nav-link",
                style={
                    "display": "block",
                    "minWidth": "0",
                    "textAlign": "center",
                    "whiteSpace": "nowrap",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                    "textDecoration": "none",
                },
            ),
            html.A(
                "↗",
                href=route,
                target="_blank",
                rel="noopener noreferrer",
                title=open_title,
                className="nav-link nav-external-link",
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "textDecoration": "none",
                    "fontSize": "10px",
                    "opacity": ".70",
                },
            ),
        ],
    )


app = Dash(
    __name__,
    suppress_callback_exceptions=True,
    title="TradELATIN Screen Deployment",
    update_title=None,
    # Never load legacy DOM translators. Language is pure Dash state.
    assets_ignore=r"^i18n_runtime\.js$",
)
server = app.server


def _language_switch() -> html.Div:
    return html.Div(
        className="language-switch",
        title="Language / Idioma",
        children=[
            html.Span("LANGUAGE", id="language-switch-label", className="language-switch-label"),
            html.Button("EN", id="lang-en", n_clicks=0, className="language-option language-option-active"),
            html.Button("ES", id="lang-es", n_clicks=0, className="language-option"),
        ],
    )


def serve_layout() -> html.Div:
    return html.Div(
        className='app-shell',
                children=[
            dcc.Location(id='url', refresh=False),
            dcc.Interval(
                id='auto-refresh',
                interval=DEFAULT_REFRESH_MS,
                n_intervals=0,
                disabled=True,
            ),
            dcc.Interval(
                id='refresh-poll',
                interval=REFRESH_POLL_MS,
                n_intervals=0,
                disabled=True,
            ),
            dcc.Store(id='refresh-state', storage_type='memory', data={'status': 'idle'}),
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
                        [family_nav_item(module, 'en') for module in SCREENS],
                        id='main-nav',
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
                        [
                            _language_switch(),
                            html.Span('DEMO', className='status-badge status-warning'),
                        ],
                        className='topbar-status language-topbar-group',
                        style={'flex': '0 0 auto'},
                    ),
                ],
            ),
            html.Div(
                [
                    selector_box('VIEW', 'screen-view'),
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
                                    selector_buttons('MARKET', 'market-selector'),
                                    selector_buttons('TIMEFRAME', 'timeframe-selector'),
                                    selector_buttons('TIMEFRAME', 'range-selector'),
                                    html.Button(
                                        "↻ RELOAD",
                                        id='manual-reload',
                                        n_clicks=0,
                                        className='reload-button header-reload-button',
                                    ),
                                ],
                            ),
                            html.Div(
                                className='compact-family-meta',
                                children=[
                                    html.Span(id='refresh-state-badge', className='status-badge status-warning', style={'display': 'none'}),
                                    html.Div(id='app-badge-row', className='badge-row'),
                                    html.Div(
                                        [
                                            html.Span('DATA AS OF', id='data-as-of-label', className='meta-label'),
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
                    html.Span('DATA SOURCE STATUS', id='footer-source-status'),
                    html.Span('JSON contracts loaded from data/contracts', id='footer-contracts'),
                    html.Span('HMI computes no market indicators', id='footer-hmi'),
                    html.Span('TradELATIN VR1 · Screen Deployment', id='footer-deployment'),
                ],
            ),
        ],
    )


app.layout = serve_layout()


@app.callback(
    Output("url", "search"),
    Input("lang-en", "n_clicks"),
    Input("lang-es", "n_clicks"),
    State("url", "search"),
    prevent_initial_call=True,
)
def switch_language(_en_clicks: int | None, _es_clicks: int | None, current_search: str | None) -> Any:
    """Change only the explicit URL language state. No reload, cookie or JS mutation."""
    if ctx.triggered_id == "lang-en":
        desired = "en"
    elif ctx.triggered_id == "lang-es":
        desired = "es"
    else:
        return no_update

    if locale_from_search(current_search) == desired:
        return no_update
    return f"?lang={desired}"


@app.callback(
    Output("main-nav", "children"),
    Output("language-switch-label", "children"),
    Output("lang-en", "className"),
    Output("lang-es", "className"),
    Output("screen-view-label", "children"),
    Output("market-selector-label", "children"),
    Output("timeframe-selector-label", "children"),
    Output("range-selector-label", "children"),
    Output("manual-reload", "children"),
    Output("data-as-of-label", "children"),
    Output("footer-source-status", "children"),
    Output("footer-contracts", "children"),
    Output("footer-hmi", "children"),
    Output("footer-deployment", "children"),
    Input("url", "search"),
)
def sync_locale_shell(search: str | None) -> tuple[Any, ...]:
    locale = locale_from_search(search)
    _trace_i18n("shell", locale=locale, search=search)
    active = "language-option language-option-active"
    inactive = "language-option"
    return (
        [family_nav_item(module, locale) for module in SCREENS],
        tr("LANGUAGE", locale),
        active if locale == "en" else inactive,
        active if locale == "es" else inactive,
        tr("VIEW", locale),
        tr("MARKET", locale),
        tr("TIMEFRAME", locale),
        tr("TIMEFRAME", locale),
        f"↻ {tr('RELOAD', locale)}",
        tr("DATA AS OF", locale),
        tr("DATA SOURCE STATUS", locale),
        tr("JSON contracts loaded from data/contracts", locale),
        tr("HMI computes no market indicators", locale),
        tr("TradELATIN VR1 · Screen Deployment", locale),
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
    Input('url', 'search'),
    Input('reload-json', 'n_clicks'),
    State('screen-view', 'value'),
    State('market-selector', 'value'),
    State('timeframe-selector', 'value'),
    State('range-selector', 'value'),
)
def sync_controls(
    pathname: str | None,
    search: str | None,
    _reload_clicks: int,
    _current_view: str | None,
    current_market: str | None,
    current_timeframe: str | None,
    current_range: str | None,
) -> tuple[Any, ...]:
    locale = locale_from_search(search)
    module, route_view = resolve_route(pathname)
    contract = load_contract(module.CONTRACT_FILE)

    view_options = [{'label': tr('SCREEN A', locale), 'value': 'main'}]
    if module.HAS_ANALYSIS:
        view_options.append({'label': tr('SCREEN B', locale), 'value': 'analysis'})
    view_options.append({'label': tr('REFERENCE', locale), 'value': 'reference'})

    # URL is the canonical navigation state. screen-view remains only for
    # backwards compatibility with old per-screen callbacks.
    selected_view = route_view

    market_options, market_default = selector_spec(contract, 'market')
    selectors = contract.get('selectors') if isinstance(contract.get('selectors'), dict) else {}
    market_config = selectors.get('market') if isinstance(selectors.get('market'), dict) else {}
    market_visible = bool(market_options) and (
        market_config.get('visible') is True
        or (module.ROUTE == liquidity_microstructure.ROUTE and market_config.get('visible') is not False)
    )

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

    market_options = localize_options(market_options, locale)
    timeframe_options = localize_options(timeframe_options, locale)
    range_options = localize_options(range_options, locale)

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
        shown if market_visible else hidden,
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
    Input('url', 'search'),
    Input('reload-json', 'n_clicks'),
)
def sync_compact_header(pathname: str | None, search: str | None, _reload_clicks: int) -> tuple[Any, ...]:
    locale = locale_from_search(search)
    module, route_view = resolve_route(pathname)
    contract = load_contract(module.CONTRACT_FILE)
    meta = screen_metadata(contract)

    if route_view == 'analysis':
        eyebrow = tr('FUNDAMENTAL TECHNICAL ANALYSIS', locale)
    elif route_view == 'reference':
        eyebrow = tr('CONTRACT REFERENCE', locale)
    else:
        eyebrow = tr('TRAD ELATIN TRADING TOOL', locale)

    title = tr(meta.get('title') or module.LABEL, locale)
    subtitle = tr(meta.get('subtitle') or str(meta.get('family') or ''), locale)
    return (
        eyebrow,
        title,
        subtitle,
        localize_component_tree(_header_badges(contract), locale),
        format_timestamp(meta.get('data_as_of')),
    )


@app.callback(
    Output('manual-reload', 'style'),
    Output('auto-refresh', 'disabled'),
    Output('auto-refresh', 'interval'),
    Input('url', 'pathname'),
)
def sync_refresh_policy(pathname: str | None) -> tuple[dict[str, Any], bool, int]:
    module = get_screen(pathname)
    reload_style = {'display': 'inline-flex'}
    family = FAMILY_KEY_BY_ROUTE.get(module.ROUTE)
    interval = FAMILY_AUTO_REFRESH_MS.get(str(family or ''))
    if interval is not None:
        return reload_style, False, int(interval)
    return reload_style, True, DEFAULT_REFRESH_MS


@app.callback(
    Output('reload-json', 'n_clicks'),
    Output('refresh-state', 'data'),
    Output('refresh-poll', 'disabled'),
    Input('auto-refresh', 'n_intervals'),
    Input('manual-reload', 'n_clicks'),
    Input('refresh-poll', 'n_intervals'),
    State('url', 'pathname'),
    State('reload-json', 'n_clicks'),
    State('refresh-state', 'data'),
    prevent_initial_call=True,
)
def orchestrate_family_refresh(
    _auto_ticks: int | None,
    _manual_clicks: int | None,
    _poll_ticks: int | None,
    pathname: str | None,
    current_signal: int | None,
    refresh_state: dict[str, Any] | None,
) -> tuple[Any, dict[str, Any], bool]:
    module = get_screen(pathname)
    family = FAMILY_KEY_BY_ROUTE.get(module.ROUTE, module.ROUTE.strip('/') or 'prices')
    state = refresh_state if isinstance(refresh_state, dict) else {'status': 'idle'}
    trigger = ctx.triggered_id

    if trigger in {'auto-refresh', 'manual-reload'}:
        if state.get('status') == 'updating':
            return no_update, state, False
        reason = 'manual' if trigger == 'manual-reload' else 'auto'
        baseline = contract_revision(module.CONTRACT_FILE)
        dispatch = request_family_refresh_async(
            family=family,
            reason=reason,
            contract_file=module.CONTRACT_FILE,
        )
        if not dispatch.configured:
            # Standalone HMI mode: no Processing refresh endpoint is configured.
            # Re-read only the currently visible family contract.
            return int(current_signal or 0) + 1, {'status': 'idle'}, True
        next_state = {
            'status': 'updating',
            'family': family,
            'route': module.ROUTE,
            'contract_file': module.CONTRACT_FILE,
            'baseline_revision': baseline,
            'started_at': time.time(),
            'reason': reason,
        }
        return no_update, next_state, False

    if trigger == 'refresh-poll':
        if state.get('status') != 'updating':
            return no_update, state, True
        contract_file = str(state.get('contract_file') or module.CONTRACT_FILE)
        baseline = str(state.get('baseline_revision') or '')
        current_revision = contract_revision(contract_file)
        if current_revision != baseline and current_revision != 'missing':
            try:
                # Only expose the new state after the producer has published a
                # complete, parseable JSON.  Until then, the last valid screen
                # remains visible.
                load_contract(contract_file)
            except Exception:
                return no_update, state, False
            completed = {
                'status': 'idle',
                'family': state.get('family'),
                'completed_at': time.time(),
            }
            current_family = FAMILY_KEY_BY_ROUTE.get(module.ROUTE)
            if current_family == state.get('family'):
                return int(current_signal or 0) + 1, completed, True
            return no_update, completed, True

        try:
            elapsed = time.time() - float(state.get('started_at'))
        except (TypeError, ValueError):
            elapsed = 0.0
        if elapsed >= refresh_timeout_seconds():
            timeout_state = {**state, 'status': 'timeout', 'finished_at': time.time()}
            return no_update, timeout_state, True
        return no_update, state, False

    return no_update, state, True


@app.callback(
    Output('refresh-state-badge', 'children'),
    Output('refresh-state-badge', 'className'),
    Output('refresh-state-badge', 'style'),
    Input('refresh-state', 'data'),
    Input('url', 'pathname'),
    Input('url', 'search'),
)
def render_refresh_status(
    refresh_state: dict[str, Any] | None,
    pathname: str | None,
    search: str | None,
) -> tuple[str, str, dict[str, str]]:
    state = refresh_state if isinstance(refresh_state, dict) else {}
    module = get_screen(pathname)
    current_family = FAMILY_KEY_BY_ROUTE.get(module.ROUTE)
    if state.get('family') not in {None, current_family}:
        return '', 'status-badge status-warning', {'display': 'none'}
    locale = locale_from_search(search)
    if state.get('status') == 'updating':
        return tr('UPDATING', locale), 'status-badge status-warning', {'display': 'inline-flex'}
    if state.get('status') == 'timeout':
        return tr('REFRESH TIMEOUT', locale), 'status-badge status-danger', {'display': 'inline-flex'}
    return '', 'status-badge status-warning', {'display': 'none'}


@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'),
    Input('url', 'search'),
    Input('market-selector', 'value'),
    Input('timeframe-selector', 'value'),
    Input('range-selector', 'value'),
    Input('reload-json', 'n_clicks'),
)
def render_screen(
    pathname: str | None,
    search: str | None,
    market: str | None,
    timeframe: str | None,
    range_id: str | None,
    _reload_clicks: int,
) -> html.Div:
    locale = locale_from_search(search)
    _trace_i18n("render", locale=locale, pathname=pathname, search=search)
    module, route_view = resolve_route(pathname)
    try:
        contract = load_contract(module.CONTRACT_FILE)
        with locale_context(locale):
            rendered = module.render(contract, route_view, market, timeframe, range_id)
            return localize_component_tree(rendered, locale)
    except Exception as exc:
        return html.Div(
            className='fatal-contract-error',
            children=[
                html.H2(tr('CONTRACT LOAD ERROR', locale)),
                html.Div(module.CONTRACT_FILE, className='fatal-file'),
                html.Pre(str(exc)),
                html.P(tr('Correct the JSON and press RELOAD. No fallback data is fabricated.', locale)),
            ],
        )


if __name__ == '__main__':
    host = os.getenv('TRADELATIN_HOST', '127.0.0.1')
    port = int(os.getenv('TRADELATIN_PORT', '8002'))
    debug = os.getenv('TRADELATIN_DEBUG', '0').lower() not in {'0', 'false', 'no'}
    app.run(host=host, port=port, debug=debug, use_reloader=False)
