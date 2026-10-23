"""Checks the built site against its content and SEO requirements.

Run from the repo root after build.py: python3 scripts/check.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import en_ca  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BASE = "/harbordesk"
ORIGIN = "https://phavesoftware.github.io"
PREFIXES = {"en-US": "", "en-CA": "en-ca/", "fr-CA": "fr-ca/"}
MAIN_PAGES = ["", "product/", "customers/", "pricing/", "resources/", "about/", "demo/", "events/", "events/churn-risk-teardown-workshop/", "brand/", "privacy/", "terms/"]
UK_SPELLINGS = r"\b(colour|colours|organisation|organise|prioritise|recognise|analyse|behaviour|favourite|centre|licence|catalogue)\b"
US_SPELLINGS = r"\b(" + "|".join(en_ca.SPELLINGS) + r")\b"
AVOID = r"\b(unlock|seamless|revolutionary|game-changer|synergy|best-in-class|world-class|cutting-edge|start free trial)\b"
LOGO_ALT = {"en-US": "Harbor Desk logo", "en-CA": "Harbor Desk logo", "fr-CA": "Logo Harbor Desk"}
WORKSHOP_WORDS = {
    "en": {"seats": "Few seats left", "reserve": "Reserve a seat",
           "closing": "Harbor Desk helps your team act before renewal becomes a rescue.",
           "eyebrow": '<p class="tagline">Churn-risk teardown workshop</p>',
           "h1": "<h1>See the accounts at risk while there is still time to talk</h1>"},
    "fr": {"seats": "Plus que quelques places", "reserve": "Réserver une place",
           "closing": "Harbor Desk aide votre équipe à agir avant que le renouvellement devienne un sauvetage."},
}

problems: list[str] = []
pages = sorted(p for p in ROOT.rglob("index.html") if ".tools" not in p.parts and ".worktrees" not in p.parts)
titles: dict[tuple[str, str], Path] = {}
counts = {code: 0 for code in PREFIXES}


def lang_of(html: str) -> str:
    m = re.search(r'<html lang="([^"]+)">', html)
    return m.group(1) if m else "?"


for page in pages:
    rel = page.relative_to(ROOT)
    html = page.read_text()
    lang = lang_of(html)
    if lang not in PREFIXES:
        problems.append(f"{rel}: unknown html lang {lang}")
        continue
    counts[lang] += 1
    prefix = PREFIXES[lang]
    if not str(rel).startswith(prefix):
        problems.append(f"{rel}: lang {lang} outside {prefix or 'the root'}")
    visible = re.sub(r"<head>.*?</head>|<script.*?</script>|<code\b.*?</code>|<pre\b.*?</pre>", " ", html, flags=re.S)
    readable_attrs = " ".join(m.group(2) for m in en_ca._READABLE_ATTR.finditer(visible))
    visible = re.sub(r"<[^>]+>", " ", visible) + " " + readable_attrs

    for pattern, label in [
        (r"<title>[^<]+</title>", "title"),
        (r'<meta name="description" content="[^"]+">', "meta description"),
        (r'<link rel="canonical" href="https://[^"]+">', "canonical"),
        (r'<meta property="og:title"', "og:title"),
        (r'<meta property="og:description"', "og:description"),
        (r'<meta property="og:image" content="https://[^"]+/og-[a-z-]+\.png">', "og:image"),
        (r'<meta property="og:site_name" content="Harbor Desk">', "og:site_name"),
        (rf'<img src="/harbordesk/assets/logo.svg" alt="{LOGO_ALT[lang]}" class="logo"', "header logo img"),
        (r'<link rel="icon" href="[^"]+favicon.ico"', "favicon"),
        (r'<link rel="apple-touch-icon"', "apple-touch-icon"),
        (r"<header class=\"site-header\">", "header"),
        (r"<main id=\"main\">", "main"),
        (r"<footer class=\"site-footer\">", "footer"),
        (r'<details class="lang-picker">', "language picker"),
        (r'<link rel="alternate" hreflang="x-default"', "x-default alternate"),
        (r"<!-- PHAVE SITE TAG GOES HERE -->\s*<script async src=\"https://harbor-desk.phvtrack.dev/bambino.js\"", "site tag comment"),
    ]:
        if not re.search(pattern, html):
            problems.append(f"{rel}: missing {label}")
    if len(re.findall(r'<link rel="alternate" hreflang="(en-US|en-CA|fr-CA)"', html)) != 3:
        problems.append(f"{rel}: needs three hreflang alternates")
    if len(re.findall(r'<li><a href="/harbordesk/[^"]*" hreflang=', html)) != 3:
        problems.append(f"{rel}: language picker needs three links")

    if len(re.findall(r"<h1[\s>]", html)) != 1:
        problems.append(f"{rel}: needs exactly one <h1>")
    # The form embed carries its own copy of the tag beside the form.
    expected_tags = 2 if 'data-phave-form="' in html else 1
    if html.count("bambino.js") != expected_tags:
        problems.append(f"{rel}: Phave tag must appear {expected_tags} time(s)")

    title = re.search(r"<title>([^<]+)</title>", html)
    if title:
        key = (lang, title.group(1))
        if key in titles:
            problems.append(f"{rel}: title duplicates {titles[key]}")
        titles[key] = rel

    hrefs = set(re.findall(r'href="(/harbordesk/[^"#]*)', html))
    for href in hrefs:
        target = ROOT / href[len(BASE) + 1:]
        if href.endswith("/"):
            target = target / "index.html"
        if not target.exists():
            problems.append(f"{rel}: broken link {href}")
    for main in MAIN_PAGES:
        if f"{BASE}/{prefix}{main}" not in hrefs:
            problems.append(f"{rel}: no link to {BASE}/{prefix}{main}")

    if lang == "en-US" and re.search(UK_SPELLINGS, visible, re.I):
        problems.append(f"{rel}: UK spelling {re.search(UK_SPELLINGS, visible, re.I).group(0)}")
    if lang == "en-CA" and re.search(US_SPELLINGS, visible, re.I):
        problems.append(f"{rel}: US spelling {re.search(US_SPELLINGS, visible, re.I).group(0)}")
    if lang.startswith("en") and "brand" not in rel.parts and re.search(AVOID, visible, re.I):
        problems.append(f"{rel}: avoided word {re.search(AVOID, visible, re.I).group(0)}")
    if lang != "en-US" and re.search(r"US\$|US dollars|dollars US|\$18,000|\$42,000|\$90,000", visible):
        problems.append(f"{rel}: US dollar price on a Canadian page")
    if "\u2014" in visible:
        problems.append(f"{rel}: em dash in copy")

for lang, prefix in PREFIXES.items():
    words = WORKSHOP_WORDS[lang[:2]]
    workshop = (ROOT / prefix / "events/churn-risk-teardown-workshop/index.html").read_text()
    needles = [
        (f'<link rel="canonical" href="{ORIGIN}{BASE}/{prefix}events/churn-risk-teardown-workshop/">', "canonical"),
        ("og-workshop", "og:image"),
        ('<section id="reserve"', "reserve section"),
        ("<!-- PHAVE FORM EMBED CODE GOES HERE -->", "form embed comment"),
        ('<div id="workshop-registration-form"', "form embed target"),
        ('<div data-phave-form="f0hohdpb03g6u9l"></div>', "Phave form element"),
        (words["seats"], "few seats badge"),
        (words["closing"], "closing line"),
    ]
    needles += [(words[k], k) for k in ("eyebrow", "h1") if k in words]
    for needle, label in needles:
        if needle not in workshop:
            problems.append(f"{prefix}workshop: missing {label}")
    if workshop.count(f'href="#reserve">{words["reserve"]}</a>') != 2:
        problems.append(f"{prefix}workshop: needs exactly two {words['reserve']} buttons to #reserve")
    thanks = (ROOT / prefix / "events/churn-risk-teardown-workshop/thanks/index.html").read_text()
    if '<meta name="robots" content="noindex">' not in thanks:
        problems.append(f"{prefix}workshop thanks: missing noindex")
    for name in ["index.html", "resources/index.html"]:
        main = (ROOT / prefix / name).read_text().split("<main", 1)[1].split("</main>")[0]
        if f'href="{BASE}/{prefix}events/churn-risk-teardown-workshop/"' not in main:
            problems.append(f"{prefix}{name}: no workshop banner in main")

sitemap = (ROOT / "sitemap.xml").read_text()
for prefix in PREFIXES.values():
    for path in ["", "events/", "events/churn-risk-teardown-workshop/"]:
        if f"<loc>{ORIGIN}{BASE}/{prefix}{path}</loc>" not in sitemap:
            problems.append(f"sitemap: missing {prefix}{path}")
if "/thanks/" in sitemap:
    problems.append("sitemap: lists a thanks page")
if len(set(counts.values())) != 1:
    problems.append(f"languages have different page counts: {counts}")

css = (ROOT / "assets/site.css").read_text()
outside_root = re.sub(r":root\s*\{.*?\}", "", css, count=1, flags=re.S)
stray = re.findall(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(", outside_root)
if stray:
    problems.append(f"assets/site.css: colors outside :root: {sorted(set(stray))}")
if re.search(r'style="', "".join(p.read_text() for p in pages)):
    problems.append("inline style attribute found")

for required in ["assets/logo.svg", "assets/logo.png", "assets/logo-white.svg", "assets/logo-mark.svg",
                 "assets/logo-mark.png", "assets/og-image.png", "assets/og-image-fr.png",
                 "assets/og-workshop.png", "assets/og-workshop-fr.png", "assets/flags/us.svg",
                 "assets/flags/ca.svg", "favicon.ico", "apple-touch-icon.png", "sitemap.xml", "robots.txt"]:
    if not (ROOT / required).exists():
        problems.append(f"missing file {required}")

print(f"checked {len(pages)} pages: {counts}")
for problem in problems:
    print("FAIL", problem)
sys.exit(1 if problems else 0)
