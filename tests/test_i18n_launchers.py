from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_legacy_i18n_asset_is_noop_and_ignored():
    source = (ROOT / "assets" / "i18n_runtime.js").read_text(encoding="utf-8")
    assert "MutationObserver(" not in source
    assert "location.reload(" not in source
    assert "localStorage." not in source
    app_source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "assets_ignore" in app_source
    assert "i18n_runtime" in app_source


def test_no_language_cookie_or_environment_authority_in_i18n_core():
    source = (ROOT / "screen_core" / "i18n.py").read_text(encoding="utf-8")
    assert "request.cookies" not in source
    assert "TRADELATIN_LANG" not in source
    assert "os.getenv" not in source
