from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
CONTRACT_DIR = BASE_DIR / "data" / "contracts"


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
    path = CONTRACT_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Contract not found: {path}")
    stat = path.stat()
    return _load_cached(str(path), stat.st_mtime_ns, stat.st_size)


def contract_revision(filename: str) -> str:
    path = CONTRACT_DIR / filename
    if not path.exists():
        return "missing"
    stat = path.stat()
    return f"{stat.st_mtime_ns}:{stat.st_size}"


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
