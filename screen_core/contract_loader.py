from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
CONTRACT_DIR = BASE_DIR / "data" / "contracts"

# Canonical screen contract filenames remain stable inside the HMI, but the
# runtime producer may publish shorter family-oriented filenames.  Keep the
# resolver deterministic and integration-friendly: explicit runtime aliases
# first, then the canonical golden/reference filename, then one unambiguous
# family-prefix match.
CONTRACT_ALIASES: dict[str, tuple[str, ...]] = {
    "prices_VR1_FINAL.json": (
        "prices.json",
        "price.json",
    ),
    "cvd_volume_orderflow_VR1_FINAL.json": (
        "cvd.json",
        "cvd_orderflow.json",
        "cvd_volume_orderflow.json",
    ),
    "open_interest_and_funding_VR1_FINAL.json": (
        "open_interest.json",
        "open_interest_funding.json",
        "oi.json",
        "oi_funding.json",
    ),
    "etf_exchange_flows_VR1_FINAL.json": (
        "etf.json",
        "etf_flows.json",
        "etf_exchange_flows.json",
    ),
    "on_chain_miners_VR1_FINAL.json": (
        "miners.json",
        "miner.json",
        "on_chain.json",
        "on_chain_miners.json",
    ),
    "volatility_market_regimes_VR1_FINAL.json": (
        "volatility.json",
        "volatility_regimes.json",
        "volatility_market_regimes.json",
    ),
    "long_short_liquidations_VR1_FINAL.json": (
        "liquidations.json",
        "liquidation.json",
        "long_short_liquidations.json",
    ),
    "liquidity_microstructure_VR1_FINAL.json": (
        "liquidity.json",
        "liquidity_microstructure.json",
    ),
}


def _normalized_stem(filename: str) -> str:
    stem = Path(filename).stem.lower().replace("-", "_").replace(" ", "_")
    while "__" in stem:
        stem = stem.replace("__", "_")
    return stem.strip("_")


def _family_prefixes(filename: str) -> tuple[str, ...]:
    aliases = CONTRACT_ALIASES.get(filename, ())
    names = (filename, *aliases)
    prefixes: list[str] = []
    for name in names:
        stem = _normalized_stem(name)
        # Remove release suffixes from the canonical name so files such as
        # prices_runtime.json or cvd_latest.json can still be resolved.
        stem = stem.removesuffix("_vr1_final")
        if stem and stem not in prefixes:
            prefixes.append(stem)
    return tuple(prefixes)


def resolve_contract_path(filename: str) -> Path:
    """Resolve a canonical contract request to an existing JSON file.

    Resolution order is intentionally strict and debuggable:
      1. explicit short/runtime family aliases (for example ``prices.json``);
      2. exact canonical golden/reference filename;
      3. exactly one JSON whose normalized stem starts with a known family
         prefix (for example ``prices_runtime.json``).

    Runtime aliases intentionally take priority over the bundled golden fixture
    when both exist, so Processing can publish ``prices.json`` without forcing
    Screens to rename or delete ``prices_VR1_FINAL.json``.

    Ambiguous prefix matches raise instead of silently choosing a file.
    """
    for alias in CONTRACT_ALIASES.get(filename, ()):
        candidate = CONTRACT_DIR / alias
        if candidate.exists():
            return candidate

    exact = CONTRACT_DIR / filename
    if exact.exists():
        return exact

    prefixes = _family_prefixes(filename)
    matches: list[Path] = []
    if CONTRACT_DIR.exists():
        for candidate in CONTRACT_DIR.glob("*.json"):
            stem = _normalized_stem(candidate.name)
            if any(stem == prefix or stem.startswith(f"{prefix}_") for prefix in prefixes):
                matches.append(candidate)

    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        names = ", ".join(sorted(item.name for item in matches))
        raise FileNotFoundError(
            f"Ambiguous contract for {filename!r} in {CONTRACT_DIR}: {names}. "
            "Keep one family file or use a preferred alias such as prices.json/cvd.json."
        )

    aliases = ", ".join(CONTRACT_ALIASES.get(filename, ())) or "none"
    raise FileNotFoundError(
        f"Contract not found for {filename!r} in {CONTRACT_DIR}. "
        f"Accepted aliases: {aliases}"
    )


@lru_cache(maxsize=32)
def _load_cached(path_text: str, modified_ns: int, size: int) -> dict[str, Any]:
    del modified_ns, size
    path = Path(path_text)
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Screen contract must be a JSON object: {path}")
    return payload


