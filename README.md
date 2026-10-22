# Harbor Desk demo website

A fictional company's marketing site, used to demo Phave form embeds.
Served by GitHub Pages at https://phavesoftware.github.io/harbordesk/.

Plain static HTML, no build step. Push to `main` and Pages republishes.

## Phave wiring

- Subscription: **Harbor Desk** on staging (`stage.phave.dev`).
- Site: **Harbor Desk website**, Self-hosted, host `phavesoftware.github.io`.
- The site tag sits at the end of `<head>` on every page, written directly
  in the HTML. Its attributes identify the account: copy it exactly, and
  replace it on every page if the key is rotated (Settings → Web → Write keys).
- `demo.html` has an empty `#demo-form` container. Add a content slot on
  the `/harbordesk/demo.html` landing page with selector `#demo-form`,
  insert mode "Replace children", and a form, then publish the slot.

## Preview locally

`python3 -m http.server 4330` and open http://localhost:4330/. The tag only
sends from the Site's allowed domains, so forms render on the published
address, not locally.
