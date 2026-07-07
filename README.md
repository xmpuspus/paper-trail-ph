# Paper Trail PH

A graph of every DPWH flood-control contract on the public record, the firms that won them, and the license revocations, blacklists, and court filings now attached to some of them.

**Live:** https://paper-trail-ph.vercel.app

![Paper Trail PH: the DPWH flood-control network forming from 2016 to 2025](media/papertrail-demo.gif)

_The scandal-core network forming year by year: 64 firms and 83 links in 2016 grow to 104 firms and 498 links by 2025. Full walkthrough (the replay, a firm's weighted award links, and the validated temporal analysis) is in [media/papertrail-demo.mp4](media/papertrail-demo.mp4). Both recorded with `node scripts/record_demo.mjs` against a local build._

> All data sourced from public records (COA, SEC, DBM, PSA, BSP, SALN disclosures). This tool computes statistical indicators only. Specific allegations, if any, require independent investigation and corroboration. Charges are allegations under the presumption of innocence.

## What it is

The 2025 Philippine flood-control controversy is spread across separate records: DPWH's contract portal, PCAB license actions, SEC filings, COA fraud audits, Ombudsman and Sandiganbayan cases, and a year of news coverage. This site joins them in one place, starting from the contract data and layering a carefully sourced overlay on top.

It answers a question the records can answer on their own: who won the most flood-control money, and where did it pool.

## The numbers

Every figure below is computed from the source data and reconciled across the site, the methodology page, and this README.

- **248,220** DPWH contracts, **₱6.379T**, infrastructure years 2016 to 2026.
- **33,866** flood-control and drainage contracts, **₱1.586T**, the second-largest infrastructure category by value.
- **6,558** distinct firms, resolved from the raw contractor field, and **220** district engineering offices.
- **8** firms carry a `[REVOKED]` license tag in the DPWH data, across **3,902** contracts worth **₱182B** (that same tag appears on 256 raw contractor strings, which a naive count would report as 256 firms).
- **20** flood-control district offices are highly concentrated (Herfindahl-Hirschman Index above 2,500, the US DOJ threshold).
- Sunwest, Inc. holds the highest recorded flood-control value at **₱32.83B**. Topnotch Catalyst Builders Inc. (the demo target) resolves to one node at **285 contracts / ₱17.41B**.

## What the analysis found

Read as a temporal knowledge graph: every award and joint venture carries its year, and every claim is tested against a null model. All figures are computed offline and reconciled; methods and limits are on the site's methodology page. These are statistical indicators, not findings of wrongdoing.

- **The market closed as the money tripled.** Flood-control spending rose from **₱52.6B (2016) to a ₱368.1B peak (2024)**. Over the same run, the share won by firms entering flood control for the first time fell from **15.2% (2017) to 3.5% (2025)**, while the share held by the 16 firms later named in the inquiry rose from **5.3% to a 14.4% peak (2024)**.
- **The contractor network consolidated into one web.** The largest connected group of the joint-venture network grew from **26 firms (2016) to 1,392 (2025)**. Co-location communities fell from **8 (2018) to 5 (2025)** while the largest grew from **59 to 158 firms**, and the yearly partition stabilized (adjusted Rand rising to **0.95**). The structure settled and merged; it did not churn.
- **Structure predicts next year's partnerships.** On a strict chronological split, prior shared-office structure predicts which firms form a new joint venture the following year at a macro **ROC-AUC of 0.70** (0.76 in 2024). It beats a degree-preserving configuration-model null in **every split (p < 0.01)**, so the signal is the structure itself, not merely which firms are large. Predictions are statistical similarity, never evidence of a relationship.
- **Partnerships tend to predate the money.** For firm pairs holding a recorded joint venture, the venture forms before the bulk of their shared awards **263 times, versus 66 the other way (about 4x)**. Sequence only, not intent.
- **A structural break around 2020 to 2021.** Pettitt change-point tests place the shift in several series (the named firms' share steps from about **7% to 12% at 2020**). Marginal significance over a ten-year window, so a candidate turning point, not proof.
- **Pattern indicators (OECD bid-rigging lens, descriptive).** **64** firm pairs with near-identical bidding footprints but no recorded joint venture (Jaccard ≥ 0.6, ≥ 4 shared offices); **14** joint-venture rings of 3 to 15 firms; **16** firms that first appeared in flood control in 2020 or later and won ≥ ₱1B within two years; and, tested and not found, **0** offices where two firms alternate the yearly top spot. Legitimate explanations include regional specialization, geography, and licence class.
- **Contract value against paid-up capital, from the firms' own SEC filings.** For 6 of the top flood-control contractors, PCIJ published the primary SEC documents. Measured against the paid-up capital on each firm's own General Information Sheet, flood-control value on the DPWH record runs to about **58,000x for M.G. Samidan (₱250,000 capital), 266x for Centerways, and 68x for Legacy**, while Sunwest at about **6x** is well capitalized (the ratio is a statistical indicator, not a finding). Sunwest and Hi-Tone register their principal office in the same Albay locality, and a "Wawao Builders Corporation" was registered with the SEC in 2025, after the DPWH perpetually banned Wawao Builders for ghost projects in September 2025. Every figure links its source document.
- **The money concentrates in Central Luzon.** Mapped by the DPWH record's own region field, Region III (Central Luzon) took the largest share of flood-control value, **₱267.1B (16.8% of ₱1.586T across 18 regions)**, ahead of NCR (₱157.9B, 10.0%) and Bicol / Region V (₱154.3B, 9.7%). Central Luzon holds the Bulacan district office at the centre of the COA fraud audits; Bicol holds the Sunwest, Centerways, and Hi-Tone cluster.

Methods: `scripts/build_temporal.py` (temporal link prediction, dynamic communities, Pettitt change-points, temporal motifs) and `scripts/build_analytics.py` (formation series, pattern indicators, Node2Vec prediction), all seeded with networkx, gensim, and scikit-learn.

## Confidence tiers

An inferred link never looks like a recorded one.

- **Recorded** (solid line): a contract award, joint venture, revoked license, blacklist, court filing, a source-linked person, or an SEC corporate-registry fact from a firm's own General Information Sheet, with a source.
- **Inferred from records** (curved, lighter): not stated but computed, such as two firms that are both top awardees in the same district offices.
- **Predicted** (faintest, off by default): a Node2Vec statistical similarity in bidding footprint between firms with no recorded joint venture. Not evidence of a relationship; unverified against any registry.
- **Possible namesake**: a shared surname is not a relationship. Not shown in this release. Reserved for a future human-verified layer.

The scandal overlay (owners, license revocations, charges) is primary-source-or-omit: an entry enters the graph only if it traces to a primary or primary-citing source (PCAB Board Resolution 075, Ombudsman and Sandiganbayan filings, DPWH Secretary orders, COA fraud audit reports, SEC resolutions). Firms without a confirmed action carry recorded facts only. Sources are in `public/data/overlay.json`.

The **SEC corporate-registry layer** (`public/data/sec.json`) is a separate recorded tier. Philippine SEC company data is not machine-readable in bulk: eSEARCH is a paid, authenticated document channel, automated scraping is not authorized under the Revised Corporation Code, and the SEC API Marketplace is subscription-gated. So it is not scraped. It curates the primary SEC documents (General Information Sheets and Articles of Incorporation) that [PCIJ](https://pcij.org/2025/08/30/flood-control-records/) obtained and published for the top contractors. Each registration number, paid-up capital figure, and registered office is transcribed from the firm's own GIS and links back to that document; the contract-to-capital ratio is computed from that capital and the flood-control value already on the DPWH record. Where a figure was not legible in the published document, it is omitted, not estimated.

## Data sources

- **DPWH contracts:** DPWH Transparency Portal via BetterGov.PH, published on HuggingFace as [`bettergovph/dpwh-transparency-data`](https://huggingface.co/datasets/bettergovph/dpwh-transparency-data). License CC0 1.0 Universal (public domain).
- **Official actions:** compiled and source-linked from PCAB, the Ombudsman and Sandiganbayan, DPWH, COA, and SEC. COA Fraud Audit Reports on the Bulacan flood-control projects (ghost projects, unauthorized relocation, payments for pre-existing structures) are attached to the contractors named (Wawao Builders, SYMS Construction, Topnotch) and to the procuring DPWH Bulacan 1st District Engineering Office, each with the specific project and amount.
- **SEC corporate records:** primary General Information Sheets and Articles of Incorporation for the top contractors, from the document set [PCIJ](https://pcij.org/2025/08/30/flood-control-records/) obtained and published. Transcribed per firm, each figure linking its source document.
- **News tagging:** recent coverage (GDELT plus PH outlets) matched by exact firm name to the verified scandal set, each linking its source article.

Full source list with access notes is in [DATA_SOURCES.md](DATA_SOURCES.md).

## How it is built

v1 is a static site. There is no database or backend at runtime. All data is baked to JSON at build time.

```
DPWH parquet ──▶ scripts/build_graph.py ──▶ public/data/*.json ──▶ Next.js (static) ──▶ Vercel
                 (entity resolution + networkx metrics)
```

- **Entity resolution** keys each firm on its DPWH numeric id (or a normalized name when absent), parses joint ventures on the `/` separator into recorded co-award edges, and reads the `[REVOKED]` and `FORMERLY` markers.
- **Graph metrics** (betweenness, PageRank, degree, Louvain communities, HHI per district office) are computed offline with networkx and baked into the graph. No Neo4j GDS.
- **Network analytics** (`scripts/build_analytics.py`): the year-by-year formation series (value, named-firm share with contract value split equally among joint awardees, newcomer share, cumulative JV network), structural pattern indicators with stated thresholds (near-identical footprints, JV rings, top-awardee alternation, sudden entrants), and Node2Vec link prediction (64 dims, seed 42; cosine similarity between firms with no recorded JV, corroborated by Adamic-Adar). All seeded and reproducible.
- **Temporal knowledge-graph analytics** (`scripts/build_temporal.py`): the graph read as timestamped quads. Temporal link prediction on a rolling chronological split (predict next year's new joint ventures from prior shared-office structure; macro ROC-AUC ~0.70, beats a degree-preserving null every year at p < 0.01). Dynamic community detection (Louvain per year with adjusted-Rand stability). Pettitt change-point tests on each structural series. Temporal motifs (does a joint venture predate the pair's shared awards?). Plus a heterogeneous temporal schema (person/firm/office/institution nodes, typed dated edges) populated only from sourced records.
- **Person layer:** the 8 people in the sourced overlay become graph nodes with recorded, source-linked edges to their firms. Curated, never scraped.
- **SEC layer** (`scripts/build_sec.py`): the recorded corporate-registry facts, transcribed from the primary GIS documents PCIJ published, with the contract-to-capital ratio computed from that paid-up capital and the flood-control value in `graph-main.json` so the numbers reconcile.
- **Geography** (`scripts/build_geography.py`): flood-control value by region from the DPWH record's own region field, the jurisdiction breakdown, reconciled to the flood-control total.
- **Baked outputs:** `stats.json`, `graph-scandal.json` (first paint), `graph-main.json` (full flood-control graph), `graph-topnotch.json` (demo ego network), `entities.json` (search index), `overlay.json` (sourced actions), `sec.json` (SEC corporate registry), `geography.json` (by-region jurisdiction), `in_news.json` (news tags), `temporal.json`, `signals.json`, `predicted-ties.json`.
- **Frontend:** Next.js 14, Sigma.js v3 (WebGL). On mobile the graph degrades to a searchable table.

## Run locally

```bash
npm install
npm run dev            # http://localhost:3000

# Rebuild the baked data from the DPWH parquet (offline):
python3 scripts/build_analytics.py   # temporal + signals + Node2Vec prediction
python3 scripts/build_temporal.py    # temporal KG: link prediction, communities, change-points, motifs
python3 scripts/build_sec.py         # SEC corporate registry + contract-to-capital ratios
python3 scripts/build_geography.py   # flood-control value by region (jurisdiction)
python3 scripts/build_graph.py       # graphs + search index (injects the above)
```

The parquet is pulled by `scripts/collectors/dpwh.py`. Neo4j is optional and only used as an offline exploration step. It is not required to run or build the site.

## Related projects

The interactive graph joining DPWH contracts, officials, court outcomes, and live news in one explorer is the gap this fills. Prior and related work:

- [BetterGov.PH flood visualizations](https://visualizations.bettergov.ph/flood) (the data source)
- [Rappler Politicontractors](https://www.rappler.com/newsbreak/investigative/politicians-government-contractors-connections-map/)
- [InfraWatch PH](https://infrawatchph.org/home/contractors)
- [PCIJ MoneyPolitics](https://moneypolitics.pcij.org/)
- [OCCRP Aleph](https://aleph.occrp.org/)
- [LittleSis](https://littlesis.org/)

## What is deferred

Not faked but stated plainly: bulk SALN wealth and SOCE campaign-finance joins (neither is available as machine-readable public data today; the one campaign-finance link shown is individually sourced), the PhilGEPS cross-check, and the dynasty layer. Two Phase 3 joins are deferred for a concrete reason: canonical PSGC province and municipality codes (the PSA publishes PSGC only as manual downloads behind Cloudflare, so jurisdiction uses the DPWH record's own region field instead), and the Open Congress bill layer (the documented BetterGov Open Congress API returned only a 404 page at every path tried this cycle). The PhilGEPS, Open Congress, and PSA collectors exist but are not part of the site yet.

Not affiliated with any government agency.
