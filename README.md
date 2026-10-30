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

## Form test pages

Four pages exercise Phave's form features the way a real marketing site
uses them. Each copy has its own form settings: `STAGING_FORMS` and
`DEV_FORMS` in `build.py`, keyed by name. A form setting holds an embed key
(Phave: the form tactic's Embed panel); a field setting holds a field id
from the form. Leave a value empty and the page shows "This form is not
connected yet." in that spot (or the plain link still works), so the site
builds and checks before anything exists in Phave. All four pages load
`assets/forms.js`, which uses only the documented page API
(`window.__phv.q`).

**The form log.** On the dev copy, or on any page with `?formlog` in the
address, a panel in the corner lists what the forms report: each form as
it becomes ready (`forms.whenReady`), `setValues` results with any refused
ids, `onValidate`, `forms.open` answering null, the `phv:form:success`
event with its values, and the `phv.form.success` dataLayer push.

| Page | Like PTC's | Settings | What it tests |
|---|---|---|---|
| `/contact/` | Global contact us | `contact` | The embed snippet in a card; starter fields; country to phone code and the inferred country; required dropdowns with a blank first choice; a character count |
| `/pilot/` | Embedded form over a background image | `pilot`, `pilot_plan`, `pilot_email` | `forms.load` into a page element; the form's own look on a dark hero; `setValues` on a page-settable hidden field from the plan buttons; `onValidate` refusing free-mail addresses |
| `/resources/templates/` | Pop-ups on gated assets, the footer form | `asset`, `asset_name`, `tour`, `newsletter` | `data-phave-form-open` on links (the link still works when the form is quiet); the asset's name into a hidden field when the pop-up opens; an event display rule; `forms.load` for the newsletter |
| `/customers/tidewater-freight/` | Case study "Download PDF" | `case_study`, `newsletter` | `forms.open` from page code; `onSuccess` returning `false` to close the pop-up and show the page's own download; `forms.open` answering null after a recent submit; the dataLayer push |

**Set up in Phave** (Harbor Desk on staging, or the local subscription for
the dev copy), then put the keys and ids into the matching dictionary and
rebuild:

1. **contact**: a form from the Global contact us starter. Add a required
   "Topic" dropdown with the placeholder "Choose a topic", and a paragraph
   field "How can we help?" with a 500-character limit and Show character
   count on. Embed it on the Site.
2. **pilot**: name, work email, company, and a hidden "Plan" field set to
   let the page set it. Give it its own look (a dark theme reads well on
   the hero). `pilot_plan` is the Plan field's id, `pilot_email` the email
   field's.
3. **asset**: a gated download with a hidden "Asset" field the page may
   set, opening as a pop-up, with 48 hours of quiet after a submit.
   `asset_name` is the Asset field's id.
4. **tour**: a short "Want a guided walk-through?" form with the display
   rule "on page event" `harbordesk:tour-halfway`. The tour on the
   templates page sends it halfway through.
5. **newsletter**: email only, inline.
6. **case_study**: a gated download for the PDF, opening as a pop-up.

Three things to know while testing:

- **Display rules arm on every page of the Site**, because a Site embed is
  placed site-wide. An event rule only fires where a page sends the event,
  but a delay rule pops up everywhere: try delay rules on the dev copy only.
- **Staging runs merged Phave code only.** Features still on a branch work
  on the dev copy against a local Phave that runs that branch.
- **Quiet hours are remembered in the browser** (only while tracking
  consent holds). To see a quiet form open again, use a private window or
  clear the site's storage.

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
