"""Builds the static Harbor Desk site from src/ fragments.

Run from the repo root: python3 scripts/build.py
Every page is written as plain HTML (folder/index.html), so the published
site needs no JavaScript and no build step on GitHub Pages.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html import escape
from pathlib import Path

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


WORKSHOP_SESSIONS = [
    # (ISO start, ISO end) in Pacific Time; ET is three hours later.
    ("2026-11-10T09:00:00-08:00", "2026-11-10T10:00:00-08:00"),
    ("2026-11-18T11:00:00-08:00", "2026-11-18T12:00:00-08:00"),
    ("2026-12-03T08:00:00-08:00", "2026-12-03T09:00:00-08:00"),
]
WORKSHOP_URL = f"{ORIGIN}{BASE}/events/churn-risk-teardown-workshop/"
WORKSHOP_EVENTS = [
    {
        "@context": "https://schema.org",
        "@type": "Event",
        "name": "Churn-risk teardown workshop",
        "description": "A 60-minute live working session for customer success leaders: how your team flags churn risk today, where accounts slip through before renewal, and which customer conversations should happen sooner.",
        "startDate": start,
        "endDate": end,
        "eventAttendanceMode": "https://schema.org/OnlineEventAttendanceMode",
        "eventStatus": "https://schema.org/EventScheduled",
        "location": {"@type": "VirtualLocation", "url": WORKSHOP_URL},
        "image": f"{ORIGIN}{BASE}/assets/og-workshop.png",
        "maximumAttendeeCapacity": 8,
        "isAccessibleForFree": True,
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD", "url": f"{WORKSHOP_URL}#reserve", "availability": "https://schema.org/LimitedAvailability"},
        "organizer": {"@type": "Organization", "name": "Harbor Desk", "url": f"{ORIGIN}{BASE}/"},
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
    source: str  # fragment file under src/
    title: str
    description: str
    nav: str | None = None  # header nav key this page highlights
    kind: str = "website"
    index: bool = True
    og_image: str = "assets/og-image.png"
    og_alt: str = "Harbor Desk logo with the line: See churn coming. Act before renewal."
    json_ld: dict | list | None = None  # page-specific structured data


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
    Page("events/churn-risk-teardown-workshop/", "event-churn-risk-teardown.html",
         "Churn-risk teardown workshop: a free 60-minute working session · Harbor Desk",
         "A free 60-minute live session on Zoom for CS leaders. Work through how your team spots churn risk, where accounts slip before renewal, and which conversations to have sooner. 8 companies per session.",
         "events", og_image="assets/og-workshop.png",
         og_alt="Harbor Desk logo with the title: Churn-risk teardown workshop. See the accounts at risk while there is still time to talk.",
         json_ld=WORKSHOP_EVENTS),
    Page("events/churn-risk-teardown-workshop/thanks/", "event-churn-risk-teardown-thanks.html",
         "Thanks, you're registered: Churn-risk teardown workshop · Harbor Desk",
         "You're registered for the Harbor Desk Churn-risk teardown workshop. Look out for a calendar invite and a short pre-work email.",
         "events", og_image="assets/og-workshop.png",
         og_alt="Harbor Desk logo with the title: Churn-risk teardown workshop.", index=False),
    Page("brand/", "brand.html", "Brand and press kit · Harbor Desk",
         "Harbor Desk logo files, color palette with hex values, fonts, and the rules for how we write: tone, words we avoid and product name capitalization.", None),
    Page("privacy/", "privacy.html", "Privacy policy · Harbor Desk",
         "How Harbor Desk collects, uses and protects information about visitors to this website, the cookies it sets, and how to opt out.", None),
    Page("terms/", "terms.html", "Terms of use · Harbor Desk",
         "The terms that govern use of the Harbor Desk website.", None),
]

HEADER_NAV = [
    ("product", "product/", "Product"),
    ("customers", "customers/", "Customers"),
    ("pricing", "pricing/", "Pricing"),
    ("resources", "resources/", "Resources"),
    ("events", "events/", "Events"),
    ("about", "about/", "About"),
]


def url(path: str) -> str:
    return f"{BASE}/{path}"


def header(page: Page) -> str:
    items = []
    for key, path, label in HEADER_NAV:
        current = ' aria-current="page"' if page.nav == key else ""
        items.append(f'<li><a href="{url(path)}"{current}>{label}</a></li>')
    demo_current = ' aria-current="page"' if page.nav == "demo" else ""
    items.append(f'<li><a class="btn btn-primary" href="{url("demo/")}"{demo_current}>Book a demo</a></li>')
    nav_items = "\n        ".join(items)
    return f"""<header class="site-header">
  <div class="wrap">
    <a href="{url("")}" class="logo-link"><img src="{url("assets/logo.svg")}" alt="Harbor Desk logo" class="logo" width="172" height="36"></a>
    <nav class="nav" aria-label="Main">
      <ul>
        {nav_items}
      </ul>
    </nav>
  </div>
