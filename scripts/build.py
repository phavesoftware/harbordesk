"""Builds the static Harbor Desk site from src/ fragments.

Run from the repo root: python3 scripts/build.py
Every page is written as plain HTML (folder/index.html), so the published
site needs no build step on GitHub Pages.

Three languages, each under its own path: US English under en-us/ (the
source, src/*.html), British English under en-gb/ (derived from the source
by scripts/en_gb.py, or taken from src/en-gb/<file> where a page needs its
own words) and German under de-de/ (src/de-de/*.html, titles and
descriptions in src/de-de/meta.json).

Two variants of the whole site: the staging site at the root, carrying the
staging Phave site tag, and a dev copy under dev/, carrying a tag served by
a developer's local Phave (noindex, canonical to the staging page, out of
the sitemap). The bare root of each variant, and every address the site had
before the language paths, is a small redirect page.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, replace
from html import escape
from pathlib import Path

import en_gb

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
BASE = "/harbordesk"
ORIGIN = "https://phavesoftware.github.io"
SITE_NAME = "Harbor Desk"
LASTMOD = "2026-10-29"
STAGING_TAG = (
    '<script async src="https://harbor-desk.phvtrack.dev/bambino.js" '
    'data-phv-tenant="harbor-desk" '
    'data-phv-key="phv_wk_PFesdDymtxDz-Sfh6mE4epN-Ikw8pBww" '
    'data-phv-consent="opt_out"></script>'
)
# Served by the developer's local Phave (Settings > Web > Write keys there).
# Chrome lets an https page load it because localhost counts as secure.
DEV_TAG = (
    '<script async src="http://beacon.local-phave.localhost:3000/bambino.js" '
    'data-phv-tenant="acme" '
    'data-phv-key="phv_wk_OOqtk86aN_cAqBa_VGaUvQFnkjl4hXLQ" '
    'data-phv-consent="opt_out"></script>'
)


# The Phave email blocks, on the dev copy's Email preferences and Unsubscribe
# pages. The head line must be the first element in <head>: it takes the
# email link code out of the address before any other script can read it.
# The snippets are Phave's own, pasted exactly as given.
PREF_HEAD = (
    '<script>(function(){try{var h=location.hash,m=/(?:^#|&)phv-pref=([^&]*)/.exec(h);if(!m)return;'
    'var c=decodeURIComponent(m[1]||"");if(c)sessionStorage.setItem("phv-pref",c);'
    'var r=h.slice(1).split("&").filter(function(p){return p.indexOf("phv-pref=")!==0}).join("&");'
    'history.replaceState(history.state,"",location.pathname+location.search+(r?"#"+r:""))}catch(e){}})();</script>'
)
BLOCK_TAG = (
    '<script async src="http://beacon.local-phave.localhost:3000/bambino.js" data-phv-tenant="acme" '
    'data-phv-key="phv_wk_OOqtk86aN_cAqBa_VGaUvQFnkjl4hXLQ"></script>'
)
# Page path -> (the page's embed box, the Phave block drawn inside it).
EMAIL_BLOCKS = {
    "email-preferences/": ('<div id="email-preferences-form" class="form-embed"></div>', "preferences"),
    "unsubscribe/": ('<div id="unsubscribe-form" class="form-embed"></div>', "unsubscribe"),
}


def block_snippet(name: str) -> str:
    return f'{BLOCK_TAG}\n      <div data-phave-block="{name}"></div>'


# The Phave forms on the contact, pilot, library and case study pages, per
# copy, because each copy talks to its own subscription. A form is named by
# the code in its embed line (Form tactic > Host my form > Embed code for,
# the value of data-phave-form); a field by its Field id (the field's
# settings in the form editor). "" until the form exists there: the page
# then says the form is not connected and its buttons do nothing.
FORM_NAMES = ("contact", "pilot", "asset", "tour", "newsletter", "case_study")
FIELD_NAMES = ("pilot_plan", "pilot_email", "asset_name")
STAGING_FORMS: dict[str, str] = {name: "" for name in FORM_NAMES + FIELD_NAMES}
DEV_FORMS: dict[str, str] = {
    "contact": "f12ipv160o33xg4",
    "pilot": "f192cema0d70ni4",
    "asset": "f1amu4jl08f9dj9",
    "tour": "f0xymbuk18hnaei",
    "newsletter": "f10eyop010cakmb",
    "case_study": "f0dpjfdh1ovcf9k",
    "pilot_plan": "aaac4266-96f5-425a-9918-f2fa213e1e9f",
    "pilot_email": "2dc1e402-713a-4feb-b50f-85be57d28c11",
    "asset_name": "48c44e0a-e2dc-44e2-8e72-2e477ac051dc",
}


@dataclass(frozen=True)
class Variant:
    prefix: str  # "" for staging, "dev/" for the dev copy
    tag: str
    public: bool  # indexed and in the sitemap
    forms: dict[str, str]  # FORM_NAMES and FIELD_NAMES to this copy's values


STAGING = Variant("", STAGING_TAG, True, STAGING_FORMS)
DEV = Variant("dev/", DEV_TAG, False, DEV_FORMS)
VARIANTS = [STAGING, DEV]


@dataclass(frozen=True)
class Lang:
    code: str  # BCP 47, as html lang and hreflang
    prefix: str  # "en-us/" etc.
    label: str  # the picker's name, in the language itself
    short: str  # the picker's closed face
    flag: str  # assets/flags/<flag>.svg
    og_suffix: str  # "" or "-de": which social card set the pages use
    currency: str  # ISO 4217, for structured data


LANGS = [
    Lang("en-US", "en-us/", "English (US)", "EN", "us", "", "USD"),
    Lang("en-GB", "en-gb/", "English (UK)", "EN", "gb", "", "GBP"),
    Lang("de-DE", "de-de/", "Deutsch", "DE", "de", "-de", "EUR"),
]
SOURCE = LANGS[0]
BY_CODE = {lang.code: lang for lang in LANGS}

# Addresses the site had before the language paths, and where they go now.
RETIRED_PREFIXES = {"": SOURCE, "en-ca/": SOURCE, "fr-ca/": SOURCE}

# Every string the page chrome writes, per language. en-GB is derived.
CHROME_EN = {
    "skip": "Skip to content",
    "logo_alt": "Harbor Desk logo",
    "nav_label": "Main",
    "nav": {"product": "Product", "customers": "Customers", "pricing": "Pricing",
            "resources": "Resources", "events": "Events", "about": "About"},
    "book": "Book a demo",
    "lang_label": "Language",
    "dev_badge": "Dev",
    "dev_title": "Dev copy: this page loads the Phave site tag from a local Phave",
    "tagline": "See churn coming. Act before renewal.",
    "country": "United States",
    "cols": {
        "Product": [("product/", "Product overview"), ("product/#health-scores", "Health Scores"),
                    ("product/#playbooks", "Playbooks"), ("product/#ebr-builder", "EBR Builder"),
                    ("pricing/", "Pricing")],
        "Company": [("about/", "About"), ("customers/", "Customers"), ("resources/", "Resources"),
                    ("events/", "Events"), ("events/churn-risk-teardown-workshop/", "Churn-risk teardown workshop"),
                    ("brand/", "Brand and press"), ("", "Home")],
        "Get started": [("demo/", "Book a demo"), ("demo/#talk-to-sales", "Talk to sales"),
                        ("contact/", "Contact us"), ("pilot/", "Start a pilot"),
                        ("resources/templates/", "Templates and guides"),
                        ("privacy/", "Privacy policy"), ("terms/", "Terms of use"),
                        ("email-preferences/", "Email preferences")],
    },
    "rights": "&copy; 2026 Harbor Desk, Inc. All rights reserved.",
    "fictional": "Harbor Desk is a fictional company used for product demos.",
}
CHROME_DE = {
    "skip": "Zum Inhalt springen",
    "logo_alt": "Harbor Desk Logo",
    "nav_label": "Hauptmenü",
    "nav": {"product": "Produkt", "customers": "Kunden", "pricing": "Preise",
            "resources": "Ressourcen", "events": "Events", "about": "Über uns"},
    "book": "Demo buchen",
    "lang_label": "Sprache",
    "dev_badge": "Dev",
    "dev_title": "Dev-Kopie: Diese Seite lädt das Phave Site-Tag aus einem lokalen Phave",
    "tagline": "Churn kommen sehen. Vor der Verlängerung handeln.",
    "country": "Vereinigte Staaten",
    "cols": {
        "Produkt": [("product/", "Produktüberblick"), ("product/#health-scores", "Health Scores"),
                    ("product/#playbooks", "Playbooks"), ("product/#ebr-builder", "EBR Builder"),
                    ("pricing/", "Preise")],
        "Unternehmen": [("about/", "Über uns"), ("customers/", "Kunden"), ("resources/", "Ressourcen"),
                        ("events/", "Events"),
                        ("events/churn-risk-teardown-workshop/", "Workshop „Churn-Risiko auf dem Prüfstand“"),
                        ("brand/", "Marke und Presse"), ("", "Startseite")],
        "Erste Schritte": [("demo/", "Demo buchen"), ("demo/#talk-to-sales", "Mit dem Vertrieb sprechen"),
                           ("contact/", "Kontakt"), ("pilot/", "Pilotphase starten"),
                           ("resources/templates/", "Vorlagen und Leitfäden"),
                           ("privacy/", "Datenschutzerklärung"), ("terms/", "Nutzungsbedingungen"),
                           ("email-preferences/", "E-Mail-Einstellungen")],
    },
    "rights": "&copy; 2026 Harbor Desk, Inc. Alle Rechte vorbehalten.",
    "fictional": "Harbor Desk ist ein fiktives Unternehmen für Produktdemos.",
}


def _en_gb_chrome(chrome: dict) -> dict:
    out = json.loads(json.dumps(chrome))
    out["nav"] = {k: en_gb.text(v) for k, v in out["nav"].items()}
    out["cols"] = {en_gb.text(t): [(p, en_gb.text(l)) for p, l in links] for t, links in out["cols"].items()}
    for key in ("tagline", "book"):
        out[key] = en_gb.text(out[key])
    return out


CHROME = {"en-US": CHROME_EN, "en-GB": _en_gb_chrome(CHROME_EN), "de-DE": CHROME_DE}

WORKSHOP_PATH = "events/churn-risk-teardown-workshop/"
WORKSHOP_SESSIONS = [
    # (ISO start, ISO end) in Pacific Time; ET is three hours later.
    ("2026-11-10T09:00:00-08:00", "2026-11-10T10:00:00-08:00"),
    ("2026-11-18T11:00:00-08:00", "2026-11-18T12:00:00-08:00"),
    ("2026-12-03T08:00:00-08:00", "2026-12-03T09:00:00-08:00"),
]
WORKSHOP_EN = {
    "name": "Churn-risk teardown workshop",
    "description": "A 60-minute live working session for customer success leaders: how your team flags churn risk today, where accounts slip through before renewal, and which customer conversations should happen sooner.",
}

# The variant being written. Set once per pass by build(); every URL the
# pages link to (other than shared assets) stays inside it.
_variant = STAGING


def workshop_events(lang: Lang, words: dict) -> list[dict]:
    page_url = f"{ORIGIN}{url(WORKSHOP_PATH, lang)}"
    return [
        {
            "@context": "https://schema.org",
            "@type": "Event",
            "name": words["name"],
            "description": words["description"],
            "inLanguage": lang.code,
            "startDate": start,
            "endDate": end,
            "eventAttendanceMode": "https://schema.org/OnlineEventAttendanceMode",
            "eventStatus": "https://schema.org/EventScheduled",
            "location": {"@type": "VirtualLocation", "url": page_url},
            "image": f"{ORIGIN}{BASE}/assets/og-workshop{lang.og_suffix}.png",
            "maximumAttendeeCapacity": 8,
            "isAccessibleForFree": True,
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": lang.currency,
                       "url": f"{page_url}#reserve", "availability": "https://schema.org/LimitedAvailability"},
            "organizer": {"@type": "Organization", "name": "Harbor Desk", "url": f"{ORIGIN}{url('', lang)}"},
            "performer": [
                {"@type": "Person", "name": "Priya Raman", "jobTitle": "VP of Customer Success"},
                {"@type": "Person", "name": "Maya Okafor", "jobTitle": "Co-founder and Chief Executive Officer"},
            ],
        }
        for start, end in WORKSHOP_SESSIONS
    ]


@dataclass
class Page:
    path: str  # "" for home, else "pricing/" etc.
    source: str  # fragment file under src/ (and src/de-de/)
    title: str
    description: str
    nav: str | None = None  # header nav key this page highlights
    kind: str = "website"
    index: bool = True
    og_image: str = "og-image"  # assets/<og_image><lang suffix>.png
    og_alt: str = "Harbor Desk logo with the line: See churn coming. Act before renewal."
    workshop: bool = False  # carries the workshop's Event structured data


PAGES = [
    Page("", "home.html", "Harbor Desk: the customer success platform for B2B SaaS",
         "Harbor Desk gives B2B SaaS customer success teams health scores they trust, playbooks that act on them, and EBR decks built from usage data. See churn coming. Act before renewal."),
    Page("product/", "product.html", "Product: Health Scores, Playbooks and EBR Builder · Harbor Desk",
         "How Harbor Desk Health Scores, Playbooks and the EBR Builder work, who uses each one, and a concrete example of each.", "product"),
    Page("customers/", "customers.html", "Customers and case studies · Harbor Desk",
         "How Tidewater Freight cut churn 18%, Northwind Analytics raised net revenue retention 9 points, and Lighthouse Payroll cut EBR prep from 6 hours to 40 minutes.", "customers"),
    Page("pricing/", "pricing.html", "Pricing: Starter, Growth and Enterprise plans · Harbor Desk",
         "Harbor Desk pricing: Starter from $18,000 a year, Growth from $42,000 a year, Enterprise from $90,000 a year. Annual platform fee with CSM seats included. Talk to sales for a quote.", "pricing"),
    Page("resources/", "resources.html", "Resources: the Harbor Desk blog for customer success leaders",
         "Practical writing for customer success leaders on health scores, playbooks and executive business reviews, from the team at Harbor Desk.", "resources"),
    Page("resources/building-a-health-score-your-csms-trust/", "post-health-score.html",
         "Building a health score your CSMs trust · Harbor Desk",
         "A health score only works if the people using it believe it. Five rules for building one your CSMs will actually act on.", "resources", "article"),
    Page("resources/running-ebrs-that-renew/", "post-ebrs.html", "Running EBRs that renew · Harbor Desk",
         "Most executive business reviews are status reports nobody asked for. How to run an EBR that earns the renewal conversation.", "resources", "article"),
    Page("resources/playbooks-that-csms-dont-ignore/", "post-playbooks.html",
         "Playbooks your CSMs won't ignore · Harbor Desk",
         "Automated customer success playbooks fail when they create work nobody can do. How to design playbooks that fire rarely and matter when they do.", "resources", "article"),
    Page("about/", "about.html", "About Harbor Desk: our story, team and values",
         "Harbor Desk was founded in 2019 in Portland, Maine, by former customer success leaders. 140 people, one job: help CS teams see churn coming and act before renewal.", "about"),
    Page("demo/", "demo.html", "Book a demo · Harbor Desk",
         "Book a 30-minute Harbor Desk demo with a customer success specialist. See Health Scores, Playbooks and the EBR Builder on accounts like yours.", "demo"),
    Page("demo/thanks/", "demo-thanks.html", "Thanks, we'll be in touch · Harbor Desk",
         "Thanks for booking a Harbor Desk demo. A customer success specialist will email you within one business day.", "demo", index=False),
    Page("events/", "events.html", "Events: live workshops for customer success leaders · Harbor Desk",
         "Free live workshops from Harbor Desk for VPs of Customer Success, CS Operations and Chief Customer Officers, including the Churn-risk teardown workshop.", "events"),
    Page(WORKSHOP_PATH, "event-churn-risk-teardown.html",
         "Churn-risk teardown workshop: a free 60-minute working session · Harbor Desk",
         "A free 60-minute live session on Zoom for CS leaders. Work through how your team spots churn risk, where accounts slip before renewal, and which conversations to have sooner. 8 companies per session.",
         "events", og_image="og-workshop",
         og_alt="Harbor Desk logo with the title: Churn-risk teardown workshop. See the accounts at risk while there is still time to talk.",
         workshop=True),
    Page(f"{WORKSHOP_PATH}thanks/", "event-churn-risk-teardown-thanks.html",
         "Thanks, you're registered: Churn-risk teardown workshop · Harbor Desk",
         "You're registered for the Harbor Desk Churn-risk teardown workshop. Look out for a calendar invite and a short pre-work email.",
         "events", og_image="og-workshop",
         og_alt="Harbor Desk logo with the title: Churn-risk teardown workshop.", index=False),
    Page("contact/", "contact.html", "Contact Harbor Desk: sales, support and partnerships",
         "Talk to Harbor Desk about pricing, a demo, your account or a partnership. Tell us where you are and the team in your time zone replies within one business day.", None),
    Page("pilot/", "pilot.html", "Start a 30-day pilot on your own accounts · Harbor Desk",
         "Run Harbor Desk on your own book of accounts for 30 days on Growth or Enterprise, with the pilot fee credited against your first year.", "pricing"),
    Page("resources/templates/", "templates.html", "Templates and guides for customer success teams · Harbor Desk",
         "Free templates from Harbor Desk: an EBR deck, a health score worksheet and a renewal risk playbook kit, plus a three-minute product tour.", "resources"),
    Page("customers/tidewater-freight/", "case-tidewater.html",
         "Case study: how Tidewater Freight cut gross churn 18% · Harbor Desk",
         "How Tidewater Freight rebuilt its health score around four signals, launched three Playbooks, and cut gross churn 18% in 12 months.", "customers", "article"),
    Page("brand/", "brand.html", "Brand and press kit · Harbor Desk",
         "Harbor Desk logo files, color palette with hex values, fonts, and the rules for how we write: tone, words we avoid and product name capitalization.", None),
    Page("privacy/", "privacy.html", "Privacy policy · Harbor Desk",
         "How Harbor Desk collects, uses and protects information about visitors to this website, the cookies it sets, and how to opt out.", None),
    Page("terms/", "terms.html", "Terms of use · Harbor Desk",
         "The terms that govern use of the Harbor Desk website.", None),
    # Reached from links in email; the Phave form embeds go in each page's box.
    Page("email-preferences/", "email-preferences.html", "Email preferences · Harbor Desk",
         "Choose which Harbor Desk emails you get: product news, blog posts and workshop invitations.", None,
         index=False),
    Page("unsubscribe/", "unsubscribe.html", "Unsubscribe from Harbor Desk email · Harbor Desk",
         "Stop receiving marketing email from Harbor Desk.", None, index=False),
]

HEADER_NAV = ["product", "customers", "pricing", "resources", "events", "about"]
NAV_PATHS = {key: f"{key}/" for key in HEADER_NAV}

# A {{base}} link to one of these stays at the site root in every language.
SHARED_FILES = re.compile(r"^/(assets/|favicon|apple-touch-icon|sitemap\.xml|robots\.txt)")


def url(path: str, lang: Lang = SOURCE, variant: Variant | None = None) -> str:
    variant = variant or _variant
    return f"{BASE}/{variant.prefix}{lang.prefix}{path}"


def asset(path: str) -> str:
    return f"{BASE}/{path}"


def localize_links(body: str, lang: Lang) -> str:
    def swap(m: re.Match[str]) -> str:
        rest = m.group(1) or ""
        if SHARED_FILES.match(rest):
            return f"{BASE}{rest}"
        return url(rest.lstrip("/"), lang)

    return re.sub(r"\{\{base\}\}(/[^\"'\s<>)]*)?", swap, body)


def page_for(page: Page, lang: Lang) -> Page:
    """The page's metadata in a language."""
    if lang.code == "en-GB":
        return replace(page, title=en_gb.text(page.title), description=en_gb.text(page.description))
    if lang.code == "de-DE":
        meta = DE_META[page.path]
        return replace(page, title=meta["title"], description=meta["description"], og_alt=meta["og_alt"])
    return page


