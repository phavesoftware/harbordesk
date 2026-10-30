// Harbor Desk's own code for the Phave forms on the contact, pilot,
// templates and case study pages. It uses only the site tag's documented
// page API, through the tag's queue, so it works whether or not the tag
// has loaded yet. On the dev copy, or with ?formlog in the address, a
// panel lists what the forms report.
(function () {
  "use strict";

  var phv = (window.__phv = window.__phv || {});
  var queue = (phv.q = phv.q || []);
  var FREE_MAIL = /@(gmail|googlemail|yahoo|hotmail|outlook|live|icloud|aol|proton(mail)?)\.[a-z.]+$/i;
  var loaded = new Map();
  var lastAsset = null;
  var logList = null;

  function log(text) {
    if (!logList) return;
    var item = document.createElement("li");
    var time = new Date().toTimeString().slice(0, 8);
    item.textContent = time + "  " + text;
    logList.prepend(item);
  }

  function startLog() {
    if (!/\/dev\//.test(location.pathname) && !/[?&]formlog\b/.test(location.search)) return;
    var panel = document.createElement("aside");
    panel.className = "form-log";
    panel.setAttribute("aria-label", "Form events");
    var title = document.createElement("h2");
    title.textContent = "Form events";
    logList = document.createElement("ol");
    panel.append(title, logList);
    document.body.append(panel);
    log("page script ready");
  }

  function one(id, value) {
    var values = {};
    values[id] = value;
    return values;
  }

  function unconnected(el) {
    var note = document.createElement("p");
    note.className = "form-note form-unset";
    note.textContent = "This form is not connected yet.";
    el.replaceChildren(note);
  }

  function watchDataLayer() {
    var layer = (window.dataLayer = window.dataLayer || []);
    var push = layer.push;
    layer.push = function () {
      for (var i = 0; i < arguments.length; i++) {
        var entry = arguments[i];
        if (entry && typeof entry.event === "string" && entry.event.indexOf("phv.") === 0) {
          log("dataLayer: " + JSON.stringify(entry));
        }
      }
      return push.apply(layer, arguments);
    };
  }

  function watchForms() {
    window.addEventListener("phv:form:success", function (event) {
      var detail = event.detail || {};
      log("phv:form:success: form " + detail.formId + ", values " + JSON.stringify(detail.values));
    });
    queue.push(["forms.whenReady", function (form) {
      var ids = Object.keys(form.getValues());
      log("form ready: tactic " + form.tacticId + ", fields " + ids.join(", "));
      fillAsset(form);
    }]);
  }

  // Templates: the asset a pop-up was opened for goes into its hidden field.
  function fillAsset(form) {
    var host = document.querySelector("[data-hd-asset-field]");
    var field = host && host.getAttribute("data-hd-asset-field");
    if (!field || !lastAsset || !form.element || !form.element.closest("dialog")) return;
    var refused = form.setValues(one(field, lastAsset)) || [];
    log("setValues asset \"" + lastAsset + "\"" + (refused.length ? ", refused " + refused.join(", ") : ""));
  }

  function rememberAsset() {
    // Capture, so the asset is known before the tag's own click handler opens the pop-up.
    document.addEventListener("click", function (event) {
      var trigger = event.target.closest && event.target.closest("[data-hd-asset]");
      if (trigger) lastAsset = trigger.getAttribute("data-hd-asset");
    }, true);
  }

  // Pilot: the plan buttons fill a hidden field the page script may set.
  function pressedPlan(into) {
    return document.querySelector('[data-hd-into="' + into + '"][aria-pressed="true"]');
  }

  function setPlan(button) {
    var into = button.getAttribute("data-hd-into");
    var form = loaded.get(document.querySelector(into));
    var field = button.getAttribute("data-hd-set");
    if (!form || !field) {
      log("plan " + button.getAttribute("data-hd-value") + ": " + (field ? "form not loaded" : "no field id set"));
      return;
    }
    var refused = form.setValues(one(field, button.getAttribute("data-hd-value"))) || [];
    log("setValues plan " + button.getAttribute("data-hd-value") + (refused.length ? ", refused " + refused.join(", ") : ""));
  }

  function bindPlans() {
    document.querySelectorAll("[data-hd-set]").forEach(function (button) {
      button.addEventListener("click", function () {
        var into = button.getAttribute("data-hd-into");
        document.querySelectorAll('[data-hd-into="' + into + '"]').forEach(function (other) {
          other.setAttribute("aria-pressed", String(other === button));
        });
        setPlan(button);
      });
    });
  }

  function workEmailCheck(form, field) {
    form.onValidate(function (values) {
      var email = String(values[field] || "");
      log("onValidate: " + (FREE_MAIL.test(email) ? "refused " + email : "ok"));
      return one(field, FREE_MAIL.test(email) ? "Use your work email." : null);
    });
  }

  function loadForms() {
    document.querySelectorAll("[data-hd-load]").forEach(function (el) {
      var key = el.getAttribute("data-hd-load");
      if (!key) return unconnected(el);
      queue.push(["forms.load", { embed: key, into: el }, function (form) {
        if (!form) {
          log("forms.load " + key + ": no form");
          unconnected(el);
          return;
        }
        log("forms.load " + key + ": painted into #" + el.id);
        loaded.set(el, form);
        var emailField = el.getAttribute("data-hd-work-email");
        if (emailField) workEmailCheck(form, emailField);
        var plan = pressedPlan("#" + el.id);
        if (plan) setPlan(plan);
      }]);
    });
  }

  // Case study: the page opens the pop-up itself and shows its own download.
  function bindOpeners() {
    document.querySelectorAll("[data-hd-open]").forEach(function (button) {
      var key = button.getAttribute("data-hd-open");
      var done = document.querySelector(button.getAttribute("data-hd-done"));
      if (!key) {
        button.disabled = true;
        button.title = "This form is not connected yet.";
        return;
      }
      button.addEventListener("click", function () {
        queue.push(["forms.open", { embed: key }, function (form) {
          if (!form) {
            log("forms.open " + key + ": null (submitted recently, or not placed on this Site)");
            if (done) done.hidden = false;
            return;
          }
          log("forms.open " + key + ": opened");
          form.onSuccess(function () {
            if (done) done.hidden = false;
            var dialog = form.element && form.element.closest("dialog");
            if (dialog) dialog.close();
            log("onSuccess: closed the pop-up and skipped the thank-you");
            return false;
          });
        }]);
      });
    });
  }

  // Templates: a stand-in video that sends the page event halfway through.
  function bindTour() {
    document.querySelectorAll("[data-hd-tour]").forEach(function (tour) {
      var name = tour.getAttribute("data-hd-tour");
      var play = tour.querySelector(".tour-play");
      var bar = tour.querySelector(".tour-progress");
      var time = tour.querySelector(".tour-time");
      var timer = null;
      play.addEventListener("click", function () {
        if (timer) return;
        var elapsed = 0;
        var sent = false;
        play.textContent = "Playing…";
        timer = setInterval(function () {
          elapsed += 1;
          var seconds = elapsed * 9;
          bar.style.width = (elapsed * 5) + "%";
          time.textContent = Math.floor(seconds / 60) + ":" + String(seconds % 60).padStart(2, "0") + " / 3:00";
          if (!sent && elapsed >= 10) {
            sent = true;
            window.dispatchEvent(new CustomEvent(name));
            log("dispatched " + name);
          }
          if (elapsed >= 20) {
            clearInterval(timer);
            timer = null;
            play.textContent = "Play again";
          }
        }, 500);
      });
    });
  }

  startLog();
  watchDataLayer();
  watchForms();
  rememberAsset();
  bindPlans();
  loadForms();
  bindOpeners();
  bindTour();
})();
