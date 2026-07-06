// Records the Paper Trail PH walkthrough for the README GIF and the LinkedIn
// video. Deliberately paced with holds on each beat so a viewer can read the
// numbers and see each feature, rather than flashing past.
//
//   node scripts/record_demo.mjs   (with the site on http://localhost:3100)
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
  window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY - o, behavior: "instant" });
}, [sel, off]);

await p.goto("http://localhost:3100/", { waitUntil: "domcontentloaded" });
await hold(3200); // BEAT 1: hero, let the headline numbers register

// BEAT 2: the network forming, year by year
await toTop("#analysis", 72);
await hold(1200);
await toTop("#analysis figure", 72);
await hold(600);
await p.locator('#analysis input[aria-label="Year"]').fill("2016");
await hold(300);
await p.locator('#analysis button[aria-label="Play"]').first().click().catch(() => {});
await hold(16500); // full replay 2016 -> 2025 at natural pace
await hold(2200);  // hold on the finished network

// BEAT 3: the validated temporal analysis (the differentiator)
await p.evaluate(() => {
  const h = [...document.querySelectorAll("#analysis h3")].find((e) => /Temporal knowledge graph/i.test(e.textContent));
  window.scrollTo({ top: h.getBoundingClientRect().top + window.scrollY - 72, behavior: "instant" });
});
await hold(5200); // read the AUC-vs-null and consolidation charts

// BEAT 4: a firm's record with award links weighted by contract count
await toTop("#explore", 72);
await hold(1000);
const inp = p.locator('input[role="combobox"]').first();
await inp.click();
await inp.type("sunwest", { delay: 55 });
await hold(600);
await inp.press("ArrowDown");
await inp.press("Enter");
await hold(1100);
const box = await p.locator("#explore canvas").first().boundingBox();
await p.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
await p.mouse.wheel(0, -230);
await hold(4200); // hold on the weighted, labelled edges + the record panel
await hold(800);

const vpath = await p.video().path();
await ctx.close();
await b.close();
console.log("VIDEO:" + vpath);