def fragment(page: Page, lang: Lang) -> str:
    if lang.code == "de-DE":
        return (SRC / "de-de" / page.source).read_text()
    if lang.code == "en-GB":
        own = SRC / "en-gb" / page.source
        return own.read_text() if own.exists() else en_gb.html((SRC / page.source).read_text())
    return (SRC / page.source).read_text()


def flag(lang: Lang) -> str:
    return f'<img src="{asset(f"assets/flags/{lang.flag}.svg")}" alt="" class="flag" width="20" height="14">'


def language_picker(page: Page, lang: Lang) -> str:
    chrome = CHROME[lang.code]
    items = []
    for other in LANGS:
        current = ' aria-current="true"' if other is lang else ""
        items.append(
            f'<li><a href="{url(page.path, other)}" hreflang="{other.code}" lang="{other.code}"{current}>'
            f"{flag(other)}<span>{other.label}</span></a></li>"
        )
    lis = "\n          ".join(items)
    return f"""<details class="lang-picker">
      <summary aria-label="{chrome["lang_label"]}: {lang.label}" title="{chrome["lang_label"]}">{flag(lang)}<span>{lang.short}</span></summary>
      <ul>
          {lis}
      </ul>
    </details>"""


def dev_badge(lang: Lang) -> str:
    if _variant.public:
        return ""
    chrome = CHROME[lang.code]
    return f'\n    <span class="dev-badge" title="{chrome["dev_title"]}">{chrome["dev_badge"]}</span>'


