"""Offline network analytics for the static site.

Three outputs, all computed from the DPWH parquet with the same entity
resolution as build_graph.py (imported from it):

  temporal.json        how the flood-control network formed, year by year
  signals.json         structural patterns the procurement-integrity
                       literature associates with coordinated bidding
                       (descriptive indicators with stated thresholds,
                       never a finding of wrongdoing)
  predicted-ties.json  Node2Vec link prediction over the firm-office
                       bipartite graph: firm pairs whose bidding footprints
                       are statistically similar but which share no recorded
                       joint venture. Statistical similarity only - not
                       evidence of a relationship.

Run AFTER placing the parquet, BEFORE build_graph.py (which injects the
predicted ties into the baked graphs):

  python3 scripts/build_analytics.py
  python3 scripts/build_graph.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

from build_graph import FC_CATEGORY, HHI_HIGH, NAMED, PARQUET, parse_firms

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "data"

YEARS = list(range(2016, 2027))
SEED = 42

DISCLAIMER = (
    "Statistical indicators derived from public data. "
    "Patterns may have legitimate explanations."
)


def load_contracts() -> list[dict]:
    """Flatten the parquet into per-contract records with resolved firm keys."""
    df = pd.read_parquet(PARQUET)
    df["budget"] = pd.to_numeric(df["budget"], errors="coerce").fillna(0.0)

    # Same two-pass canonical keying as build_graph.py.
    name_to_id: dict[str, str] = {}
    votes: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    parsed = []
    for raw in df["contractor"].tolist():
        firms = parse_firms(raw)
        parsed.append(firms)
        for f in firms:
            if f["id"]:
                if f["norm"]:
                    name_to_id.setdefault(f["norm"], f["id"])
                votes[f["id"]][f["display"]] += 1

    def key_of(f: dict) -> str | None:
        if f["id"]:
            return f["id"]
        if f["norm"] and f["norm"] in name_to_id:
            return name_to_id[f["norm"]]
        return "n:" + f["norm"] if f["norm"] else None

    names: dict[str, str] = {}
    rows = []
    loc = df["location"].tolist()
    cats = df["category"].astype(str).tolist()
    budgets = df["budget"].tolist()
    yrs = pd.to_numeric(df["infraYear"], errors="coerce").tolist()
    for i in range(len(df)):
        firms = parsed[i]
        if not firms:
            continue
        keys = []
        for f in firms:
            k = key_of(f)
            if k is None:
                continue
            keys.append(k)
            if k not in names or (f["id"] and votes.get(k)):
                nm = max(votes[k].items(), key=lambda kv: kv[1])[0] if votes.get(k) else f["display"]
                names[k] = nm
        if not keys:
            continue
        location = loc[i] if isinstance(loc[i], dict) else {}
        y = yrs[i]
        rows.append({
            "keys": sorted(set(keys)),
            "deo": (location or {}).get("province") or "Unspecified DEO",
            "region": (location or {}).get("region") or "Unspecified",
            "fc": cats[i] == FC_CATEGORY,
            "val": float(budgets[i] or 0.0),
            "year": int(y) if y == y and 2000 <= y <= 2030 else None,  # NaN-safe
        })
    return rows, names


def build_temporal(rows, names):
    fc = [r for r in rows if r["fc"] and r["year"] in YEARS]

    per_year = {y: {"n": 0, "val": 0.0} for y in YEARS}
    # For SHARE-of-year series, split a contract's value equally among its
    # joint awardees so firm shares sum to 100% of the year total.
    firm_year_val = defaultdict(lambda: defaultdict(float))   # firm -> year -> attributed val
    deo_year_firm = defaultdict(lambda: defaultdict(float))   # (deo,y) -> firm -> val
    deo_year_n = defaultdict(int)
    jv_pair_first = {}                                        # pair -> first year

    for r in fc:
        y = r["year"]
        per_year[y]["n"] += 1
        per_year[y]["val"] += r["val"]
        split = r["val"] / len(r["keys"])
        for k in r["keys"]:
            firm_year_val[k][y] += split
            deo_year_firm[(r["deo"], y)][k] += r["val"]
        deo_year_n[(r["deo"], y)] += 1
        for a, b in combinations(r["keys"], 2):
            pair = (a, b)
            jv_pair_first[pair] = min(jv_pair_first.get(pair, y), y)

    first_year = {k: min(ys) for k, ys in firm_year_val.items()}

    # Per-year: concentrated offices (HHI>2500 among offices with >=5 FC
    # contracts that year - a floor so 1-contract office-years don't count).
    conc_by_year = {y: 0 for y in YEARS}
    active_deos = {y: 0 for y in YEARS}
    for (deo, y), fv in deo_year_firm.items():
        if deo_year_n[(deo, y)] < 5:
            continue
        tot = sum(fv.values())
        if tot <= 0:
            continue
        hhi = sum((v / tot * 100.0) ** 2 for v in fv.values())
        active_deos[y] += 1
        if hhi > HHI_HIGH:
            conc_by_year[y] += 1

    series = []
    cum_pairs = set()
    cum_firms = set()
    for y in YEARS:
        val = per_year[y]["val"]
        named_val = sum(firm_year_val[k].get(y, 0.0) for k in NAMED)
        entrant_val = sum(
            yv.get(y, 0.0) for k, yv in firm_year_val.items() if first_year[k] == y
        )
        year_firm_vals = sorted(
            (yv.get(y, 0.0) for yv in firm_year_val.values() if yv.get(y, 0.0) > 0),
            reverse=True,
        )
        cr10 = (sum(year_firm_vals[:10]) / val * 100.0) if val > 0 else 0.0

        for pair, fy in jv_pair_first.items():
            if fy == y:
                cum_pairs.add(pair)
                cum_firms.update(pair)
        Gy = nx.Graph()
        Gy.add_edges_from(cum_pairs)
        giant = max((len(c) for c in nx.connected_components(Gy)), default=0)

        series.append({
            "year": y,
            "fc_contracts": per_year[y]["n"],
            "fc_value": round(val, 2),
            "named_share_pct": round(named_val / val * 100.0, 2) if val > 0 else 0.0,
            "entrant_share_pct": round(entrant_val / val * 100.0, 2) if val > 0 else 0.0,
            "cr10_pct": round(cr10, 2),
            "concentrated_deos": conc_by_year[y],
            "active_deos": active_deos[y],
            "jv_firms_cum": len(cum_firms),
            "jv_pairs_cum": len(cum_pairs),
            "jv_giant_component": giant,
        })

    # Drop trailing years with no flood-control activity (e.g. a not-yet-
    # populated infra year at the end of the record).
    while series and series[-1]["fc_contracts"] == 0:
        series.pop()

    return {
        "_meta": {
            "method": (
                "Per infrastructure year, from the DPWH record: flood-control value and "
                "contract count; the 16 named firms' share of that year's value; the share "
                "won by firms appearing in flood control for the first time that year; the "
                "top-10-firm share (CR10); district offices above HHI 2500 that year (among "
                "offices with at least 5 flood-control contracts that year); and the "
                "cumulative joint-venture network (firms, pairs, largest connected group). "
                "For the share series, a contract's value is split equally among its joint "
                "awardees so shares sum to 100%. 2016 is the first observed year, so every "
                "firm counts as a first appearance there (the entrant series is only "
                "meaningful from 2017 on)."
            ),
            "disclaimer": DISCLAIMER,
        },
        "years": series,
    }


def build_signals(rows, names):
    fc = [r for r in rows if r["fc"]]

    firm_val = defaultdict(float)
    firm_n = defaultdict(int)
    firm_deos = defaultdict(set)
    firm_first = {}
    firm_val_first2 = defaultdict(float)
    jv_pairs = defaultdict(int)
    deo_firm_val = defaultdict(lambda: defaultdict(float))
    deo_year_top = defaultdict(dict)  # deo -> year -> (firm, val, n)

    deo_year_val = defaultdict(lambda: defaultdict(float))
    deo_year_cnt = defaultdict(lambda: defaultdict(int))
    for r in fc:
        y = r["year"]
        for k in r["keys"]:
            firm_val[k] += r["val"]
            firm_n[k] += 1
            firm_deos[k].add(r["deo"])
            deo_firm_val[r["deo"]][k] += r["val"]
            if y is not None:
                if k not in firm_first or y < firm_first[k]:
                    firm_first[k] = y
        for a, b in combinations(r["keys"], 2):
            jv_pairs[(a, b)] += 1
        if y is not None:
            for k in r["keys"]:
                deo_year_val[(r["deo"], y)][k] += r["val"]
                deo_year_cnt[(r["deo"], y)][k] += 1

    for r in fc:
        y = r["year"]
        if y is None:
            continue
        for k in r["keys"]:
            if y <= firm_first.get(k, 9999) + 1:
                firm_val_first2[k] += r["val"]

    def nm(k):
        return names.get(k, k)

    # --- Signal 1: near-identical bidding footprints without a recorded JV.
    eligible = [k for k in firm_val if firm_n[k] >= 10 and firm_val[k] >= 5e8]
    fp_items = []
    for a, b in combinations(sorted(eligible), 2):
        if (a, b) in jv_pairs or (b, a) in jv_pairs:
            continue
        da, db = firm_deos[a], firm_deos[b]
        shared = da & db
        if len(shared) < 4:
            continue
        jac = len(shared) / len(da | db)
        if jac >= 0.6:
            fp_items.append({
                "firms": [nm(a), nm(b)],
                "keys": [a, b],
                "shared_offices": len(shared),
                "jaccard": round(jac, 3),
                "combined_fc_value": round(firm_val[a] + firm_val[b], 2),
            })
    fp_items.sort(key=lambda x: -x["combined_fc_value"])

    # --- Signal 2: joint-venture groups (connected components >= 3 firms).
    J = nx.Graph()
    for (a, b), n in jv_pairs.items():
        J.add_edge(a, b, n=n)
    jv_groups = []
    for comp in nx.connected_components(J):
        # Small, dense groups only. The giant chained component (a thousand+
        # firms linked through chains of one-off JVs) is reported in
        # temporal.json as jv_giant_component, not as a "group".
        if not (3 <= len(comp) <= 15):
            continue
        comp = sorted(comp)
        val = sum(firm_val[k] for k in comp)
        edges = J.subgraph(comp).number_of_edges()
        possible = len(comp) * (len(comp) - 1) / 2
        jv_groups.append({
            "firms": [nm(k) for k in comp],
            "keys": comp,
            "size": len(comp),
            "internal_jv_pairs": edges,
            "density": round(edges / possible, 2) if possible else 0,
            "combined_fc_value": round(val, 2),
        })
    jv_groups.sort(key=lambda x: -x["combined_fc_value"])

    # --- Signal 3: two firms alternating as an office's top awardee.
    alternation = []
    for deo, fv in deo_firm_val.items():
        tot = sum(fv.values())
        if tot <= 0:
            continue
        hhi = sum((v / tot * 100.0) ** 2 for v in fv.values())
        if hhi <= HHI_HIGH:
            continue
        tops = []
        for y in YEARS:
            yv = deo_year_val.get((deo, y))
            if not yv or sum(deo_year_cnt[(deo, y)].values()) < 3:
                continue
            tops.append((y, max(yv.items(), key=lambda kv: kv[1])[0]))
        if len(tops) < 4:
            continue
        holders = [t[1] for t in tops]
        uniq = sorted(set(holders))
        switches = sum(1 for i in range(1, len(holders)) if holders[i] != holders[i - 1])
        if len(uniq) == 2 and switches >= 2:
            alternation.append({
                "office": deo,
                "hhi": round(hhi, 1),
                "years": [t[0] for t in tops],
                "top_by_year": [nm(t[1]) for t in tops],
                "firms": [nm(u) for u in uniq],
                "keys": uniq,
                "switches": switches,
            })
    alternation.sort(key=lambda x: -x["switches"])

    # --- Signal 4: new firms with immediate large flood-control awards.
    entrants = []
    for k, first in firm_first.items():
        if first >= 2020 and firm_val_first2[k] >= 1e9:
            entrants.append({
                "firm": nm(k),
                "key": k,
                "first_year": first,
                "value_first_two_years": round(firm_val_first2[k], 2),
                "contracts": firm_n[k],
            })
    entrants.sort(key=lambda x: -x["value_first_two_years"])

    return {
        "_meta": {
            "framing": (
                "Structural patterns that the procurement-integrity literature (e.g. the "
                "OECD guidelines for fighting bid rigging in public procurement) associates "
                "with coordinated bidding. Each is a descriptive statistic with the "
                "threshold stated. None is a finding of wrongdoing; legitimate explanations "
                "include regional specialization, geography, and licence class."
            ),
            "disclaimer": DISCLAIMER,
        },
        "footprint_pairs": {
            "definition": (
                "Two firms with no recorded joint venture whose flood-control district-office "
                "footprints are near-identical (Jaccard >= 0.6, >= 4 shared offices; firms "
                "with >= 10 flood-control contracts and >= P500M)."
            ),
            "count": len(fp_items),
            "items": fp_items[:12],
        },
        "jv_groups": {
            "definition": (
                "Groups of 3+ firms connected through recorded joint ventures on "
                "flood-control contracts (connected components of the co-award graph)."
            ),
            "count": len(jv_groups),
            "items": jv_groups[:10],
        },
        "alternation": {
            "definition": (
                "Highly concentrated offices (HHI > 2500) where the yearly top awardee "
                "alternates between exactly two firms across 4+ active years (>= 3 "
                "flood-control contracts per counted year, >= 2 switches)."
            ),
            "count": len(alternation),
            "items": alternation[:10],
        },
        "entrants": {
            "definition": (
                "Firms whose first flood-control award came in 2020 or later and that won "
                ">= P1B within their first two years in the category."
            ),
            "count": len(entrants),
            "items": entrants[:12],
        },
    }


def build_prediction(rows, names):
    """Node2Vec over the firm-office bipartite FC graph; cosine similarity
    between firms with no recorded JV. Corroborated with Adamic-Adar."""
    from node2vec import Node2Vec

    fc = [r for r in rows if r["fc"]]
    firm_val = defaultdict(float)
    firm_deo_n = defaultdict(lambda: defaultdict(int))
    jv = set()
    for r in fc:
        for k in r["keys"]:
            firm_val[k] += r["val"]
            firm_deo_n[k][r["deo"]] += 1
        for a, b in combinations(r["keys"], 2):
            jv.add((a, b))

    G = nx.Graph()
    for k, deos in firm_deo_n.items():
        for d, n in deos.items():
            G.add_edge("F:" + k, "D:" + d, weight=n)
    for a, b in jv:
        G.add_edge("F:" + a, "F:" + b, weight=2)

    print(f"  Node2Vec graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    n2v = Node2Vec(
        G, dimensions=64, walk_length=30, num_walks=10,
        weight_key="weight", workers=1, seed=SEED, quiet=True,
    )
    model = n2v.fit(window=10, min_count=1, seed=SEED, workers=1)

    big = sorted([k for k, v in firm_val.items() if v >= 1e9], key=lambda k: -firm_val[k])
    print(f"  candidate firms (fc >= P1B): {len(big)}")
    vecs = {}
    for k in big:
        node = "F:" + k
        if node in model.wv:
            v = model.wv[node]
            vecs[k] = v / (np.linalg.norm(v) or 1.0)

    aa_cache = {}
    def adamic_adar(a, b):
        if (a, b) not in aa_cache:
            try:
                _, _, s = next(iter(nx.adamic_adar_index(G, [("F:" + a, "F:" + b)])))
            except (StopIteration, ZeroDivisionError, nx.NetworkXError):
                s = 0.0
            aa_cache[(a, b)] = s
        return aa_cache[(a, b)]

    pairs = []
    ks = [k for k in big if k in vecs]
    for i in range(len(ks)):
        for j in range(i + 1, len(ks)):
            a, b = ks[i], ks[j]
            if (a, b) in jv or (b, a) in jv:
                continue
            cos = float(np.dot(vecs[a], vecs[b]))
            if cos < 0.5:
                continue
            pairs.append((cos, a, b))
    pairs.sort(reverse=True)
    top = pairs[:40]

    items = []
    for cos, a, b in top:
        shared = set(firm_deo_n[a]) & set(firm_deo_n[b])
        items.append({
            "firms": [names.get(a, a), names.get(b, b)],
            "keys": [a, b],
            "score": round(cos, 4),
            "adamic_adar": round(adamic_adar(a, b), 3),
            "shared_offices": len(shared),
        })

    return {
        "_meta": {
            "method": (
                "Node2Vec graph embedding (64 dims, 10 walks of length 30 per node, "
                "seed 42) over the flood-control firm-to-district-office graph plus "
                "recorded joint-venture edges. For firm pairs with >= P1B recorded "
                "flood-control value each and NO recorded joint venture, the score is "
                "the cosine similarity of their embeddings; Adamic-Adar over shared "
                "offices is reported alongside for corroboration."
            ),
            "caveat": (
                "A predicted tie is a statistical similarity in bidding footprint. It is "
                "NOT evidence of a relationship, coordination, or wrongdoing, and it has "
                "not been verified against any registry or filing."
            ),
            "disclaimer": DISCLAIMER,
        },
        "count": len(items),
        "pairs": items,
    }


def main():
    print(f"Loading {PARQUET.name} ...")
    rows, names = load_contracts()
    print(f"  {len(rows)} contracts with resolvable firms")

    temporal = build_temporal(rows, names)
    tot_val = sum(y["fc_value"] for y in temporal["years"])
    print(f"Temporal: {len(temporal['years'])} years, total FC value P{tot_val/1e12:.3f}T")

    signals = build_signals(rows, names)
    for key in ("footprint_pairs", "jv_groups", "alternation", "entrants"):
        print(f"Signal {key}: {signals[key]['count']}")

    predicted = build_prediction(rows, names)
    print(f"Predicted ties kept: {predicted['count']}")

    for name, obj in [("temporal.json", temporal), ("signals.json", signals),
                      ("predicted-ties.json", predicted)]:
        p = OUT / name
        p.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))
        print(f"  wrote {name} ({p.stat().st_size/1e3:.1f} kB)")


if __name__ == "__main__":
    main()