</header>"""


def footer() -> str:
    def col(title: str, links: list[tuple[str, str]]) -> str:
        lis = "\n".join(f'          <li><a href="{url(p)}">{label}</a></li>' for p, label in links)
        return f"""      <nav aria-label="{title}">
        <h2>{title}</h2>
        <ul>
{lis}
        </ul>
      </nav>"""

    return f"""<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div>
        <img src="{url("assets/logo-white.svg")}" alt="Harbor Desk logo" class="footer-logo" width="143" height="30">
        <p>See churn coming. Act before renewal.</p>
        <address>Harbor Desk, Inc.<br>220 Wharf Street<br>Portland, ME 04101<br>United States</address>
      </div>
{col("Product", [("product/", "Product overview"), ("product/#health-scores", "Health Scores"), ("product/#playbooks", "Playbooks"), ("product/#ebr-builder", "EBR Builder"), ("pricing/", "Pricing")])}
{col("Company", [("about/", "About"), ("customers/", "Customers"), ("resources/", "Resources"), ("events/", "Events"), ("events/churn-risk-teardown-workshop/", "Churn-risk teardown workshop"), ("brand/", "Brand and press"), ("", "Home")])}
{col("Get started", [("demo/", "Book a demo"), ("demo/#talk-to-sales", "Talk to sales"), ("privacy/", "Privacy policy"), ("terms/", "Terms of use")])}
    </div>
    <div class="footer-base">
      <span>&copy; 2026 Harbor Desk, Inc. All rights reserved.</span>
      <span>Harbor Desk is a fictional company used for product demos.</span>
    </div>
  </div>
</footer>"""


ORGANIZATION = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "Harbor Desk",
    "legalName": "Harbor Desk, Inc.",
    "url": f"{ORIGIN}{BASE}/",
    "logo": f"{ORIGIN}{BASE}/assets/logo.png",
    "slogan": "See churn coming. Act before renewal.",
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


def head(page: Page) -> str:
    canonical = f"{ORIGIN}{url(page.path)}"
    og_image = f"{ORIGIN}{url(page.og_image)}"
    og_alt = escape(page.og_alt)
    page_ld = (
        f'\n  <script type="application/ld+json">{json.dumps(page.json_ld)}</script>'
        if page.json_ld else ""
    )
    title = escape(page.title)
    desc = escape(page.description)
    robots = "" if page.index else '\n  <meta name="robots" content="noindex">'
    return f"""<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{desc}">{robots}
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="{page.kind}">
  <meta property="og:site_name" content="{SITE_NAME}">
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
  <link rel="stylesheet" href="{url("assets/site.css")}">
  <script type="application/ld+json">{json.dumps(ORGANIZATION)}</script>{page_ld}
  <!-- PHAVE SITE TAG GOES HERE -->
  {TAG}
</head>"""


def render(page: Page) -> str:
    body = (SRC / page.source).read_text().replace("{{base}}", BASE)
    h1_count = len(re.findall(r"<h1[\s>]", body))
    if h1_count != 1:
        raise SystemExit(f"{page.source}: expected one <h1>, found {h1_count}")
    return f"""<!doctype html>
<html lang="en-US">
{head(page)}
<body>
<a class="skip" href="#main">Skip to content</a>
{header(page)}
<main id="main">
{body.strip()}
</main>
{footer()}
</body>
</html>
"""


def word_count(html: str) -> int:
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return len(re.findall(r"[A-Za-z0-9$%][\w'’.,$%-]*", text))


def main() -> None:
    for page in PAGES:
        out = ROOT / page.path / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(page))
        words = word_count((SRC / page.source).read_text())
        print(f"{url(page.path):70} {words:5} words")

    entries = "\n".join(
        f"  <url><loc>{ORIGIN}{url(p.path)}</loc><lastmod>{LASTMOD}</lastmod></url>"
        for p in PAGES if p.index
    )
    (ROOT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{entries}\n</urlset>\n'
    )
    (ROOT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {ORIGIN}{url('sitemap.xml')}\n"
    )


if __name__ == "__main__":
    main()