def load_contract(filename: str) -> dict[str, Any]:
    path = resolve_contract_path(filename)
    stat = path.stat()
    return _load_cached(str(path), stat.st_mtime_ns, stat.st_size)


def contract_revision(filename: str) -> str:
    try:
        path = resolve_contract_path(filename)
    except FileNotFoundError:
        return "missing"
    stat = path.stat()
    return f"{path.name}:{stat.st_mtime_ns}:{stat.st_size}"


def screen_metadata(contract: dict[str, Any]) -> dict[str, Any]:
    screen = contract.get("screen")
    header = contract.get("header") if isinstance(contract.get("header"), dict) else {}
    context = contract.get("context") if isinstance(contract.get("context"), dict) else {}

    if isinstance(screen, dict):
        screen_id = screen.get("id") or screen.get("screen_id") or contract.get("screen_id")
        family = screen.get("family") or contract.get("family") or screen_id
        title = screen.get("title") or header.get("title") or family
        subtitle = screen.get("subtitle") or ""
        route = screen.get("route")
    else:
        screen_id = contract.get("screen_id") or screen or contract.get("family")
        family = contract.get("family") or screen_id
        title = header.get("title") or str(screen_id or "TradELATIN")
        subtitle = ""
        route = None

    data_as_of = (
        context.get("data_as_of")
        or context.get("selected_data_as_of")
        or contract.get("reference_timestamp")
        or header.get("data_as_of")
    )
    mode = contract.get("mode")
    if isinstance(mode, dict):
        data_mode = mode.get("data_mode")
        is_demo = mode.get("is_demo")
    else:
        data_mode = context.get("data_mode") or contract.get("data_mode") or mode
        is_demo = context.get("is_demo") if "is_demo" in context else contract.get("is_demo")

    return {
        "screen_id": screen_id,
        "family": family,
        "title": title,
        "subtitle": subtitle,
        "route": route,
        "data_as_of": data_as_of,
        "data_mode": data_mode,
        "is_demo": is_demo,
    }


def _normalize_option(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        value = item.get("id") or item.get("value") or item.get("key") or item.get("label")
        label = item.get("label") or str(value)
        return {"label": label, "value": value}
    return {"label": str(item), "value": item}


def selector_spec(contract: dict[str, Any], selector_name: str) -> tuple[list[dict[str, Any]], Any]:
    selectors = contract.get("selectors") if isinstance(contract.get("selectors"), dict) else {}
    selector = selectors.get(selector_name)

    if selector_name == "range" and selector is None:
        selector = selectors.get("display_range") or contract.get("range_selector")
    if selector_name == "timeframe" and selector is None:
        selector = selectors.get("interval") or contract.get("timeframe_selector")

    if not isinstance(selector, dict):
        context = contract.get("context") if isinstance(contract.get("context"), dict) else {}
        fallback_map = {
            "market": (context.get("available_markets") or context.get("markets"), context.get("default_market") or context.get("selected_market")),
            "timeframe": (context.get("available_timeframes") or context.get("available_intervals") or context.get("timeframes"), context.get("default_timeframe") or context.get("selected_timeframe") or context.get("selected_interval") or context.get("presentation_default_timeframe")),
            "range": (context.get("available_display_ranges"), context.get("selected_display_range") or context.get("default_display_range") or context.get("presentation_default_range")),
        }
        options, selected = fallback_map.get(selector_name, (None, None))
        if not options:
            return [], None
        normalized = [_normalize_option(item) for item in options]
        return normalized, selected or normalized[0]["value"]

    options = selector.get("options") or []
    normalized = [_normalize_option(item) for item in options]
    selected = selector.get("selected") or selector.get("default")
    if selected is None and normalized:
        selected = normalized[0]["value"]
    return normalized, selected


def active_badges(contract: dict[str, Any]) -> list[dict[str, str]]:
    badges = contract.get("badges")
    if badges is None:
        header = contract.get("header") if isinstance(contract.get("header"), dict) else {}
        badges = header.get("badges")
    if not isinstance(badges, list):
        return []

    result: list[dict[str, str]] = []
    for badge in badges:
        if not isinstance(badge, dict):
            continue
        status = str(badge.get("status") or "active").lower()
        if status in {"inactive", "false", "disabled", "off"}:
            continue
        text = badge.get("text") or badge.get("label") or badge.get("id") or badge.get("badge_id")
        if text:
            result.append({"text": str(text), "status": status})
    return result
