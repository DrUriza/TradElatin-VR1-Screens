from __future__ import annotations

import json
from pathlib import Path

import app as app_module
from screen_core.i18n import locale_context, locale_from_search, translate_text

ROOT = Path(__file__).resolve().parents[1]


def _entry_paths(payload: dict) -> set[tuple[str, str, str]]:
    paths: set[tuple[str, str, str]] = set()
    for family, family_block in payload.items():
        if family.startswith("_") or not isinstance(family_block, dict):
            continue
        for section, section_block in family_block.items():
            if not isinstance(section_block, dict):
                continue
            for key, value in section_block.items():
                if isinstance(value, dict):
                    paths.add((family, section, key))
    return paths


def _visible_strings(node):
    result = []
    if node is None:
        return result
    if isinstance(node, str):
        return [node]
    if isinstance(node, (list, tuple)):
        for item in node:
            result.extend(_visible_strings(item))
        return result
    if hasattr(node, "_prop_names"):
        for prop in node._prop_names:
            if not hasattr(node, prop):
                continue
            value = getattr(node, prop)
            if prop == "children":
                result.extend(_visible_strings(value))
            elif prop in {"title", "placeholder"} and isinstance(value, str):
                result.append(value)
            elif prop == "options" and isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and isinstance(item.get("label"), str):
                        result.append(item["label"])
            elif prop == "columns" and isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and isinstance(item.get("name"), str):
                        result.append(item["name"])
    return result


def test_locale_is_only_url_state():
    assert locale_from_search(None) == "en"
    assert locale_from_search("") == "en"
    assert locale_from_search("?lang=en") == "en"
    assert locale_from_search("?lang=es") == "es"
    assert locale_from_search("?lang=xx") == "en"
    assert locale_from_search("?foo=1&lang=es") == "es"


def test_translation_uses_explicit_locale_context():
    with locale_context("en"):
        assert translate_text("DATA AS OF") == "DATA AS OF"
        assert translate_text("RESUMEN DE INDICADORES") == "INDICATOR SUMMARY"
    with locale_context("es"):
        assert translate_text("DATA AS OF") == "DATOS AL"
        assert translate_text("INDICATOR SUMMARY") == "RESUMEN DE INDICADORES"


def test_help_registries_are_structurally_identical_and_specific():
    en = json.loads((ROOT / "data/help/contextual_help_vr1_en.json").read_text(encoding="utf-8"))
    es = json.loads((ROOT / "data/help/contextual_help_vr1_es.json").read_text(encoding="utf-8"))
    assert _entry_paths(en) == _entry_paths(es)
    assert len(_entry_paths(en)) == 144

    generic_spanish = {
        "Resume una métrica principal de la familia Liquidations & Positioning.",
        "Describe un análisis derivado de la Pantalla B de Prices.",
        "Describe una variable principal mostrada en la Pantalla A de CVD & Order Flow.",
    }
    all_es_what = []
    for family, family_block in es.items():
        if family.startswith("_") or not isinstance(family_block, dict):
            continue
        for section_block in family_block.values():
            if not isinstance(section_block, dict):
                continue
            for entry in section_block.values():
                if isinstance(entry, dict):
                    all_es_what.append(entry.get("what_measures"))
    assert generic_spanish.isdisjoint(set(all_es_what))
    assert len(all_es_what) == len(set(all_es_what)) == 144


def test_prices_screen_b_summary_switches_language():
    en_component = app_module.render_screen("/prices/analysis", "?lang=en", None, None, None, 0)
    es_component = app_module.render_screen("/prices/analysis", "?lang=es", None, None, None, 0)
    en_text = "\n".join(_visible_strings(en_component))
    es_text = "\n".join(_visible_strings(es_component))

    assert "INDICATOR SUMMARY" in en_text
    assert "STRENGTH LEGEND" in en_text
    assert "RESUMEN DE INDICADORES" not in en_text
    assert "LEYENDA DE FUERZA" not in en_text

    assert "RESUMEN DE INDICADORES" in es_text
    assert "LEYENDA DE FUERZA" in es_text
    assert "INDICATOR SUMMARY" not in es_text
    assert "STRENGTH LEGEND" not in es_text


