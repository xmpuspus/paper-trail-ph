// Search over the baked entity index, augmented with the sourced overlay.
//
// The raw index (public/data/entities.json) holds only firms and district
// offices. People (owners, officers, the persons named in reporting) and a
// firm's former names live in the overlay and in the `former` field. This
// module folds those into each firm's searchable text so a search for an owner
// or an old company name resolves to the firm node the site can actually show.
//
// Matching has two tiers:
//   1. exact: every query word is a substring of the firm's text (order-free,
//      punctuation-insensitive). This is what carries a normal search.
//   2. similar: when exact results are thin, every query word is within a small
//      edit distance of some word in the text. This catches typos and drops a
//      "similar" set below the exact hits.

import type { Entity, Overlay } from "./types";

export interface SearchResult {
  entity: Entity;
  // Why this surfaced when the query did not match the firm's own name:
  // an owner/officer name, or a former company name. Null when the name matched.
  reason: { kind: "name" | "former"; text: string } | null;
  similar: boolean;
}

interface Alias {
  text: string;
  norm: string;
  kind: "name" | "former";
}

interface Item {
  entity: Entity;
  labelNorm: string;
  haystack: string; // label + aliases, normalized, space-joined
  aliases: Alias[];
  fc: number;
}

// Lowercase, strip accents, reduce every run of non-alphanumerics to one space.
// "Elizaldy \"Zaldy\" Co" -> "elizaldy zaldy co"; "SUNWEST, INC" -> "sunwest inc".
export function normalize(s: string): string {
  return s
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

export function buildSearchIndex(entities: Entity[], overlay: Overlay | null): Item[] {
  // firm key -> owner/officer display names, from both overlay surfaces.
  const namesByFirm = new Map<string, string[]>();
  const push = (key: string, name: string) => {
    const arr = namesByFirm.get(key);
    if (arr) arr.push(name);
    else namesByFirm.set(key, [name]);
  };
  if (overlay) {
    for (const p of overlay.persons) for (const fk of p.firms) push(fk, p.name);
    for (const [fk, f] of Object.entries(overlay.firms)) if (f.owner) push(fk, f.owner);
  }

  return entities.map((e) => {
    const aliases: Alias[] = [];
    const seen = new Set<string>();
    for (const name of namesByFirm.get(e.key) ?? []) {
      const norm = normalize(name);
      if (!norm || seen.has(norm)) continue;
      seen.add(norm);
      aliases.push({ text: name, norm, kind: "name" });
    }
    if (e.former) {
      const norm = normalize(e.former);
      if (norm && !seen.has(norm)) {
        seen.add(norm);
        aliases.push({ text: e.former, norm, kind: "former" });
      }
    }
    const labelNorm = normalize(e.label);
    const haystack = [labelNorm, ...aliases.map((a) => a.norm)].join(" ");
    return { entity: e, labelNorm, haystack, aliases, fc: e.fc_value || 0 };
  });
}

// How many edits a query word may be off by to still count as "similar".
// Short words get no slack (2-char words would fuzzy-match half the index).
function slack(word: string): number {
  return word.length <= 3 ? 0 : word.length <= 6 ? 1 : 2;
}

// Levenshtein distance, capped: returns cap+1 as soon as the whole row exceeds
// the cap, so a far-off word bails after O(cap) work instead of O(len^2).
function boundedLev(a: string, b: string, cap: number): number {
  const al = a.length;
  const bl = b.length;
  if (Math.abs(al - bl) > cap) return cap + 1;
  let prev = new Array<number>(bl + 1);
  for (let j = 0; j <= bl; j++) prev[j] = j;
  for (let i = 1; i <= al; i++) {
    const cur = new Array<number>(bl + 1);
    cur[0] = i;
    let rowMin = i;
    const ac = a.charCodeAt(i - 1);
    for (let j = 1; j <= bl; j++) {
      const cost = ac === b.charCodeAt(j - 1) ? 0 : 1;
      const v = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost);
      cur[j] = v;
      if (v < rowMin) rowMin = v;
    }
    if (rowMin > cap) return cap + 1;
    prev = cur;
  }
  return prev[bl];
}

// Distance of a query word to the closest word in `words`; -1 if none is within
// the word's slack. A prefix match (typing "sun" for "sunwest") is distance 0.
function wordDistance(token: string, words: string[]): number {
  const cap = slack(token);
  let best = -1;
  for (const w of words) {
    if (w.startsWith(token)) return 0; // user typed a prefix of this word
    if (cap === 0) continue;
    const d = boundedLev(token, w, cap);
    if (d <= cap && (best < 0 || d < best)) best = d;
  }
  return best;
}

function reasonFor(
  item: Item,
  tokens: string[],
  mode: "exact" | "similar",
): { kind: "name" | "former"; text: string } | null {
  // Label matched on its own — no need to explain.
  const labelWords = item.labelNorm.split(" ");
  const labelHit =
    mode === "exact"
      ? tokens.every((t) => item.labelNorm.includes(t))
      : tokens.every((t) => wordDistance(t, labelWords) >= 0);
  if (labelHit) return null;

  for (const a of item.aliases) {
    const hit =
      mode === "exact"
        ? tokens.every((t) => a.norm.includes(t))
        : tokens.every((t) => wordDistance(t, a.norm.split(" ")) >= 0);
    if (hit) return { kind: a.kind, text: a.text };
  }
  return item.aliases[0] ? { kind: item.aliases[0].kind, text: item.aliases[0].text } : null;
}

const MAX_RESULTS = 40;
const EXACT_ENOUGH = 8; // stop looking for "similar" once this many exact hits exist

export function searchEntities(items: Item[], query: string): SearchResult[] {
  const qn = normalize(query);
  if (!qn) return [];
  const tokens = qn.split(" ");

  interface Scored {
    item: Item;
    rank: number;
    similar: boolean;
  }
  const exact: Scored[] = [];

  for (const it of items) {
    if (!tokens.every((t) => it.haystack.includes(t))) continue;
    const rank =
      it.labelNorm === qn ? 0 : it.labelNorm.startsWith(qn) ? 1 : it.labelNorm.includes(qn) ? 2 : 3;
    exact.push({ item: it, rank, similar: false });
  }
  exact.sort((a, b) => a.rank - b.rank || b.item.fc - a.item.fc);

  const scored: Scored[] = [...exact];

  // Only pay for fuzzy scanning when exact hits are thin.
  if (exact.length < EXACT_ENOUGH) {
    const inExact = new Set(exact.map((s) => s.item.entity.key));
    const similar: Scored[] = [];
    for (const it of items) {
      if (inExact.has(it.entity.key)) continue;
      const words = it.haystack.split(" ");
      let total = 0;
      let ok = true;
      for (const t of tokens) {
        const d = wordDistance(t, words);
        if (d < 0) {
          ok = false;
          break;
        }
        total += d;
      }
      if (ok) similar.push({ item: it, rank: total, similar: true });
    }
    similar.sort((a, b) => a.rank - b.rank || b.item.fc - a.item.fc);
    scored.push(...similar);
  }

  return scored.slice(0, MAX_RESULTS).map((s) => ({
    entity: s.item.entity,
    reason: reasonFor(s.item, tokens, s.similar ? "similar" : "exact"),
    similar: s.similar,
  }));
}
