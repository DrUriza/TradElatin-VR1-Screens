from __future__ import annotations

import json
from pathlib import Path

import screen_core.contract_loader as loader


def _write(path: Path, family: str) -> None:
    path.write_text(json.dumps({"family": family}), encoding="utf-8")


def test_short_family_aliases(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(loader, "CONTRACT_DIR", tmp_path)
    cases = {
        "prices_VR1_FINAL.json": "prices.json",
        "cvd_volume_orderflow_VR1_FINAL.json": "cvd.json",
        "open_interest_and_funding_VR1_FINAL.json": "open_interest.json",
        "etf_exchange_flows_VR1_FINAL.json": "etf.json",
        "on_chain_miners_VR1_FINAL.json": "miners.json",
        "volatility_market_regimes_VR1_FINAL.json": "volatility.json",
        "long_short_liquidations_VR1_FINAL.json": "liquidations.json",
        "liquidity_microstructure_VR1_FINAL.json": "liquidity.json",
    }
    for canonical, short_name in cases.items():
        _write(tmp_path / short_name, short_name)
        assert loader.resolve_contract_path(canonical).name == short_name
        (tmp_path / short_name).unlink()


def test_runtime_alias_has_priority(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(loader, "CONTRACT_DIR", tmp_path)
    _write(tmp_path / "prices_VR1_FINAL.json", "canonical")
    _write(tmp_path / "prices.json", "alias")
    assert loader.resolve_contract_path("prices_VR1_FINAL.json").name == "prices.json"


def test_unambiguous_family_prefix_is_allowed(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(loader, "CONTRACT_DIR", tmp_path)
    _write(tmp_path / "prices_runtime.json", "prices")
    assert loader.resolve_contract_path("prices_VR1_FINAL.json").name == "prices_runtime.json"


def test_ambiguous_family_prefix_fails_loudly(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(loader, "CONTRACT_DIR", tmp_path)
    _write(tmp_path / "prices_runtime.json", "one")
    _write(tmp_path / "prices_latest.json", "two")
    try:
        loader.resolve_contract_path("prices_VR1_FINAL.json")
    except FileNotFoundError as exc:
        assert "Ambiguous contract" in str(exc)
    else:
        raise AssertionError("Ambiguous family files must not be selected silently")
