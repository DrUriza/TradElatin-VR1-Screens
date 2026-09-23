# C9 Stacks/sBTC Endpoint Catalog

## Catalog status

**Status: Planned / In Development — Pre-Implementation Specification.**

Despite the filename, this catalog does not add application or provider
endpoints. It records the proposed C9 observable groups and candidate source
families that future grant work may map into versioned contracts.

The current public Screen HMI represents C1-C8. No Stacks adapter, operational
Stacks pipeline, C9 JSON contract, C9 route, or C9 HMI exists today. Those are
proposed grant deliverables beginning in Milestone 1. Nothing in this catalog
states or implies grant approval or operational Stacks support.

The architectural sequence is:

`Stacks/sBTC -> Adapter -> Normalization -> Versioned C9 Contracts -> Financial Observables -> HMI`

The HMI does not contact providers. Processing owns acquisition, source
validation, normalization, contract generation, and live-provider status;
Screen consumes the resulting contracts and renders the Processing status.

**C9 owns the Stacks/sBTC data, while C1–C8 can consume C9 observables for cross-family contextual analysis.**

## 1. Committed C9 observables

These are the three committed observable groups. Field names and wire schemas
remain subject to the versioned-contract design performed during grant work.

### C9.1 — sBTC Supply & Peg State

| Observable | Required meaning / constraint |
| --- | --- |
| sBTC total supply | Reported sBTC supply from a validated public source |
| Supply change / net issuance | Change in supply over an explicitly defined interval |
| Mint/burn-related supply activity | Source-supported activity associated with minting or burning |
| Peg/bridge-cap context | Included only where supported by selected public sources |
| Derived reconciliation metrics | Included only when technically supported; must be labeled derived and retain provenance |

### C9.2 — sBTC Bridge Flow

| Observable | Required meaning / constraint |
| --- | --- |
| BTC→sBTC deposits | Bridge operations moving value toward sBTC |
| sBTC→BTC withdrawals | Bridge operations moving value toward BTC |
| Gross deposit volume | Sum of normalized deposit amounts over a defined window |
| Gross withdrawal volume | Sum of normalized withdrawal amounts over a defined window |
| Net bridge flow | Deposits minus withdrawals using compatible units and window |
| Operation counts | Counts separated by direction and, where applicable, state |
| Operation-size distributions | Included only where supported by validated source data |

### C9.3 — sBTC Bridge Operational State

| Observable | Required meaning / constraint |
| --- | --- |
| Operation state | Pending / accepted / confirmed / failed, preserving source semantics |
| Deposit RBF state | Included where applicable |
| Pending value | Normalized value of operations currently pending |
| Operation age / settlement timing | Derived only when timestamps and lifecycle semantics support it |
| Fulfillment BTC fees | Included where available |
| Withdrawal capacity / limits | Source-reported capacity or applicable limits |
| Chain-state and bridge context | Operational context with timestamp, provenance, and quality metadata |

## 2. Proposed source families

These sources are candidates for future validation and mapping. They are not
currently connected to Screen:

- official sBTC contracts such as `sbtc-token` and `sbtc-registry`
- Emily public API
- Stacks node/read-only contract interfaces
- Hiro / Stacks indexed APIs
- protocol-specific contracts/events for future transversal observables

No exact provider path, method, or payload is frozen here. Concrete endpoint
selection, adapter implementation, normalization, and contract schemas belong
to the proposed grant milestones.

## 3. Proposed transversal source surface

The following surface is explicitly separate from the committed C9 observable
groups. It documents future extensibility and possible C1-C8 contextual use;
it does not add functionality or change existing family semantics.

| Family | Proposed C9 context | Semantic guardrail |
| --- | --- | --- |
| C1 Prices | sBTC market price / BTC deviation when a reliable market source exists; DEX/pool execution context | Do not represent these items as currently implemented |
| C2 CVD & Order Flow | sBTC transfers; DEX swaps / signed flow where semantics allow it | Transfers are not CVD; buyer/seller/aggressor semantics require validated evidence |
| C3 Open Interest & Funding | Stacks lending, borrowing, utilization, and rates as context | Lending metrics are not Open Interest or Funding |
| C4 ETF & Exchange Flows | BTC→sBTC deposits; sBTC→BTC withdrawals; gross and net bridge flows | C9 retains ownership of bridge data |
| C5 On-Chain & Miners | sBTC supply, mint/burn, transfers, holders, bridge completion, signer/registry state | Does not replace existing Bitcoin miner metrics |
| C6 Volatility | Bridge stress; pending/failed/RBF activity; measurable peg-related changes; fees; network/bridge conditions | Derived measures require definitions, provenance, and quality metadata |
| C7 Liquidations | Future Stacks DeFi/lending liquidations after protocol and source validation | Keep distinct from derivatives liquidations |
| C8 Liquidity Microstructure | DEX/AMM pool state, reserves, swaps, slippage, and price impact | AMM liquidity must not be presented as order-book depth |

## 4. Non-operational declaration

- C9 is Planned / In Development.
- No Stacks adapter exists today.
- No operational Stacks data pipeline exists today.
- No Stacks C9 HMI exists today.
- Adapter, normalization, versioned contracts, and HMI are proposed grant deliverables.
- The current Screen repository represents C1-C8.
- C1-C8 are implemented and validated primarily through emulator, synthetic-data, and replay workflows.
- The HMI consumes Processing-generated contracts and does not contact providers.
- Live-provider status is generated by Processing and only rendered by Screen.
