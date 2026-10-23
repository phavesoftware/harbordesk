// Generates the Harbor Desk logo files in assets/ (SVG, PNG, ICO, social card).
// Run from the repo root: node scripts/logo.mjs
// Needs the gitignored .tools/ install (opentype.js, @resvg/resvg-js, png-to-ico)
// and the font files in .tools/fonts/.
import { createRequire } from "node:module";
import { writeFileSync, readFileSync, mkdirSync } from "node:fs";

const require = createRequire(
  new URL("../.tools/package.json", import.meta.url),
);
const opentype = require("opentype.js");
const { Resvg } = require("@resvg/resvg-js");
const pngToIcoModule = require("png-to-ico");
const pngToIco = pngToIcoModule.default ?? pngToIcoModule;

const PRIMARY = "#008080";
const SECONDARY = "#000080";
const INK = "#0f2a44";
const ACCENT = "#f5a524";
const WHITE = "#ffffff";
const LINE = "#d8e2e5";

const FONTS = ".tools/fonts";
const ttf = readFileSync(`${FONTS}/Manrope-800.ttf`);
const manrope = opentype.parse(
  ttf.buffer.slice(ttf.byteOffset, ttf.byteOffset + ttf.byteLength),
);

mkdirSync("assets", { recursive: true });

function anchor(color) {
  return `<g fill="none" stroke="${color}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="50" cy="24" r="7"/>
    <path d="M50 31V78"/>
    <path d="M37 42H63"/>
    <path d="M24 58C26 70 37 78 50 78C63 78 74 70 76 58"/>
    <path d="M18 64L24 57L31 62"/>
    <path d="M82 64L76 57L69 62"/>
  </g>`;
}

function markTile(tile, glyph) {
  return `<rect width="100" height="100" rx="24" fill="${tile}"/>${anchor(glyph)}`;
}

function textPath(text, x, baseline, size, color) {
  const path = manrope.getPath(text, x, baseline, size);
  return {
    svg: path.toSVG(2).replace("<path ", `<path fill="${color}" `),
    advance: manrope.getAdvanceWidth(text, size),
  };
}

function wordmark(harborColor, deskColor) {
  const size = 58;
  const x = 124;
  const baseline = 71;
  const harbor = textPath("Harbor", x, baseline, size, harborColor);
  const gap = manrope.getAdvanceWidth(" ", size);
  const desk = textPath(
    "Desk",
    x + harbor.advance + gap,
    baseline,
    size,
    deskColor,
  );
  return {
    svg: harbor.svg + desk.svg,
    width: Math.ceil(x + harbor.advance + gap + desk.advance + 4),
  };
}

function svgDoc(width, height, body, title) {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" role="img" aria-label="${title}">
<title>${title}</title>
${body}
</svg>
`;
}

function png(svg, width, path) {
  const out = new Resvg(svg, {
    fitTo: { mode: "width", value: width },
    font: { loadSystemFonts: false },
  })
    .render()
    .asPng();
  writeFileSync(path, out);
  return out;
}

const color = wordmark(SECONDARY, PRIMARY);
const logo = svgDoc(
  color.width,
  100,
  markTile(PRIMARY, WHITE) + color.svg,
  "Harbor Desk logo",
);
writeFileSync("assets/logo.svg", logo);
png(logo, 600, "assets/logo.png");

const white = wordmark(WHITE, WHITE);
const logoWhite = svgDoc(
  white.width,
  100,
  anchor(WHITE) + white.svg,
  "Harbor Desk logo (white)",
);
writeFileSync("assets/logo-white.svg", logoWhite);
png(logoWhite, 600, "assets/logo-white.png");

const mark = svgDoc(100, 100, markTile(PRIMARY, WHITE), "Harbor Desk mark");
writeFileSync("assets/logo-mark.svg", mark);
png(mark, 512, "assets/logo-mark.png");

const fullBleed = svgDoc(
  100,
  100,
  `<rect width="100" height="100" fill="${PRIMARY}"/><g transform="translate(14 14) scale(0.72)">${anchor(WHITE)}</g>`,
  "Harbor Desk icon",
);
png(fullBleed, 180, "apple-touch-icon.png");
const icoSizes = [16, 32, 48].map((size) =>
  png(mark, size, `.tools/favicon-${size}.png`),
);
writeFileSync("favicon.ico", await pngToIco(icoSizes));
writeFileSync("favicon.svg", mark);

const cardLogo = wordmark(WHITE, WHITE);

function socialCard(eyebrow, lines, subline, out) {
  const eyebrowText = eyebrow
    ? `<text x="96" y="300" font-family="Inter" font-weight="600" font-size="26" letter-spacing="3" fill="${ACCENT}">${eyebrow}</text>`
    : "";
  const top = eyebrow ? 372 : 400;
  const headline = lines
    .map(
      ([text, fill], i) =>
        `<text x="96" y="${top + i * 76}" font-family="Manrope" font-weight="800" font-size="60" fill="${fill}">${text}</text>`,
    )
    .join("\n  ");
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630">
  <rect width="1200" height="630" fill="${INK}"/>
  <rect y="606" width="1200" height="24" fill="${PRIMARY}"/>
  <rect x="96" y="606" width="180" height="24" fill="${ACCENT}"/>
  <g transform="translate(96 ${eyebrow ? 110 : 150}) scale(${eyebrow ? 1.2 : 1.6})">${markTile(PRIMARY, WHITE)}${cardLogo.svg}</g>
  ${eyebrowText}
  ${headline}
  <text x="96" y="${top + lines.length * 76 - 6}" font-family="Inter" font-size="28" fill="${LINE}">${subline}</text>
</svg>`;
  const pngOut = new Resvg(svg, {
    fitTo: { mode: "width", value: 1200 },
    font: {
      loadSystemFonts: false,
      fontFiles: [
        `${FONTS}/Manrope-800.ttf`,
        `${FONTS}/Inter-400.ttf`,
        `${FONTS}/Inter-600.ttf`,
      ],
      defaultFontFamily: "Inter",
    },
  })
    .render()
    .asPng();
  writeFileSync(out, pngOut);
}

socialCard(
  null,
  [
    ["See churn coming.", WHITE],
    ["Act before renewal.", ACCENT],
  ],
  "The customer success platform for B2B SaaS teams.",
  "assets/og-image.png",
);
socialCard(
  "FREE LIVE WORKSHOP",
  [
    ["Churn-risk teardown workshop", WHITE],
    ["See the accounts at risk while", ACCENT],
    ["there is still time to talk.", ACCENT],
  ],
  "60 minutes on Zoom · 8 companies per session · Nov and Dec 2026",
  "assets/og-workshop.png",
);
socialCard(
  null,
  [
    ["Voyez venir l’attrition.", WHITE],
    ["Agissez avant le renouvellement.", ACCENT],
  ],
  "La plateforme de réussite client des équipes SaaS B2B.",
  "assets/og-image-fr.png",
);
socialCard(
  "ATELIER GRATUIT EN DIRECT",
  [
    ["Décortiquer le risque d’attrition", WHITE],
    ["Repérez les comptes à risque", ACCENT],
    ["pendant qu’il est encore temps.", ACCENT],
  ],
  "60 minutes sur Zoom · 8 entreprises par séance · nov. et déc. 2026",
  "assets/og-workshop-fr.png",
);

console.log(
  "logo width",
  color.width,
  "white width",
  white.width,
  readFileSync("assets/logo.png").length,
  "bytes png",
);
