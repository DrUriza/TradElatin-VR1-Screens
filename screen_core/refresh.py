from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass
from urllib.parse import quote
from urllib.request import Request, urlopen

# Fixed HMI cadence.  These values are deliberately independent of chart
# timeframe because Processing owns the acquisition/processing schedule.
FAMILY_AUTO_REFRESH_MS: dict[str, int] = {
    "prices": 5_000,
    "cvd": 30_000,
    "open_interest": 60_000,
}

DEFAULT_REFRESH_TIMEOUT_S = 120.0


@dataclass(frozen=True)
class RefreshDispatch:
    configured: bool
    started: bool
    family: str
    endpoint: str | None


def processing_refresh_url() -> str | None:
    value = os.getenv("TRADELATIN_PROCESSING_REFRESH_URL", "").strip()
    return value or None


def refresh_timeout_seconds() -> float:
    raw = os.getenv("TRADELATIN_REFRESH_TIMEOUT_S", str(DEFAULT_REFRESH_TIMEOUT_S))
    try:
        return max(5.0, float(raw))
    except (TypeError, ValueError):
        return DEFAULT_REFRESH_TIMEOUT_S


def _trace(message: str) -> None:
    if os.getenv("TRADELATIN_TRACE_REFRESH", "0").lower() in {"1", "true", "yes"}:
        print(f"[REFRESH] {message}", flush=True)


def _post_refresh(endpoint: str, payload: dict[str, object]) -> None:
    try:
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            endpoint,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        with urlopen(request, timeout=5.0) as response:  # noqa: S310 - configured local integration endpoint
            _trace(f"family={payload.get('family')} HTTP {getattr(response, 'status', '?')}")
    except Exception as exc:  # The Dash request thread must never block/fail on Processing.
        _trace(f"family={payload.get('family')} request failed: {exc}")


def request_family_refresh_async(*, family: str, reason: str, contract_file: str) -> RefreshDispatch:
    """Ask Processing to refresh one family without blocking Dash.

    The endpoint is optional so Screens can still run standalone against static
    JSON files.  If the URL contains ``{family}``, it is replaced with the URL
    encoded family key.  Otherwise the family is sent in the JSON body.
    """
    endpoint = processing_refresh_url()
    if not endpoint:
        return RefreshDispatch(False, False, family, None)

    final_endpoint = endpoint.replace("{family}", quote(family, safe=""))
    payload: dict[str, object] = {
        "family": family,
        "reason": reason,
        "contract_file": contract_file,
        "requested_at": time.time(),
    }
    thread = threading.Thread(
        target=_post_refresh,
        args=(final_endpoint, payload),
        name=f"tradelatin-refresh-{family}",
        daemon=True,
    )
    thread.start()
    return RefreshDispatch(True, True, family, final_endpoint)
