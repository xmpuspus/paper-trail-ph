import { chromium } from "playwright";
const b = await chromium.launch();
const ctx = await b.newContext({ viewport: { width: 1200, height: 700 }, recordVideo: { dir: "tmp/gif", size: { width: 1200, height: 700 } }, deviceScaleFactor: 1 });
const p = await ctx.newPage();
await p.goto("http://localhost:3100/", { waitUntil: "domcontentloaded" });
await p.waitForTimeout(1600); // hero: the numbers

await p.evaluate(() => document.querySelector('#analysis').scrollIntoView({ block: "start" }));
await p.waitForTimeout(700);
await p.locator('#analysis input[aria-label="Year"]').fill('2016'); // interacted -> no auto-play race
await p.waitForTimeout(250);
await p.locator('#analysis button[aria-label="Play"]').first().click().catch(()=>{});
await p.waitForTimeout(15600); // the replay 2016 -> 2025

await p.evaluate(() => document.querySelector('#explore').scrollIntoView({ block: "start" }));
await p.waitForTimeout(700);
const inp = p.locator('input[role="combobox"]').first();
await inp.click(); await inp.type("sunwest", { delay: 45 }); await p.waitForTimeout(400);
await inp.press("ArrowDown"); await inp.press("Enter");
await p.waitForTimeout(900);
const box = await p.locator('#explore canvas').first().boundingBox();
await p.mouse.move(box.x + box.width/2, box.y + box.height/2);
await p.mouse.wheel(0, -220);
await p.waitForTimeout(2200);

const vpath = await p.video().path();
await ctx.close(); await b.close();
console.log("VIDEO:" + vpath);
