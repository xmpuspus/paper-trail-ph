// Records the README demo GIF: hero, the network replay forming 2016 -> 2025,
// then a firm's weighted award links. Viewport is tall enough to keep the whole
// replay canvas in frame (it is ~0.66 of the width). Output webm -> ffmpeg GIF.
//
//   node scripts/record_demo.mjs   (with the site on http://localhost:3100)
import { chromium } from "playwright";

const b = await chromium.launch();
const ctx = await b.newContext({
  viewport: { width: 1200, height: 900 },
  recordVideo: { dir: "tmp/gif", size: { width: 1200, height: 900 } },
  deviceScaleFactor: 1,
});
const p = await ctx.newPage();
await p.goto("http://localhost:3100/", { waitUntil: "domcontentloaded" });
await p.waitForTimeout(1600); // hero: the numbers

// show the section heading briefly, then bring the whole replay figure into frame
await p.evaluate(() => document.querySelector("#analysis").scrollIntoView({ block: "start" }));
await p.waitForTimeout(900);
await p.evaluate(() => {
  // clear the sticky header so the year + counters row is fully visible
  const f = document.querySelector("#analysis figure");
  window.scrollTo(0, f.getBoundingClientRect().top + window.scrollY - 72);
});
await p.waitForTimeout(500);

// clean start at 2016, then play the growth
await p.locator('#analysis input[aria-label="Year"]').fill("2016");
await p.waitForTimeout(250);
await p.locator('#analysis button[aria-label="Play"]').first().click().catch(() => {});
await p.waitForTimeout(15600); // full replay 2016 -> 2025

// weighted edges in the explorer
await p.evaluate(() => document.querySelector("#explore").scrollIntoView({ block: "start" }));
await p.waitForTimeout(700);
const inp = p.locator('input[role="combobox"]').first();
await inp.click();
await inp.type("sunwest", { delay: 45 });
await p.waitForTimeout(400);
await inp.press("ArrowDown");
await inp.press("Enter");
await p.waitForTimeout(900);
const box = await p.locator("#explore canvas").first().boundingBox();
await p.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
await p.mouse.wheel(0, -220);
await p.waitForTimeout(2200);

const vpath = await p.video().path();
await ctx.close();
await b.close();
console.log("VIDEO:" + vpath);
