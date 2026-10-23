# Harbor Desk demo website

A fictional B2B SaaS company's marketing site, used to demo Phave: form
embeds, and the brand kit and knowledge base Maestro fills by reading a
website. Served by GitHub Pages at https://phavesoftware.github.io/harbordesk/.

Everything here is invented. Harbor Desk is a customer success platform
(Health Scores, Playbooks, EBR Builder) for B2B SaaS companies with 50 to
2,000 employees.

## Layout

- `src/*.html`: the content of each page (just what goes inside `<main>`).
- `scripts/build.py`: wraps each fragment in the shared head, header and
  footer, writes `<page>/index.html`, `sitemap.xml` and `robots.txt`. The
  page list, titles and descriptions live at the top of this file.
- `scripts/check.py`: checks the built pages (one h1, unique titles, meta
  and Open Graph tags, no broken internal links, every page links every main
  page, no colors outside `:root`, US spelling, no avoided words).
- `scripts/logo.mjs`: generates the logo SVGs, PNGs, favicon and the
  1200x630 social card into `assets/` and the repo root.
- `assets/site.css`: the one stylesheet. The palette and fonts are CSS
  variables in `:root`; nothing else declares a color.

The built HTML is committed, so Pages serves it as is with no build step.

## Editing

```sh
python3 scripts/build.py && python3 scripts/check.py
```

All links are root-absolute under `/harbordesk/` (`BASE` in `build.py`).
Write `{{base}}/pricing/` in a fragment and the build fills it in.

To regenerate the logo files, install the tools once into the gitignored
`.tools/` (`npm i opentype.js @resvg/resvg-js png-to-ico` there, plus the
Manrope 800 and Inter 400 TTFs in `.tools/fonts/`), then
`node scripts/logo.mjs`.

## Languages

Every page exists in three languages, switched from the flag picker in the
header (each page links to the same page in the others, with `hreflang`
alternates and a sitemap entry per language):

| Language | Path | Source |
|---|---|---|
| English (US) | `/harbordesk/` | `src/*.html`, the source of truth |
| English (Canada) | `/harbordesk/en-ca/` | derived at build time by `scripts/en_ca.py` (Canadian spellings, prices in Canadian dollars); put a file in `src/en-ca/` to override a page |
| Français (Canada) | `/harbordesk/fr-ca/` | `src/fr-ca/*.html`, titles and descriptions in `src/fr-ca/meta.json` |

Edit a US page and the Canadian English page follows on the next build. The
French page does not: update `src/fr-ca/` in the same change. Prices in
Canadian dollars are one table in `en_ca.py` (`PRICES`); the French pages
spell the same amounts. Links in a fragment written as `{{base}}/...` point
at the page's own language; `{{base}}/assets/...` stays shared.

The Phave form on the workshop page is the same form in every language, so
it shows in English on the French page.

## Phave wiring

- Subscription: **Harbor Desk** on staging (`stage.phave.dev`).
- Site: Self-hosted, host `phavesoftware.github.io`.
- The site tag is the last element in `<head>` on every page (`TAG` in
  `build.py`). Its attributes identify the account: copy it exactly, and
  rebuild if the key is rotated (Settings → Web → Write keys).
- `/harbordesk/demo/` has a `#demo-form` card holding a plain HTML form. A
  content slot with selector `#demo-form` and insert mode "Replace
  children" swaps in a Phave form. The plain form's fields carry no `name`,
  so submitting it sends nothing; it only navigates to `/demo/thanks/`.
- Every `<head>` carries `<!-- PHAVE SITE TAG GOES HERE -->` with the tag
  directly after it.
- `/harbordesk/events/churn-risk-teardown-workshop/` has a `#reserve`
  section with `<!-- PHAVE FORM EMBED CODE GOES HERE -->` and an empty
  `#workshop-registration-form`: paste the Phave form embed there, or point
  a content slot at that selector. Registrations should land on
  `/harbordesk/events/churn-risk-teardown-workshop/thanks/` (noindex, not
  in the nav or sitemap). The session dates live in `WORKSHOP_SESSIONS` in
  `build.py` (structured data) and in the two event fragments (visible text).
- `/harbordesk/privacy/` has opt-out and allow buttons that call
  `window.__phv.consent(false | true)` (queued if the tag has not loaded).

## Preview locally

Links are root-absolute under `/harbordesk/`, so serve this folder at that
path:

```sh
mkdir -p /tmp/hd-preview && ln -sfn "$PWD" /tmp/hd-preview/harbordesk
python3 -m http.server -d /tmp/hd-preview 4330
```

Then open http://localhost:4330/harbordesk/. The Phave tag only sends from
the Site's allowed domains, so embedded forms show on the published site,
not locally.
