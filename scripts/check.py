"""Checks the built site against its content and SEO requirements.

Run from the repo root after build.py: python3 scripts/check.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "/harbordesk"
MAIN_PAGES = ["", "product/", "customers/", "pricing/", "resources/", "about/", "demo/", "brand/", "privacy/", "terms/"]
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
        (r'<meta property="og:image" content="https://[^"]+og-image.png">', "og:image"),
        (r'<meta property="og:site_name" content="Harbor Desk">', "og:site_name"),
        (r'<img src="/harbordesk/assets/logo.svg" alt="Harbor Desk logo" class="logo"', "header logo img"),
        (r'<link rel="icon" href="[^"]+favicon.ico"', "favicon"),
        (r'<link rel="apple-touch-icon"', "apple-touch-icon"),
        (r"<header class=\"site-header\">", "header"),
        (r"<main id=\"main\">", "main"),
        (r"<footer class=\"site-footer\">", "footer"),
    ]:
        if not re.search(pattern, html):
            problems.append(f"{rel}: missing {label}")

    if len(re.findall(r"<h1[\s>]", html)) != 1:
        problems.append(f"{rel}: needs exactly one <h1>")
    if html.count("bambino.js") != 1:
        problems.append(f"{rel}: Phave tag must appear exactly once")

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
