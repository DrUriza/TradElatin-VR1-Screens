# TradELATIN VR1 Screens — Final HMI V7

This package is a complete copy/paste repository baseline for the final Screens/HMI state before popup-content refinement and Processing E2E integration.

## Included final structural decisions

- One Dash application, one process, one canonical entry point: `python main.py`.
- EN/ES language state is explicit in the URL: `?lang=en` / `?lang=es`.
- No language cookies, localStorage authority, MutationObserver, or reload loop.
- Prices Screen A remains large (590 px main chart/panel).
- Open Interest Screen A remains large (590 px card/panel, 556 px graph).
- Volatility Screen B uses a 3x2 analysis grid plus a 286 px regime-summary column.
- Liquidations Screen A contains the four native views plus a Screen-B selector; its target summary is no longer rendered on Screen A.
- Liquidations Screen B contains selectable native analysis cards plus the `LIQUIDITY TARGET SUMMARY` side panel.
- Liquidity keeps independent Spot/Perpetual market views and separate Order Book, Whale Orders, Executed Operations and Large Trades.
- Contextual-help popup timing/shape/positioning is preserved; content refinement remains a later phase.

## Latest HMI-only corrections

### Prices

- Fibonacci/Support/Resistance values remain contract-owned.
- Labels are rendered as explicit annotations inside the chart domain to avoid y-axis collisions.
- Support/Resistance labels respect EN/ES.

### Open Interest

- Exact crossover events are rendered only when their exact timestamp is inside the visible OI data window.
- The HMI does not recalculate or alter event timestamps/values.

### Contract filename resolution

Screens still requests canonical contract IDs internally, but runtime Processing may publish concise filenames:

- `prices.json`
- `cvd.json`
- `open_interest.json`
- `etf.json`
- `miners.json`
- `volatility.json`
- `liquidations.json`
- `liquidity.json`

Concise runtime aliases take priority over bundled canonical golden fixtures when both exist. This allows Processing runtime output to override demo/golden fixtures without renaming them.

## Validation performed in this package build

- `py_compile`: PASS for app, main, screen_core, screens and tests.
- 8/8 bundled JSON contracts parse successfully.
- Contract alias resolver assertions: PASS.

Full `pytest` must be run in the user's project `.venv` because Dash is not installed in the artifact build container.
