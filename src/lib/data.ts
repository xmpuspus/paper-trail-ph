import fs from "fs";
import path from "path";
import type { Stats, GraphData, Overlay, InNews, TemporalData, SignalsData, PredictedTies, TemporalAnalysis, SecData } from "./types";

// Build-time readers: the page is a server component, so these bake the small
// JSON straight into the static HTML (instant first paint, no fetch, no CLS).

const DATA = path.join(process.cwd(), "public", "data");

function readJson<T>(file: string): T {
  return JSON.parse(fs.readFileSync(path.join(DATA, file), "utf-8")) as T;
}

export function getStats(): Stats {
  return readJson<Stats>("stats.json");
}
export function getScandalGraph(): GraphData {
  return readJson<GraphData>("graph-scandal.json");
}
export function getTopnotchGraph(): GraphData {
  return readJson<GraphData>("graph-topnotch.json");
}
export function getOverlay(): Overlay {
  return readJson<Overlay>("overlay.json");
}
export function getInNews(): InNews {
  return readJson<InNews>("in_news.json");
}
export function getTemporal(): TemporalData {
  return readJson<TemporalData>("temporal.json");
}
export function getSignals(): SignalsData {
  return readJson<SignalsData>("signals.json");
}
export function getPredicted(): PredictedTies {
  return readJson<PredictedTies>("predicted-ties.json");
}
export function getTemporalAnalysis(): TemporalAnalysis {
  return readJson<TemporalAnalysis>("temporal-analysis.json");
}
export function getSec(): SecData {
  return readJson<SecData>("sec.json");
}
