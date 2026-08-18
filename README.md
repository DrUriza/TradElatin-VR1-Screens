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

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

On macOS or Linux, activate the environment with
`source .venv/bin/activate` before installing the requirements and running
`python app.py`.

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
