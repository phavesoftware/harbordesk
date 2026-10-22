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
