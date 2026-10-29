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
  page, no colors outside `:root`, US spelling on US pages and British on UK
  pages, no foreign prices, each copy carries only its own tag, every
  redirect lands on a page, no avoided words).
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

Every page exists in three languages, each under its own path, switched from
the flag picker in the header (each page links to the same page in the
others, with `hreflang` alternates and a sitemap entry per language):

| Language | Path | Source |
|---|---|---|
| English (US) | `/harbordesk/en-us/` | `src/*.html`, the source of truth |
| English (UK) | `/harbordesk/en-gb/` | derived at build time by `scripts/en_gb.py` (British spellings, prices in pounds, workshop times in GMT); put a file in `src/en-gb/` to override a page |
| Deutsch | `/harbordesk/de-de/` | `src/de-de/*.html`, titles and descriptions in `src/de-de/meta.json` |

Edit a US page and the British page follows on the next build. The German
page does not: update `src/de-de/` in the same change (the translation brief
is in `.tools/de-brief.md`). Prices in pounds are one table in `en_gb.py`
(`PRICES`); the German pages spell the euro amounts themselves. Links in a
fragment written as `{{base}}/...` point at the page's own language and
variant; `{{base}}/assets/...` stays shared.

`/harbordesk/` itself redirects to the visitor's language (German, British
or US English by the browser's language list). The addresses the site had
before the language paths (`/harbordesk/pricing/`, `/harbordesk/en-ca/...`,
`/harbordesk/fr-ca/...`) are redirect pages to the US English page.

The Phave form on the workshop page is the same form in every language, so
it shows in English on the German page.

## Staging and dev copies

The build writes the whole site twice, identical but for the Phave site tag:

| Copy | Path | Tag |
|---|---|---|
| Staging | `/harbordesk/<lang>/` | `STAGING_TAG` in `build.py`: the Harbor Desk subscription on staging |
| Dev | `/harbordesk/dev/<lang>/` | `DEV_TAG` in `build.py`: served by a developer's local Phave (`http://…localhost:…/bambino.js`) |

The dev pages carry a "Dev" badge beside the logo, `noindex`, a canonical
pointing at the staging page, and stay out of the sitemap. Chrome loads an
`http://localhost` script on an https page (localhost counts as secure), and
may ask once to allow access to devices on the local network. To point the
dev copy at another local subscription, replace `DEV_TAG` with the snippet
from that Phave's Settings → Web → Write keys (allowed origin
`https://phavesoftware.github.io`) and rebuild.

## Phave wiring

- Subscription: **Harbor Desk** on staging (`stage.phave.dev`).
- Site: Self-hosted, host `phavesoftware.github.io`.
- The site tag is the last element in `<head>` on every page (`STAGING_TAG`
  in `build.py`; the workshop fragment's form embed writes `{{tag}}` for its
  second copy). Its attributes identify the account: copy it exactly, and
  rebuild if the key is rotated (Settings → Web → Write keys).
- Page paths below are the US English ones; every language and the dev
  copy have the same pages under their own prefix.
- `/harbordesk/en-us/demo/` has a `#demo-form` card holding a plain HTML form. A
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
