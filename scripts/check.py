"""Checks the built site against its content and SEO requirements.

Run from the repo root after build.py: python3 scripts/check.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "/harbordesk"
MAIN_PAGES = ["", "product/", "customers/", "pricing/", "resources/", "about/", "demo/", "events/", "events/churn-risk-teardown-workshop/", "brand/", "privacy/", "terms/"]
UK_SPELLINGS = r"\b(colour|colours|organisation|organise|prioritise|recognise|analyse|behaviour|favourite|centre|licence|catalogue)\b"
AVOID = r"\b(unlock|seamless|revolutionary|game-changer|synergy|best-in-class|world-class|cutting-edge|start free trial)\b"

problems: list[str] = []
pages = sorted(p for p in ROOT.rglob("index.html") if ".tools" not in p.parts)
titles: dict[str, Path] = {}

for page in pages:
    rel = page.relative_to(ROOT)
    html = page.read_text()
    visible = re.sub(r"<head>.*?</head>|<script.*?</script>", " ", html, flags=re.S)

    for pattern, label in [
        (r"<title>[^<]+</title>", "title"),
        (r'<meta name="description" content="[^"]+">', "meta description"),
        (r'<link rel="canonical" href="https://[^"]+">', "canonical"),
        (r'<meta property="og:title"', "og:title"),
        (r'<meta property="og:description"', "og:description"),
        (r'<meta property="og:image" content="https://[^"]+/og-[a-z]+\.png">', "og:image"),
        (r'<meta property="og:site_name" content="Harbor Desk">', "og:site_name"),
        (r'<img src="/harbordesk/assets/logo.svg" alt="Harbor Desk logo" class="logo"', "header logo img"),
        (r'<link rel="icon" href="[^"]+favicon.ico"', "favicon"),
        (r'<link rel="apple-touch-icon"', "apple-touch-icon"),
        (r"<header class=\"site-header\">", "header"),
        (r"<main id=\"main\">", "main"),
        (r"<footer class=\"site-footer\">", "footer"),
        (r"<!-- PHAVE SITE TAG GOES HERE -->\s*<script async src=\"https://harbor-desk.phvtrack.dev/bambino.js\"", "site tag comment"),
    ]:
        if not re.search(pattern, html):
            problems.append(f"{rel}: missing {label}")

    if len(re.findall(r"<h1[\s>]", html)) != 1:
        problems.append(f"{rel}: needs exactly one <h1>")
    # The form embed carries its own copy of the tag beside the form.
    expected_tags = 2 if 'data-phave-form="' in html else 1
    if html.count("bambino.js") != expected_tags:
        problems.append(f"{rel}: Phave tag must appear {expected_tags} time(s)")

    title = re.search(r"<title>([^<]+)</title>", html)
    if title:
        if title.group(1) in titles:
            problems.append(f"{rel}: title duplicates {titles[title.group(1)]}")
        titles[title.group(1)] = rel

    hrefs = set(re.findall(r'href="(/harbordesk/[^"#]*)', html))
    for href in hrefs:
        target = ROOT / href[len(BASE) + 1:]
        if href.endswith("/"):
            target = target / "index.html"
        if not target.exists():
            problems.append(f"{rel}: broken link {href}")
    for main in MAIN_PAGES:
        if f"{BASE}/{main}" not in hrefs:
            problems.append(f"{rel}: no link to {BASE}/{main}")

    if re.search(UK_SPELLINGS, visible, re.I):
        problems.append(f"{rel}: UK spelling {re.search(UK_SPELLINGS, visible, re.I).group(0)}")
    if rel.parts[0] != "brand" and re.search(AVOID, visible, re.I):
        problems.append(f"{rel}: avoided word {re.search(AVOID, visible, re.I).group(0)}")

workshop = (ROOT / "events/churn-risk-teardown-workshop/index.html").read_text()
for needle, label in [
    ('<link rel="canonical" href="https://phavesoftware.github.io/harbordesk/events/churn-risk-teardown-workshop/">', "workshop canonical"),
    ('og-workshop.png', "workshop og:image"),
    ('<p class="tagline">Churn-risk teardown workshop</p>', "workshop eyebrow"),
    ("<h1>See the accounts at risk while there is still time to talk</h1>", "workshop h1"),
    ('<section id="reserve"', "reserve section"),
    ("<!-- PHAVE FORM EMBED CODE GOES HERE -->", "form embed comment"),
    ('<div id="workshop-registration-form"', "form embed target"),
    ('<div data-phave-form="f0hohdpb03g6u9l"></div>', "Phave form element"),
    ("Few seats left", "few seats badge"),
    ("Harbor Desk helps your team act before renewal becomes a rescue.", "closing line"),
]:
    if needle not in workshop:
        problems.append(f"workshop: missing {label}")
if workshop.count('href="#reserve">Reserve a seat</a>') != 2:
    problems.append("workshop: needs exactly two Reserve a seat buttons to #reserve")
thanks = (ROOT / "events/churn-risk-teardown-workshop/thanks/index.html").read_text()
if '<meta name="robots" content="noindex">' not in thanks:
    problems.append("workshop thanks: missing noindex")
sitemap = (ROOT / "sitemap.xml").read_text()
for path in ["events/", "events/churn-risk-teardown-workshop/"]:
    if f"{BASE}/{path}</loc>" not in sitemap:
        problems.append(f"sitemap: missing {path}")
if "/thanks/" in sitemap:
    problems.append("sitemap: lists a thanks page")
for name in ["index.html", "resources/index.html"]:
    if f'href="{BASE}/events/churn-risk-teardown-workshop/"' not in (ROOT / name).read_text().split("<main", 1)[1].split("</main>")[0]:
        problems.append(f"{name}: no workshop banner in main")

css = (ROOT / "assets/site.css").read_text()
outside_root = re.sub(r":root\s*\{.*?\}", "", css, count=1, flags=re.S)
stray = re.findall(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(", outside_root)
if stray:
    problems.append(f"assets/site.css: colors outside :root: {sorted(set(stray))}")
if re.search(r'style="', "".join(p.read_text() for p in pages)):
    problems.append("inline style attribute found")

for required in ["assets/logo.svg", "assets/logo.png", "assets/logo-white.svg", "assets/logo-mark.svg",
                 "assets/logo-mark.png", "assets/og-image.png", "favicon.ico", "apple-touch-icon.png",
                 "sitemap.xml", "robots.txt"]:
    if not (ROOT / required).exists():
        problems.append(f"missing file {required}")

print(f"checked {len(pages)} pages")
for problem in problems:
    print("FAIL", problem)
sys.exit(1 if problems else 0)
