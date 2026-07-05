# Next-session brief: enhance + publish paper-trail-ph as a live accountability graph site

Copy the fenced block below into a fresh session started in `~/Desktop/paper-trail-ph`. Everything above the fence is context for Xavier; the fenced block is the prompt.

## Why this exists (context for Xavier, not for the agent)

paper-trail-ph is a v0 that shipped once (2 commits, last 2026-02-17) and went cold. It already holds a strong spine: 248,220 DPWH contracts (PHP 6.38T, 11,161 contractors, 220 procuring entities) from the BetterGovPH CC0 dataset, plus PhilGEPS, Open Congress, PSA PSGC, and COMELEC. The frontend is already Next.js + Sigma.js v3 (@react-sigma/core). The only reason it is not publicly hosted is the always-on Neo4j backend.

The live news moment is the reason to move now. The DPWH flood-control ghost-project cartel is the biggest PH accountability story of 2026 (COA P325M Bulacan case Jan 2026, ~60 contractors blacklisted Feb 2026, Sen. Jinggoy Estrada Sandiganbayan warrant Jun 1 with 3 DPWH NCR engineers suspended Jun 29, Sen. Rodante Marcoleta Ombudsman plunder charge Jul 3 over P75M undeclared donations, Balamban Cebu ghost projects Jul 1). The named contractors are ALREADY in the ingested dataset. This is his proven top-tier LinkedIn format (the "corruption graph Neo4j" post did 8.4k impressions / 255 reactions / 23 reposts, a top-5 post).

Verified data readiness this session (2026-07-04):
- READY now: BetterGovPH DPWH HF dataset (Parquet, through 2025-08, CC0); GDELT (news events API, free); PH news RSS (Rappler/Philstar/Inquirer/Senate); PCIJ MoneyPolitics (campaign-finance context, web-citable).
- Re-verify (existing collectors, may have drifted): Open Congress API now returns an HTML shell at `/api/v1` paths, so the collector needs a live re-check; PhilGEPS is manual XLSX; PSA and COMELEC are manual, Cloudflare-gated.
- PARTIAL, defer to v1.1: SALN (saln.bettergov.ph is a live no-auth SPA but name-by-name scrape, no bulk API); COMELEC SOCE campaign finance (Project Suri beta; use PCIJ MoneyPolitics as the interim mirror).
- BLOCKED, defer to v1.2+: SEC bulk beneficial ownership (per-lookup only, bulk needs an institutional request); Ombudsman case data (no clean API).

Architecture decision (locked): keep the Next.js + Sigma.js v3 frontend, drop the always-on Neo4j, bake a pre-computed static graph JSON (NetworkX offline for betweenness / PageRank / Louvain / HHI), pre-aggregate 248k contracts down to a curated ~2k-5k-node explorer, deploy static on the PERSONAL Vercel account. GraphRAG becomes an optional serverless Vercel function calling a current Claude model with a k-hop subgraph as context (about $15-20/month, or omit for a free v1). This is a backend swap plus a UI/UX and news-linking enhancement, not a rebuild.

The one real risk: this publishes a network of named living people under active charges, optimized for reach. The guardrails below are hard gates, not suggestions. Getting a name wrong is a defamation exposure, not just a data bug.

---