def test_all_routes_render_in_both_languages_without_obvious_cross_language_ui():
    routes = []
    for module in app_module.SCREENS:
        routes.append(module.ROUTE)
        if module.HAS_ANALYSIS:
            routes.append(f"{module.ROUTE}/analysis")

    spanish_markers = (
        "resumen de indicadores", "leyenda de fuerza", "← regresar",
        "no seleccionaste", "pantalla b especializada",
    )
    english_markers = (
        "indicator summary", "strength legend", "← back",
        "no metrics selected for screen b", "screen b specialized",
    )

    for route in routes:
        en_component = app_module.render_screen(route, "?lang=en", None, None, None, 0)
        es_component = app_module.render_screen(route, "?lang=es", None, None, None, 0)
        en_text = "\n".join(_visible_strings(en_component)).lower()
        es_text = "\n".join(_visible_strings(es_component)).lower()
        for marker in spanish_markers:
            assert marker not in en_text, f"EN leak on {route}: {marker}"
        for marker in english_markers:
            assert marker not in es_text, f"ES leak on {route}: {marker}"


def test_language_shell_is_single_app_single_state():
    en = app_module.sync_locale_shell("?lang=en")
    es = app_module.sync_locale_shell("?lang=es")
    assert en[1] == "LANGUAGE"
    assert es[1] == "IDIOMA"
    assert "language-option-active" in en[2]
    assert "language-option-active" in es[3]


def _hrefs(node):
    result = []
    if node is None:
        return result
    if isinstance(node, (list, tuple)):
        for item in node:
            result.extend(_hrefs(item))
        return result
    if hasattr(node, "_prop_names"):
        href = getattr(node, "href", None)
        if isinstance(href, str) and href.startswith("/"):
            result.append(href)
        if hasattr(node, "children"):
            result.extend(_hrefs(getattr(node, "children")))
    return result


def test_internal_navigation_preserves_explicit_locale():
    for locale in ("en", "es"):
        for module in app_module.SCREENS:
            component = app_module.render_screen(module.ROUTE, f"?lang={locale}", None, None, None, 0)
            for href in _hrefs(component):
                assert f"lang={locale}" in href, (module.ROUTE, locale, href)


def test_language_callback_graph_has_no_feedback_path():
    app_module.app._setup_server()
    callback_map = app_module.app.callback_map
    language_callback = callback_map["url.search"]
    assert {item["id"] for item in language_callback["inputs"]} == {"lang-en", "lang-es"}

    # URL language is an input to rendering/localization callbacks only; no
    # callback that consumes it is allowed to write url.search again.
    for output, spec in callback_map.items():
        consumes_search = any(item.get("id") == "url" and item.get("property") == "search" for item in spec.get("inputs", []))
        if consumes_search:
            assert output != "url.search"


def test_no_secondary_locale_store_exists():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "locale-store" not in source
    for path in (ROOT / "screens").glob("*.py"):
        assert "locale-store" not in path.read_text(encoding="utf-8")


def test_screen_source_strings_are_canonical_english():
    """Visible HMI source text should not regress to Spanish hard-coding."""
    import ast
    import re

    spanish = re.compile(
        r"[áéíóúñÁÉÍÓÚÑ]|\\b(?:Precio|Cambio|Volumen|Indicadores|Selecciona|Bandas|Niveles|"
        r"Soportes|Resistencias|Acumulado|Regresar|Análisis|Pantalla|Resumen|Leyenda|"
        r"Fuerza|Señal|Presión|Compra|Venta|Tendencia|Régimen|Flujo)\\b",
        re.IGNORECASE,
    )
    leaks = []
    for path in (ROOT / "screens").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and spanish.search(node.value):
                leaks.append((path.name, getattr(node, "lineno", 0), node.value))
    assert not leaks, leaks[:10]


def test_spanish_contextual_help_has_no_mixed_ui_vocabulary():
    payload = json.loads((ROOT / "data/help/contextual_help_vr1_es.json").read_text(encoding="utf-8"))
    text = json.dumps(payload, ensure_ascii=False)
    forbidden = (
        " Price ", " Liquidity ", " Liquidations ", " Volatility ",
        " forced flow ", " crowding ", " deleveraging ",
    )
    for token in forbidden:
        assert token not in f" {text} ", token
