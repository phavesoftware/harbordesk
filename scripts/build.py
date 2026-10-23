"""Builds the static Harbor Desk site from src/ fragments.

Run from the repo root: python3 scripts/build.py
Every page is written as plain HTML (folder/index.html), so the published
site needs no JavaScript and no build step on GitHub Pages.

Three languages: US English at the root (the source, src/*.html), Canadian
English under en-ca/ (derived from the source by scripts/en_ca.py, or taken
from src/en-ca/<file> where a page needs its own words) and Canadian French
under fr-ca/ (src/fr-ca/*.html, titles and descriptions in src/fr-ca/meta.json).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, replace
from html import escape
from pathlib import Path

import en_ca

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
BASE = "/harbordesk"
ORIGIN = "https://phavesoftware.github.io"
SITE_NAME = "Harbor Desk"
LASTMOD = "2026-10-22"
TAG = (
    '<script async src="https://harbor-desk.phvtrack.dev/bambino.js" '
    'data-phv-tenant="harbor-desk" '
    'data-phv-key="phv_wk_PFesdDymtxDz-Sfh6mE4epN-Ikw8pBww" '
    'data-phv-consent="opt_out"></script>'
)


@dataclass(frozen=True)
class Lang:
    code: str  # BCP 47, as html lang and hreflang
    prefix: str  # "" for the source, else "en-ca/"
    label: str  # the picker's name, in the language itself
    short: str  # the picker's closed face
    flag: str  # assets/flags/<flag>.svg
    og_suffix: str  # "" or "-fr": which social card set the pages use


LANGS = [
    Lang("en-US", "", "English (US)", "EN", "us", ""),
    Lang("en-CA", "en-ca/", "English (Canada)", "EN", "ca", ""),
    Lang("fr-CA", "fr-ca/", "Français (Canada)", "FR", "ca", "-fr"),
]
SOURCE = LANGS[0]

# Every string the page chrome writes, per language. en-CA is derived.
CHROME_EN = {
    "skip": "Skip to content",
    "logo_alt": "Harbor Desk logo",
    "nav_label": "Main",
    "nav": {"product": "Product", "customers": "Customers", "pricing": "Pricing",
            "resources": "Resources", "events": "Events", "about": "About"},
    "book": "Book a demo",
    "lang_label": "Language",
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
                        ("privacy/", "Privacy policy"), ("terms/", "Terms of use")],
    },
    "rights": "&copy; 2026 Harbor Desk, Inc. All rights reserved.",
    "fictional": "Harbor Desk is a fictional company used for product demos.",
}
CHROME_FR = {
    "skip": "Aller au contenu",
    "logo_alt": "Logo Harbor Desk",
    "nav_label": "Principal",
    "nav": {"product": "Produit", "customers": "Clients", "pricing": "Tarifs",
            "resources": "Ressources", "events": "Événements", "about": "À propos"},
    "book": "Réserver une démo",
    "lang_label": "Langue",
    "tagline": "Voyez venir l'attrition. Agissez avant le renouvellement.",
    "country": "États-Unis",
    "cols": {
        "Produit": [("product/", "Aperçu du produit"), ("product/#health-scores", "Health Scores"),
                    ("product/#playbooks", "Playbooks"), ("product/#ebr-builder", "EBR Builder"),
                    ("pricing/", "Tarifs")],
        "Entreprise": [("about/", "À propos"), ("customers/", "Clients"), ("resources/", "Ressources"),
                       ("events/", "Événements"),
                       ("events/churn-risk-teardown-workshop/", "Atelier « Décortiquer le risque d'attrition »"),
                       ("brand/", "Marque et presse"), ("", "Accueil")],
        "Pour commencer": [("demo/", "Réserver une démo"), ("demo/#talk-to-sales", "Parler aux ventes"),
                           ("privacy/", "Politique de confidentialité"), ("terms/", "Conditions d'utilisation")],
    },
    "rights": "&copy; 2026 Harbor Desk, Inc. Tous droits réservés.",
    "fictional": "Harbor Desk est une entreprise fictive utilisée pour des démonstrations de produit.",
}


def _en_ca_chrome(chrome: dict) -> dict:
    out = json.loads(json.dumps(chrome))
    out["nav"] = {k: en_ca.text(v) for k, v in out["nav"].items()}
    out["cols"] = {en_ca.text(t): [(p, en_ca.text(l)) for p, l in links] for t, links in out["cols"].items()}
    for key in ("tagline", "book"):
        out[key] = en_ca.text(out[key])
    return out


CHROME = {"en-US": CHROME_EN, "en-CA": _en_ca_chrome(CHROME_EN), "fr-CA": CHROME_FR}

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
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD" if lang is SOURCE else "CAD",
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
    source: str  # fragment file under src/ (and src/fr-ca/)
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
    Page("brand/", "brand.html", "Brand and press kit · Harbor Desk",
         "Harbor Desk logo files, color palette with hex values, fonts, and the rules for how we write: tone, words we avoid and product name capitalization.", None),
    Page("privacy/", "privacy.html", "Privacy policy · Harbor Desk",
         "How Harbor Desk collects, uses and protects information about visitors to this website, the cookies it sets, and how to opt out.", None),
    Page("terms/", "terms.html", "Terms of use · Harbor Desk",
         "The terms that govern use of the Harbor Desk website.", None),
]

HEADER_NAV = ["product", "customers", "pricing", "resources", "events", "about"]
NAV_PATHS = {key: f"{key}/" for key in HEADER_NAV}

# A {{base}} link to one of these stays at the site root in every language.
SHARED_FILES = re.compile(r"^/(assets/|favicon|apple-touch-icon|sitemap\.xml|robots\.txt)")


def url(path: str, lang: Lang = SOURCE) -> str:
    return f"{BASE}/{lang.prefix}{path}"


def localize_links(body: str, lang: Lang) -> str:
    def swap(m: re.Match[str]) -> str:
        rest = m.group(1) or ""
        if SHARED_FILES.match(rest):
            return f"{BASE}{rest}"
        return f"{BASE}/{lang.prefix}{rest.lstrip('/')}"

    return re.sub(r"\{\{base\}\}(/[^\"'\s<>)]*)?", swap, body)


def page_for(page: Page, lang: Lang) -> Page:
    """The page's metadata in a language."""
    if lang.code == "en-CA":
        return replace(page, title=en_ca.text(page.title), description=en_ca.text(page.description))
    if lang.code == "fr-CA":
        meta = FR_META[page.path]
        return replace(page, title=meta["title"], description=meta["description"], og_alt=meta["og_alt"])
    return page