def header(page: Page, lang: Lang) -> str:
    chrome = CHROME[lang.code]
    items = []
    for key in HEADER_NAV:
        current = ' aria-current="page"' if page.nav == key else ""
        items.append(f'<li><a href="{url(NAV_PATHS[key], lang)}"{current}>{chrome["nav"][key]}</a></li>')
    demo_current = ' aria-current="page"' if page.nav == "demo" else ""
    items.append(f'<li><a class="btn btn-primary" href="{url("demo/", lang)}"{demo_current}>{chrome["book"]}</a></li>')
    nav_items = "\n        ".join(items)
    return f"""<header class="site-header">
  <div class="wrap">
    <a href="{url("", lang)}" class="logo-link"><img src="{asset("assets/logo.svg")}" alt="{chrome["logo_alt"]}" class="logo" width="172" height="36"></a>{dev_badge(lang)}
    <nav class="nav" aria-label="{chrome["nav_label"]}">
      <ul>
        {nav_items}
      </ul>
    </nav>
    {language_picker(page, lang)}
  </div>
</header>"""


def footer(lang: Lang) -> str:
    chrome = CHROME[lang.code]

    def col(title: str, links: list[tuple[str, str]]) -> str:
        lis = "\n".join(f'          <li><a href="{url(p, lang)}">{escape(label, quote=False)}</a></li>' for p, label in links)
        return f"""      <nav aria-label="{title}">
        <h2>{title}</h2>
        <ul>
{lis}
        </ul>
      </nav>"""

    cols = "\n".join(col(t, links) for t, links in chrome["cols"].items())
    return f"""<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div>
        <img src="{asset("assets/logo-white.svg")}" alt="{chrome["logo_alt"]}" class="footer-logo" width="143" height="30">
        <p>{chrome["tagline"]}</p>
        <address>Harbor Desk, Inc.<br>220 Wharf Street<br>Portland, ME 04101<br>{chrome["country"]}</address>
      </div>
{cols}
    </div>
    <div class="footer-base">
      <span>{chrome["rights"]}</span>
      <span>{chrome["fictional"]}</span>
    </div>
  </div>
</footer>"""