```
ultrawork enhance and publish paper-trail-ph as a live, hosted Philippine accountability graph site that rides the DPWH flood-control scandal, don't stop until every phase below is verified done.

PROJECT
- Path: ~/Desktop/paper-trail-ph (git repo on main, 2 commits, last 2026-02-17, LOCAL ONLY unless a personal GitHub remote already exists. Commit as the personal xmpuspus identity only, use --no-gpg-sign.)
- Current stack: Next.js 14 + Sigma.js v3 (@react-sigma/core) frontend; Neo4j backend; ETL in scripts/pipeline.py; data in data/raw and data/processed; cypher/ seeds. Deploy target is PERSONAL Vercel account xmpuspus ONLY (this is a personal civic project, never a work account, see the personal-vs-work hard rule).
- What it does now: cross-references DPWH (248,220 contracts, PHP 6.38T, 11,161 contractors), PhilGEPS, Open Congress, PSA PSGC, COMELEC into a Neo4j knowledge graph with entity resolution, derived relationships (co-bidding, ownership, surname), red-flag analysis, a Sigma explorer, and a GraphRAG chat.
- Goal: host it publicly, link it to the live scandal, deepen the graph data science, and bring the UI/UX up to a global standard, without ever asserting a conclusion the records do not support.

HARD GUARDRAILS (read first, they gate every phase)
1. Sourced facts, never tool-asserted conclusions. "The Ombudsman charged Marcoleta on 2026-07-03 (link to filing)" is a sourced fact and is allowed. "Marcoleta's donor network" drawn by inference is an assertion and is NOT allowed as a bare claim. Every charge, blacklist, or COA finding rendered on a node MUST carry the primary-source link (Ombudsman filing, COA report number, DPWH blacklist notice, Sandiganbayan case). Verify each named person and charge against the PRIMARY filing before it enters the graph, not against an aggregator headline.
2. Confidence-tier every edge, visually. Recorded edges (contract award, blacklist, COA finding, Ombudsman charge) render as solid, full-weight, with a source link. Derived edges (co-bidding, shared address, ownership inference) render dashed and lighter, labeled "inferred from records". Surname-dynasty matching is LOW confidence and potentially defamatory (a shared surname is not a relationship): render it faintest, label it "possible namesake, unverified", and never let it read as a wrongdoing link. An inferred edge must never look like a recorded one.
3. Presumption of innocence. Charges are allegations. Every person node with a pending case shows "charged, case pending" with the filing link, and shows dismissal or acquittal if that happens. No copy that pronounces guilt.
4. Keep the repo's existing discipline: descriptive statistics only, not accusations; ban "ghost", "fraud", "thief", "corrupt" as tool-voice verdicts in all user-facing copy and API output (use "flagged for review", "blacklisted per DPWH", "charged per Ombudsman filing", each with a link); put the analytics disclaimer on EVERY computed surface ("Statistical indicators derived from public records. Patterns may have legitimate explanations."). The word "ghost project" is allowed ONLY when quoting and linking a named source (COA, news), never as the tool's own label.
5. Personal accounts only. Personal Vercel, personal GitHub, personal API keys. Never a work/Attic/Boost credential.
6. Do NOT invoke the Workflow tool or any deep-research fan-out. Those need Xavier's explicit per-run approval. Use at most 4-5 regular Agent subagents if you need parallelism.

CLUSTER CONVENTIONS (the paper-trail-ph scoped rules auto-load when you edit files here, follow them)
- Neo4j Community edition ONLY, never GDS (GDS is paid). For graph algorithms use networkx (export subgraph, compute, bake to JSON). This matches the locked static-build decision. paper-trail-ph uses Neo4j ports 7474/7687.
- Canonical disclaimer block on every README and About page, verbatim: "All data sourced from public records (COA, SEC, DBM, PSA, BSP, SALN disclosures). This tool computes statistical indicators only. Specific allegations, if any, require independent investigation and corroboration." Plus the analytics disclaimer on every computed panel.
- In public copy (LinkedIn, README), say "Related projects" or "What came before", not "prior art". Before any "first/only" claim, run a real prior-art check (GitHub, PyPI, directories) and narrow the claim to what is true. PCIJ MoneyPolitics, Rappler's contractor tracker, OCCRP Aleph, and LittleSis are the related projects to credit; the honest gap is the interactive graph that joins DPWH contracts + officials + cases + live news in one explorer.
- If GraphRAG uses a backend, the cluster convention is Next.js rewrites proxying to a local FastAPI, single-origin, never enable CORS.

PHASE 0 - make the cold repo run again (do this first, log to tmp/verify-<UTC>/)
- The repo is 4.5 months cold. `npm install`, confirm the Next.js app builds. Check for bitrotted deps.
- Re-verify every existing collector against its live source TODAY: Open Congress API (the base now returns an HTML shell, find the real JSON endpoints via /api/scalar or fix the collector), the BetterGovPH HF dataset (still CC0, re-pull the latest snapshot), PhilGEPS, PSA, COMELEC. Log HTTP status and row counts.
- Decide and record: does v1 keep any Neo4j at all, or go fully static? Recommended: fully static baked JSON for the public site, keep the Neo4j pipeline as the offline build step only. Confirm with the data before committing to the teardown.

PHASE 1 - the offline graph + data science (NetworkX, pre-computed, baked to JSON)
- Build the graph in Python from the ingested sources. Entities: contractors, procuring entities (DPWH district offices), officials/legislators, donors, cases. Edges: recorded (award, blacklist, COA finding, charge, donation) vs derived (co-bidding, shared attribute), each tagged with a confidence tier and a source link.
- Pre-aggregate 248k contracts to a curated explorer of ~2k-5k nodes: bipartite projection contractor<->procuring-entity weighted by shared-contract count and peso value, then filter to the top nodes by betweenness (brokers), PageRank (flow influence), and degree, PLUS force-include every entity named in the current scandal coverage.
- Compute with NetworkX (offline, no running DB): betweenness centrality (broker officials/firms), PageRank, Louvain community detection (co-bidding clusters), HHI per procuring entity (single-vendor concentration, flag > 2500), degree. Bake all metrics as node/edge attributes into the exported graph.json. Keep per-scandal subgraph JSONs (flood-control, Marcoleta donors, Estrada case) as separate small files for fast load and for the story-rail.
- Defer to v1.1 (state clearly, do not fake): Node2Vec link prediction, temporal money-flow snapshots, SALN wealth join, SOCE campaign-finance join. Leave clean interfaces for them.

PHASE 2 - news linking (this is what makes it "live")
- Pull GDELT and PH news RSS (Rappler, Philstar, Inquirer, Senate). Run NER (spaCy or a cheap current Claude model, read the claude-api skill for the correct current model id, use Haiku 4.5 for cheap batch NER) to extract persons/orgs/amounts.
- Match extracted entities to graph nodes with rapidfuzz (token_set_ratio, >= 88 threshold), and require a light human-review pass on the match list before tagging (a false match here is the defamation risk). Tag matched nodes `in_news` with {headline, source_url, date}.
- In the UI, `in_news` nodes get a subtle pulse and a "In the news this week" tooltip linking the source. This is the hook: the reader opens the site during the scandal and sees the named entities already lit.
- The demo that must work: search "Topnotch Catalyst Builders" (a named blacklisted flood-control contractor already in the dataset) and see its full DPWH contract network, its procuring entities, its co-bidders, its concentration score, with the blacklist and COA source links.

PHASE 3 - UI/UX enhancement to a global standard (DEEP, this is a first-class goal, not polish)
Invoke the design skills and let them drive, do not freehand this:
- /frontend-design for aesthetic direction and typographic system.
- /ui-ux and /ui-ux-pro-max for the interaction and heuristics pass (Nielsen visibility of status, user control, recognition over recall, error prevention; Krug clarity; progressive disclosure).
- /dataviz (or the data-visualization skill) for the graph's visual encoding: a categorical, color-blind-safe community palette that works in BOTH light and dark mode, weight/size encodings that are honest (node size = recorded contract value, not inferred importance), and a clear legend.
Required UX, measured against global standards:
- Information architecture: a landing that states what this is and its limits, a story-rail that walks the flood-control scandal (the hero narrative) with the graph reacting beat by beat, a search-first interactive explorer, per-entity detail cards (contracts, amounts, cases, sources, confidence-tiered relationships), and the GraphRAG chat panel.
- The confidence tiers from the guardrails must be legible at a glance: solid vs dashed edges, a legend, and a filter to show/hide inferred edges.
- Accessibility: full keyboard navigation, ARIA on interactive nodes, a screen-reader table fallback for the graph (the graph is not the only way to reach the data), color-blind-safe colors, sufficient contrast in light and dark.
- Responsive: on mobile the WebGL graph degrades to a fast searchable list plus entity cards, never a broken canvas. Loading, empty, and error states everywhere. No layout shift.
- Performance: Sigma.js v3 WebGL, lazy-load the big graph, ship the scandal subgraph first for instant first paint.
- Trust surface: a visible methodology page, the disclaimer on every computed panel, the primary-source links on every claim, an "about the data and its limits" section.

PHASE 4 - GraphRAG (optional for v1, cheap and serverless if included)
- A Vercel serverless function that takes a question plus a seed entity, extracts a 2-hop subgraph from the baked JSON, serializes it, and calls a current Claude model (read the claude-api skill for the correct current model id; do not hardcode an old one) to answer WITH node citations that link back into the graph. About $15-20/month. If it risks slowing the ship, cut it from v1 and ship the explorer, add chat in v1.1.

PHASE 5 - deslop, visual QA gate, publish
- Run /deslop over ALL human-facing copy including every UI string, methodology text, tooltips, and the LinkedIn draft. Zero AI tells, zero em-dashes (hard rule), plain concrete language, real nouns.
- MANDATORY visual QA hard gate (/screenshot-qa): screenshot every page and the explorer at 1920x1080 AND 1440x900, Read each screenshot back, verify the graph fills its frame (not a tiny floating cluster), the confidence tiers are visible, the story-rail reads, mobile degrades correctly. Loop fix-and-reshoot until clean. "It rendered" is not "it looks good".
- Recompute every number and reconcile it to the digit across README, methodology, UI, and the LinkedIn draft.
- Deploy to the PERSONAL Vercel account, fingerprint the live site against the local build, confirm the public URL returns 200 and shows the current build.
- Regenerate the hero demo.gif from the LIVE site (real recording, not a mockup) showing the Topnotch-Catalyst-search demo and the story-rail. Frame-extract and Read it back.

DEFINITION OF DONE
- Public site live on personal Vercel, 200, shows the scandal subgraph on first load.
- Every named person/charge on the graph links to a primary source; inferred edges are visually distinct and labeled; disclaimer on every computed surface; zero tool-voice verdict words.
- NetworkX metrics baked into the graph; the Topnotch-Catalyst search demo works.
- `in_news` tagging live from GDELT/RSS with a reviewed match list.
- UI/UX passes the /screenshot-qa gate at both viewports, accessible, responsive, deslopped, no em-dashes.
- README + methodology + LinkedIn draft reconciled to the numbers, hero GIF re-recorded from the live site.
- LinkedIn draft written to the proven format (news hook first, checkable artifact, one repeatable number, honest-caveat voice, link in the first comment), leading with the DPWH cartel and the "who won the most" question, NOT naming-and-shaming an individual as the tool's verdict.

HARD GUARDRAILS RECAP: sourced facts not conclusions; confidence-tier every edge; presumption of innocence; descriptive not accusatory copy with the verdict-word ban and disclaimer; personal accounts only; no Workflow tool.
```
