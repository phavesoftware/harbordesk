// Loads the Phave site tag on every page. Paste the values from the Harbor
// Desk staging subscription: Settings -> Web -> Write keys -> the
// "Harbor Desk website" key -> tag snippet.
(function () {
  var PHAVE_TAG = {
    src: "https://harbor-desk.phvtrack.dev/bambino.js",
    tenant: "harbor-desk",
    key: "PASTE_WRITE_KEY_HERE",
    consent: "opt_in",
  };

  if (PHAVE_TAG.key.indexOf("PASTE_") === 0) return;

  var s = document.createElement("script");
  s.async = true;
  s.src = PHAVE_TAG.src;
  s.setAttribute("data-phv-tenant", PHAVE_TAG.tenant);
  s.setAttribute("data-phv-key", PHAVE_TAG.key);
  s.setAttribute("data-phv-consent", PHAVE_TAG.consent);
  document.head.appendChild(s);
})();