def organization(lang: Lang) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "Harbor Desk",
        "legalName": "Harbor Desk, Inc.",
        "url": f"{ORIGIN}{url('', lang, STAGING)}",
        "logo": f"{ORIGIN}{BASE}/assets/logo.png",
        "slogan": CHROME[lang.code]["tagline"],
        "description": "Harbor Desk is a customer success platform for B2B SaaS companies with 50 to 2,000 employees: health scores, playbooks and executive business reviews built from usage data.",
        "foundingDate": "2019",
        "numberOfEmployees": {"@type": "QuantitativeValue", "value": 140},
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "220 Wharf Street",
            "addressLocality": "Portland",
            "addressRegion": "ME",
            "postalCode": "04101",
            "addressCountry": "US",
        },
    }


def alternates(page: Page) -> str:
    links = [f'<link rel="alternate" hreflang="{l.code}" href="{ORIGIN}{url(page.path, l)}">' for l in LANGS]
    links.append(f'<link rel="alternate" hreflang="x-default" href="{ORIGIN}{url(page.path)}">')
    return "\n  ".join(links)


def head(page: Page, lang: Lang) -> str:
    # The dev copy points search engines at the staging page it mirrors.
    canonical = f"{ORIGIN}{url(page.path, lang, STAGING)}"
    og_image = f"{ORIGIN}{asset(f'assets/{page.og_image}{lang.og_suffix}.png')}"
    og_alt = escape(page.og_alt)
    ld = [organization(lang)]
    if page.workshop:
        ld.append(workshop_events(lang, DE_META["_event"] if lang.code == "de-DE" else WORKSHOP_EN))
    page_ld = "".join(f'\n  <script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld)
    title = escape(page.title)
    desc = escape(page.description)
    robots = "" if page.index and _variant.public else '\n  <meta name="robots" content="noindex">'
    og_locale = lang.code.replace("-", "_")
    others = "".join(f'\n  <meta property="og:locale:alternate" content="{l.code.replace("-", "_")}">' for l in LANGS if l is not lang)
    first = f"\n  {PREF_HEAD}" if email_block(page) else ""
    return f"""<head>{first}
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{desc}">{robots}
  <link rel="canonical" href="{canonical}">
  {alternates(page)}
  <meta property="og:type" content="{page.kind}">
  <meta property="og:site_name" content="{SITE_NAME}">
  <meta property="og:locale" content="{og_locale}">{others}
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{og_image}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="{og_alt}">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" href="{asset("favicon.ico")}" sizes="any">
  <link rel="icon" href="{asset("favicon.svg")}" type="image/svg+xml">
  <link rel="apple-touch-icon" href="{asset("apple-touch-icon.png")}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;family=Manrope:wght@700;800&amp;display=swap">
  <link rel="stylesheet" href="{asset("assets/site.css")}">{page_ld}
  <!-- PHAVE SITE TAG GOES HERE -->
  {_variant.tag}
</head>"""


def email_block(page: Page) -> tuple[str, str] | None:
    """The page's (embed box, Phave block name), on the dev copy only."""
    return None if _variant.public else EMAIL_BLOCKS.get(page.path)


FORM_KEY = re.compile(r"^[a-z0-9_]*$")
UNCONNECTED = '<p class="form-note form-unset">This form is not connected yet.</p>'


def form_value(name: str) -> str:
    if name not in _variant.forms:
        raise SystemExit(f"unknown form or field {name!r}: add it to FORM_NAMES or FIELD_NAMES")
    value = _variant.forms[name]
    if name in FORM_NAMES and not FORM_KEY.match(value):
        raise SystemExit(f"{_variant.prefix or 'staging'} form {name!r}: {value!r} is not an embed code")
    return value


def fill_forms(body: str) -> str:
    """{{embed:x}} is the embed line (the tag beside the form, as Phave
    writes it), {{open:x}} the pop-up trigger attribute, {{form:x}} and
    {{field:x}} the bare values the page script reads."""
    def embed(m: re.Match[str]) -> str:
        key = form_value(m.group(1))
        return f'{{{{tag}}}}\n        <div data-phave-form="{key}"></div>' if key else UNCONNECTED

    def opener(m: re.Match[str]) -> str:
        key = form_value(m.group(1))
        return f' data-phave-form-open="{key}"' if key else ""

    body = re.sub(r"\{\{embed:([a-z_]+)\}\}", embed, body)
    body = re.sub(r" ?\{\{open:([a-z_]+)\}\}", opener, body)
    return re.sub(r"\{\{(?:form|field):([a-z_]+)\}\}", lambda m: escape(form_value(m.group(1))), body)


def render(page: Page, lang: Lang) -> str:
    body = fill_forms(localize_links(fragment(page, lang), lang)).replace("{{tag}}", _variant.tag)
    if block := email_block(page):
        box, name = block
        body = body.replace(box, box.replace("></div>", f">\n      {block_snippet(name)}\n    </div>"))
    h1_count = len(re.findall(r"<h1[\s>]", body))
    if h1_count != 1:
        raise SystemExit(f"{lang.prefix}{page.source}: expected one <h1>, found {h1_count}")
    meta = page_for(page, lang)
    return f"""<!doctype html>
<html lang="{lang.code}">
{head(meta, lang)}
<body>
<a class="skip" href="#main">{CHROME[lang.code]["skip"]}</a>
{header(meta, lang)}
<main id="main">
{body.strip()}
</main>
{footer(lang)}
</body>
</html>
"""


def redirect(target: str, pick_language: bool = False) -> str:
    """A page that sends the visitor on to `target`, keeping any #fragment.
    The bare root of a variant picks a language from the browser first."""
    pick = ""
    if pick_language:
        base = target[: -len(SOURCE.prefix)]
        pick = f"""
    var langs = (navigator.languages || [navigator.language || ""]).map(function (l) {{ return l.toLowerCase(); }});
    for (var i = 0; i < langs.length; i++) {{
      if (langs[i].indexOf("de") === 0) {{ to = "{base}de-de/"; break; }}
      if (langs[i] === "en-gb" || langs[i] === "en-ie") {{ to = "{base}en-gb/"; break; }}
      if (langs[i].indexOf("en") === 0) break;
    }}"""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="robots" content="noindex">
  <title>Harbor Desk</title>
  <link rel="canonical" href="{ORIGIN}{target}">
  <meta http-equiv="refresh" content="0; url={target}">
  <script>
    var to = "{target}";{pick}
    location.replace(to + location.hash);
  </script>
</head>
<body>
  <p><a href="{target}">Harbor Desk</a></p>
</body>
</html>
"""


def word_count(html: str) -> int:
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return len(re.findall(r"[^\W_][\w'’.,$%-]*", text))


def sitemap() -> str:
    entries = []
    for page in PAGES:
        if not page.index:
            continue
        alts = "".join(
            f'\n    <xhtml:link rel="alternate" hreflang="{l.code}" href="{ORIGIN}{url(page.path, l, STAGING)}"/>' for l in LANGS
        )
        for lang in LANGS:
            entries.append(
                f"  <url>\n    <loc>{ORIGIN}{url(page.path, lang, STAGING)}</loc>\n    <lastmod>{LASTMOD}</lastmod>{alts}\n  </url>"
            )
    body = "\n".join(entries)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        f"{body}\n</urlset>\n"
    )


DE_META: dict = json.loads((SRC / "de-de" / "meta.json").read_text())


def write(rel: str, html: str) -> None:
    out = ROOT / rel / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)


def build(variant: Variant) -> None:
    global _variant
    _variant = variant
    for lang in LANGS:
        for page in PAGES:
            write(f"{variant.prefix}{lang.prefix}{page.path}", render(page, lang))
            print(f"{url(page.path, lang):82} {word_count(fragment(page, lang)):5} words")
    for old, lang in RETIRED_PREFIXES.items() if variant.public else ():
        for page in PAGES:
            if old == "" and page.path == "":
                continue
            write(f"{variant.prefix}{old}{page.path}", redirect(url(page.path, lang)))
    write(variant.prefix, redirect(url("", SOURCE), pick_language=True))


def main() -> None:
    for variant in VARIANTS:
        build(variant)
    (ROOT / "sitemap.xml").write_text(sitemap())
    (ROOT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nDisallow: {BASE}/dev/\n\nSitemap: {ORIGIN}{asset('sitemap.xml')}\n"
    )


if __name__ == "__main__":
    main()
