/*
 * TradELATIN VR1 - legacy i18n runtime neutralizer.
 *
 * Intentionally NO-OP. Locale state lives only in the Dash URL query
 * (?lang=en / ?lang=es). Never add MutationObserver, DOM translation,
 * cookies, localStorage, or reload-based language switching here.
 *
 * The file remains only so copying this repo over an older Windows folder
 * overwrites any historical V4 i18n_runtime.js that could cause chattering.
 */
(function () {
  'use strict';
})();
