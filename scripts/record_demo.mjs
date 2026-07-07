// Records the Paper Trail PH walkthrough for the README GIF and the LinkedIn
// video. Deliberately paced with holds on each beat so a viewer can read the
// numbers and see each feature, rather than flashing past.
//
//   node scripts/record_demo.mjs   (with the site on http://localhost:3100)
//
// Beats: the DPWH flood-control record, enriched with each firm's SEC filing and
// the COA fraud-audit findings, then read through time.
//   1. hero (the scale)
//   2. a firm's record enriched with its SEC filing and the COA audit finding
//   3. the network forming year by year, 2016 to 2025
//   4. the validated temporal analysis
//   5. flood-control value by region
//   6. contract value against each firm's own paid-up capital (SEC)
//
// Produces a webm in tmp/gif/. Post-process to MP4 (LinkedIn) and GIF (README)
// with the ffmpeg commands in the repo (see the demo build step).
import { chromium } from "playwright";

const b = await chromium.launch();
const ctx = await b.newContext({
  viewport: { width: 1200, height: 900 },
  recordVideo: { dir: "tmp/gif", size: { width: 1200, height: 900 } },
  deviceScaleFactor: 1,
});
const p = await ctx.newPage();
const hold = (ms) => p.waitForTimeout(ms);
const toTop = (sel, off) => p.evaluate(([s, o]) => {
  const el = document.querySelector(s);
  if (el) window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY - o, behavior: "instant" });
}, [sel, off]);
const toHeading = (re, off) => p.evaluate(([r, o]) => {
  const h = [...document.querySelectorAll("#analysis h3")].find((e) => new RegExp(r, "i").test(e.textContent));
  if (h) window.scrollTo({ top: h.getBoundingClientRect().top + window.scrollY - o, behavior: "instant" });
}, [re, off]);
const panelScroll = (top) => p.evaluate((t) => {
  const el = document.querySelector('aside[aria-label^="Details for"] .custom-scrollbar');
  if (el) el.scrollTo({ top: t, behavior: "smooth" });
}, top);

await p.goto("http://localhost:3100/", { waitUntil: "domcontentloaded" });
await hold(3200); // BEAT 1: hero, let the headline numbers register

// BEAT 2: a firm's record, enriched with its SEC filing and the COA audit finding
await toTop("#explore", 72);
await hold(1000);
const inp = p.locator('input[role="combobox"]').first();
await inp.click();
await inp.type("wawao builders", { delay: 55 });
await hold(750);
// select Wawao Builders specifically (not the unrelated "Wawa Rich")
await p.locator('#search-results [role="option"]').filter({ hasText: /WAWAO BUILDERS/i }).first().click();
await hold(1500); // the record panel: DPWH contracts + Corporate registry (SEC)
await panelScroll(320);
await hold(3200); // hold on the SEC registration, paid-up capital, contract-to-capital
// scroll the COA Fraud Audit Report finding into view within the panel
await p.evaluate(() => {
  const panel = document.querySelector('aside[aria-label^="Details for"] .custom-scrollbar');
  if (!panel) return;
  const el = [...panel.querySelectorAll("span, h3, li, p")].find((e) => /COA Fraud Audit Report/i.test(e.textContent));
  if (el) el.scrollIntoView({ block: "center", behavior: "smooth" });
});
await hold(3600); // hold on the COA Fraud Audit Report finding, with its source

// BEAT 3: the network forming, year by year
await toTop("#analysis", 72);
await hold(900);
await toTop("#analysis figure", 72);
await hold(500);
await p.locator('#analysis input[aria-label="Year"]').fill("2016");
await hold(300);
await p.locator('#analysis button[aria-label="Play"]').first().click().catch(() => {});
await hold(16000); // full replay 2016 -> 2025 at natural pace
await hold(1800);  // hold on the finished network

// BEAT 4: the validated temporal analysis
await toHeading("Temporal knowledge graph", 72);
await hold(4800); // read the AUC-vs-null and consolidation charts

// BEAT 5: flood-control value by region
await toHeading("by region", 72);
await hold(4400);

// BEAT 6: contract value against each firm's own paid-up capital, from the SEC filing
await toHeading("Corporate registry", 72);
await hold(5600); // the contract-to-capital table, 58,000x down to Sunwest's 6x

const vpath = await p.video().path();
await ctx.close();
await b.close();
console.log("VIDEO:" + vpath);
