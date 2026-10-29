"""Checks the built site against its content and SEO requirements.

Run from the repo root after build.py: python3 scripts/check.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402
import en_gb  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BASE = "/harbordesk"
ORIGIN = "https://phavesoftware.github.io"
LANG_PREFIXES = {lang.code: lang.prefix for lang in build.LANGS}
VARIANTS = {v.prefix: v for v in build.VARIANTS}
MAIN_PAGES = ["", "product/", "customers/", "pricing/", "resources/", "about/", "demo/", "events/", "events/churn-risk-teardown-workshop/", "brand/", "privacy/", "terms/"]
UK_SPELLINGS = r"\b(colour|colours|organisation|organise|prioritise|recognise|analyse|behaviour|favourite|centre|licence|catalogue)\b"
US_SPELLINGS = (r"\b(" + "|".join(re.escape(w) for w in en_gb.SPELLINGS) + r"|(" + "|".join(en_gb.ISE_STEMS)
                + r")iz(e|es|ed|ing|ation|ations))\b")
AVOID = r"\b(unlock|seamless|revolutionary|game-changer|synergy|best-in-class|world-class|cutting-edge|start free trial)\b"
LOGO_ALT = {code: build.CHROME[code]["logo_alt"] for code in LANG_PREFIXES}
WORKSHOP_WORDS = {
    "en-US": {"seats": "Few seats left", "reserve": "Reserve a seat",
              "closing": "Harbor Desk helps your team act before renewal becomes a rescue.",
              "eyebrow": '<p class="tagline">Churn-risk teardown workshop</p>',
              "h1": "<h1>See the accounts at risk while there is still time to talk</h1>"},
    "en-GB": {"seats": "Few seats left", "reserve": "Reserve a seat",
              "closing": "Harbor Desk helps your team act before renewal becomes a rescue.",
              "times": "5:00 to 6:00 pm GMT (9:00 to 10:00 am PT)"},
    "de-DE": {"seats": "Nur noch wenige Plätze", "reserve": "Platz reservieren",
              "closing": "Harbor Desk hilft Ihrem Team zu handeln, bevor die Verlängerung zur Rettungsaktion wird.",
              "times": "18:00 bis 19:00 Uhr MEZ"},
}
FOREIGN_MONEY = {
    "en-GB": r"\$\d|US\s+dollars",
    "de-DE": r"\$\d|US-Dollar|US\s+dollars|£",
}

problems: list[str] = []
pages = sorted(p for p in ROOT.rglob("index.html")
               if not {".tools", ".worktrees", "src", "node_modules"} & set(p.relative_to(ROOT).parts))
titles: dict[tuple[str, str, str], Path] = {}
counts: dict[tuple[str, str], int] = {(v, code): 0 for v in VARIANTS for code in LANG_PREFIXES}


def lang_of(html: str) -> str:
    m = re.search(r'<html lang="([^"]+)">', html)
    return m.group(1) if m else "?"


def target_exists(href: str) -> bool:
    target = ROOT / href[len(BASE) + 1:]
    if href.endswith("/"):
        target = target / "index.html"
    return target.exists()


def check_redirect(rel: Path, html: str) -> None:
    targets = set(re.findall(r'(/harbordesk/[^"#;\s]*/)"', html))
    if not targets:
        problems.append(f"{rel}: redirect without a target")
    for href in targets:
        if not target_exists(href) or "http-equiv" in (ROOT / href[len(BASE) + 1:] / "index.html").read_text():
            problems.append(f"{rel}: redirects to {href}, which is not a page")
    if '<meta name="robots" content="noindex">' not in html:
        problems.append(f"{rel}: redirect missing noindex")


def check_page(rel: Path, html: str) -> None:
    lang = lang_of(html)
    variant_prefix = "dev/" if str(rel).startswith("dev/") else ""
    variant = VARIANTS[variant_prefix]
    if lang not in LANG_PREFIXES:
        problems.append(f"{rel}: unknown html lang {lang}")
        return
    counts[(variant_prefix, lang)] += 1
    prefix = variant_prefix + LANG_PREFIXES[lang]
    if not str(rel).startswith(prefix):
        problems.append(f"{rel}: lang {lang} outside {prefix}")
    visible = re.sub(r"<head>.*?</head>|<script.*?</script>|<code\b.*?</code>|<pre\b.*?</pre>", " ", html, flags=re.S)
    readable_attrs = " ".join(m.group(2) for m in en_gb._READABLE_ATTR.finditer(visible))
    visible = re.sub(r"<[^>]+>", " ", visible) + " " + readable_attrs

    tag_src = re.escape(re.search(r'src="([^"]+)"', variant.tag).group(1))
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
        (rf"<!-- PHAVE SITE TAG GOES HERE -->\s*<script async src=\"{tag_src}\"", "site tag comment"),
    ]:
        if not re.search(pattern, html):
            problems.append(f"{rel}: missing {label}")
    if len(re.findall(r'<link rel="alternate" hreflang="(en-US|en-GB|de-DE)"', html)) != 3:
        problems.append(f"{rel}: needs three hreflang alternates")
    if len(re.findall(rf'<li><a href="/harbordesk/{variant_prefix}[^"]*" hreflang=', html)) != 3:
        problems.append(f"{rel}: language picker needs three links in its own variant")

    if len(re.findall(r"<h1[\s>]", html)) != 1:
        problems.append(f"{rel}: needs exactly one <h1>")
    # The form embed carries its own copy of the tag beside the form.
    expected_tags = 2 if 'data-phave-form="' in html else 1
    if html.count(variant.tag) != expected_tags or html.count("bambino.js") != expected_tags:
        problems.append(f"{rel}: its variant's Phave tag must appear {expected_tags} time(s), and no other tag")
    if "{{" in html:
        problems.append(f"{rel}: unfilled placeholder")
    if not variant.public:
        if '<meta name="robots" content="noindex">' not in html:
            problems.append(f"{rel}: dev page missing noindex")
        if 'class="dev-badge"' not in html:
            problems.append(f"{rel}: dev page missing its badge")
        if f'<link rel="canonical" href="{ORIGIN}{BASE}/{prefix[len(variant_prefix):]}' not in html:
            problems.append(f"{rel}: dev page canonical must be the staging page")
    elif 'class="dev-badge"' in html:
        problems.append(f"{rel}: staging page carries the dev badge")

    title = re.search(r"<title>([^<]+)</title>", html)
    if title:
        key = (variant_prefix, lang, title.group(1))
        if key in titles:
            problems.append(f"{rel}: title duplicates {titles[key]}")
        titles[key] = rel

    hrefs = set(re.findall(r'href="(/harbordesk/[^"#]*)', html))
    for href in hrefs:
        if not target_exists(href):
            problems.append(f"{rel}: broken link {href}")
        elif not href.startswith(f"{BASE}/{variant_prefix}") and not build.SHARED_FILES.match(href[len(BASE):]):
            problems.append(f"{rel}: link {href} leaves its variant")
    for main in MAIN_PAGES:
        if f"{BASE}/{prefix}{main}" not in hrefs:
            problems.append(f"{rel}: no link to {BASE}/{prefix}{main}")

    if lang == "en-US" and re.search(UK_SPELLINGS, visible, re.I):
        problems.append(f"{rel}: UK spelling {re.search(UK_SPELLINGS, visible, re.I).group(0)}")
    if lang == "en-GB" and re.search(US_SPELLINGS, visible, re.I):
        problems.append(f"{rel}: US spelling {re.search(US_SPELLINGS, visible, re.I).group(0)}")
    if lang.startswith("en") and "brand" not in rel.parts and re.search(AVOID, visible, re.I):
        problems.append(f"{rel}: avoided word {re.search(AVOID, visible, re.I).group(0)}")
    if lang in FOREIGN_MONEY and re.search(FOREIGN_MONEY[lang], visible):
        problems.append(f"{rel}: foreign price {re.search(FOREIGN_MONEY[lang], visible).group(0)}")
    if "\u2014" in visible:
        problems.append(f"{rel}: em dash in copy")


for page in pages:
    rel = page.relative_to(ROOT)
    html = page.read_text()
    if 'http-equiv="refresh"' in html:
        check_redirect(rel, html)
    else:
        check_page(rel, html)

for variant_prefix in VARIANTS:
    if not (ROOT / variant_prefix / "index.html").exists():
        problems.append(f"{variant_prefix or 'root'}: no landing redirect")
    for lang, lang_prefix in LANG_PREFIXES.items():
        prefix = variant_prefix + lang_prefix
        words = WORKSHOP_WORDS[lang]
        workshop = (ROOT / prefix / "events/churn-risk-teardown-workshop/index.html").read_text()
        needles = [
            (f'<link rel="canonical" href="{ORIGIN}{BASE}/{lang_prefix}events/churn-risk-teardown-workshop/">', "canonical"),
            ("og-workshop", "og:image"),
            ('<section id="reserve"', "reserve section"),
            ("<!-- PHAVE FORM EMBED CODE GOES HERE -->", "form embed comment"),
            ('<div id="workshop-registration-form"', "form embed target"),
            ('<div data-phave-form="f0hohdpb03g6u9l"></div>', "Phave form element"),
            (words["seats"], "few seats badge"),
            (words["closing"], "closing line"),
        ]
        needles += [(words[k], k) for k in ("eyebrow", "h1", "times") if k in words]
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
for prefix in LANG_PREFIXES.values():
    for path in ["", "events/", "events/churn-risk-teardown-workshop/"]:
        if f"<loc>{ORIGIN}{BASE}/{prefix}{path}</loc>" not in sitemap:
            problems.append(f"sitemap: missing {prefix}{path}")
for bad in ["/thanks/", f"{BASE}/dev/", "en-ca/", "fr-ca/"]:
    if bad in sitemap:
        problems.append(f"sitemap: lists {bad}")
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
                 "assets/logo-mark.png", "assets/og-image.png", "assets/og-image-de.png",
                 "assets/og-workshop.png", "assets/og-workshop-de.png", "assets/flags/us.svg",
                 "assets/flags/gb.svg", "assets/flags/de.svg", "favicon.ico", "apple-touch-icon.png",
                 "sitemap.xml", "robots.txt"]:
    if not (ROOT / required).exists():
        problems.append(f"missing file {required}")

print(f"checked {len(pages)} pages: {counts}")
for problem in problems:
    print("FAIL", problem)
sys.exit(1 if problems else 0)
