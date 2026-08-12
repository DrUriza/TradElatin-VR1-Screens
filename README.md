# TradELATIN Screen Deployment

Dash + Plotly sandbox for reconstructing the eight TradELATIN VR1 screen families directly from their screen-contract JSON files.

## First run — 3 steps

1. Open PowerShell in this folder and run `py -3.11 -m venv .venv` followed by `.\.venv\Scripts\Activate.ps1`.
2. Run `pip install -r requirements.txt`.
3. Run `python app.py` and open `http://127.0.0.1:8050`.

You may also run `./run.ps1` on Windows.

## Eight family modules

- `screens/prices.py`
- `screens/cvd_volume_orderflow.py`
- `screens/open_interest_and_funding.py`
- `screens/etf_exchange_flows.py`
- `screens/on_chain_miners.py`
- `screens/volatility_market_regimes.py`
- `screens/long_short_liquidations.py`
- `screens/liquidity_microstructure.py`

Each family module defines its contract filename, route, reference images, Pantalla A layout, and Pantalla B availability.

## JSON workflow

Edit or replace the corresponding file under `data/contracts/`, then press **RELOAD JSON**. The application reloads only the active family. Invalid JSON is shown as a contract error and no fallback values are fabricated.

## Views

- **PANTALLA A:** operational family dashboard.
- **PANTALLA B:** technical/fundamental view when contractually applicable.
- **REFERENCIA:** the supplied contractual PNG images for side-by-side reconstruction.

## Repository structure

```text
tradelatin-screen-deployment/
├── app.py
├── assets/
│   ├── tradelatin.css
│   └── reference/
├── data/contracts/
├── screen_core/
│   ├── components.py
│   ├── contract_loader.py
│   ├── figures.py
│   └── formatting.py
├── screens/                  # exactly eight family .py modules
├── tests/
└── docs/CONTRACT_RULES.md
```

The versions in `requirements.txt` are Dash 4.4.0 and Plotly 6.9.0. Python 3.11 or newer is recommended.