def fragment(page: Page, lang: Lang) -> str:
    if lang.code == "fr-CA":
        return (SRC / "fr-ca" / page.source).read_text()
    if lang.code == "en-CA":
        own = SRC / "en-ca" / page.source
        return own.read_text() if own.exists() else en_ca.html((SRC / page.source).read_text())
    return (SRC / page.source).read_text()


def flag(lang: Lang) -> str:
    return f'<img src="{url(f"assets/flags/{lang.flag}.svg")}" alt="" class="flag" width="20" height="14">'


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
    <a href="{url("", lang)}" class="logo-link"><img src="{url("assets/logo.svg")}" alt="{chrome["logo_alt"]}" class="logo" width="172" height="36"></a>
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
        <img src="{url("assets/logo-white.svg")}" alt="{chrome["logo_alt"]}" class="footer-logo" width="143" height="30">
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
        "url": f"{ORIGIN}{url('', lang)}",
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
    canonical = f"{ORIGIN}{url(page.path, lang)}"
    og_image = f"{ORIGIN}{url(f'assets/{page.og_image}{lang.og_suffix}.png')}"
    og_alt = escape(page.og_alt)
    ld = [organization(lang)]
    if page.workshop:
        ld.append(workshop_events(lang, FR_META["_event"] if lang.code == "fr-CA" else WORKSHOP_EN))
    page_ld = "".join(f'\n  <script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld)
    title = escape(page.title)
    desc = escape(page.description)
    robots = "" if page.index else '\n  <meta name="robots" content="noindex">'
    og_locale = lang.code.replace("-", "_")
    others = "".join(f'\n  <meta property="og:locale:alternate" content="{l.code.replace("-", "_")}">' for l in LANGS if l is not lang)
    return f"""<head>
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
  <link rel="icon" href="{url("favicon.ico")}" sizes="any">
  <link rel="icon" href="{url("favicon.svg")}" type="image/svg+xml">
  <link rel="apple-touch-icon" href="{url("apple-touch-icon.png")}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;family=Manrope:wght@700;800&amp;display=swap">
  <link rel="stylesheet" href="{url("assets/site.css")}">{page_ld}
  <!-- PHAVE SITE TAG GOES HERE -->
  {TAG}
</head>"""


def render(page: Page, lang: Lang) -> str:
    body = localize_links(fragment(page, lang), lang)
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
            f'\n    <xhtml:link rel="alternate" hreflang="{l.code}" href="{ORIGIN}{url(page.path, l)}"/>' for l in LANGS
        )
        for lang in LANGS:
            entries.append(
                f"  <url>\n    <loc>{ORIGIN}{url(page.path, lang)}</loc>\n    <lastmod>{LASTMOD}</lastmod>{alts}\n  </url>"
            )
    body = "\n".join(entries)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        f"{body}\n</urlset>\n"
    )


FR_META: dict = json.loads((SRC / "fr-ca" / "meta.json").read_text())


def main() -> None:
    for lang in LANGS:
        for page in PAGES:
            out = ROOT / lang.prefix / page.path / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(render(page, lang))
            words = word_count(fragment(page, lang))
            print(f"{url(page.path, lang):76} {words:5} words")

    (ROOT / "sitemap.xml").write_text(sitemap())
    (ROOT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {ORIGIN}{url('sitemap.xml')}\n"
    )


if __name__ == "__main__":
    main()
