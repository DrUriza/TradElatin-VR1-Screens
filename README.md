# TradELATIN VR1 Screens

Bitcoin market-intelligence HMI for eight analysis families:

1. Prices
2. CVD & Order Flow
3. Open Interest & Funding
4. ETF & Exchange Flows
5. On-Chain & Miners
6. Volatility & Market Regimes
7. Liquidations & Positioning
8. Liquidity Microstructure

## Run

Create/activate the virtual environment and start the single canonical entry point:

```powershell
.\.venv\Scripts\Activate.ps1
python main.py
```

Then open:

```text
http://127.0.0.1:8002/prices?lang=en
```

The same Dash process supports **English and Spanish**. Use `EN | ES` in the top bar; language is stored only in the URL (`?lang=en` / `?lang=es`).

There are no separate English/Spanish servers, cookies, localStorage translators or DOM mutation observers.

## Architecture

```text
Input
  -> Processing
  -> Classification
  -> Contract Builder
  -> hmi_contract JSON
  -> Screens/HMI
```

Screens renders precomputed contract values and does not calculate market analytics.

Financial contracts are language-neutral. UI translations and contextual help are presentation-only.

See:

- `docs/I18N.md`
- `docs/DEBUGGING.md`
- `docs/CONTRACT_RULES.md`
- `docs/VALIDATION.md`

## Contract filenames

Screens keeps canonical golden fixtures such as `prices_VR1_FINAL.json`, but runtime Processing outputs may use concise family names. Supported preferred runtime names are:

```text
prices.json
cvd.json
open_interest.json
etf.json
miners.json
volatility.json
liquidations.json
liquidity.json
```

If both a concise runtime name and its canonical golden fixture exist, the concise runtime file is selected. The resolved filename is visible in the contract revision string for debugging.
