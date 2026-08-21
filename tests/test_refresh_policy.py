from __future__ import annotations

from screen_core.refresh import FAMILY_AUTO_REFRESH_MS, processing_refresh_url, request_family_refresh_async


def test_family_cadence_is_fixed() -> None:
    assert FAMILY_AUTO_REFRESH_MS == {
        "prices": 5_000,
        "cvd": 30_000,
        "open_interest": 60_000,
    }


def test_refresh_hook_is_optional(monkeypatch) -> None:
    monkeypatch.delenv("TRADELATIN_PROCESSING_REFRESH_URL", raising=False)
    assert processing_refresh_url() is None
    result = request_family_refresh_async(
        family="prices",
        reason="manual",
        contract_file="prices_VR1_FINAL.json",
    )
    assert result.configured is False
    assert result.started is False
