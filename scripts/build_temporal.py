"""Temporal knowledge-graph analytics for the flood-control network.

Everything here is computed offline from the DPWH parquet and validated. Four
techniques plus a heterogeneous schema:

  1. Temporal link prediction. Predict next year's new joint ventures from the
     prior shared-office structure with a time-decayed Adamic-Adar score, on a
     rolling chronological split (train on years <= T, test on ties that first
     appear in T+1, never peeking at the future). Skill is measured by ROC-AUC
     and checked two ways: a label-permutation test (is the ranking better than
     chance?) and a degree-preserving configuration-model null (is the signal
     real, or just an artefact of which firms are big?).

  2. Dynamic communities. Louvain on the cumulative firm co-location graph each
     year, with year-over-year partition stability (adjusted Rand), to see the
     cartel structure crystallise, and the largest community's trajectory.

  3. Change-points. Pettitt's non-parametric test on each yearly structural
     series, to date when the market's structure shifted.

  4. Temporal motifs. For firm pairs that both share offices and hold a recorded
     joint venture, did the JV form before or after their shared awards
     concentrated? Sequence, not just co-occurrence.

Plus a heterogeneous temporal edge list (Person / Firm / Office / Institution
nodes; typed, dated edges) built ONLY from the sourced overlay. That is the
money-and-power schema, populated with real data and ready to scale when bulk
SALN / SOCE records become machine-readable.

Descriptive statistics from public data. Patterns may have legitimate
explanations. Predictions are statistical, never evidence of a relationship.

Run after build_analytics.py:  python3 scripts/build_temporal.py
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import networkx as nx
import numpy as np
from sklearn.metrics import roc_auc_score

from build_analytics import load_contracts
from build_graph import NAMED

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "data"

YEARS = list(range(2016, 2026))
HALF_LIFE = 2.0                 # years; recent awards weigh more
LAMBDA = math.log(2) / HALF_LIFE
BIG = 1e9                       # firm is "sizeable" at >= P1B flood-control value
SEED = 42
DISCLAIMER = "Statistical indicators derived from public data. Patterns may have legitimate explanations."


# ----------------------------------------------------------------- substrate
def build_substrate(rows, names):
    """Timestamped quads: firm-office awards and firm-firm joint ventures."""
    firm_val = defaultdict(float)
    firm_office_years = defaultdict(lambda: defaultdict(list))  # firm -> office -> [years]
    office_firm_first = defaultdict(dict)                       # office -> firm -> first year
    jv_years = defaultdict(set)                                 # (a,b) sorted -> {years}

    for r in rows:
        if not r["fc"] or r["year"] is None:
            continue
        y, o = r["year"], r["deo"]
        keys = sorted(set(r["keys"]))
        for f in keys:
            firm_val[f] += r["val"]
            firm_office_years[f][o].append(y)
            cur = office_firm_first[o].get(f)
            office_firm_first[o][f] = y if cur is None else min(cur, y)
        for a, b in combinations(keys, 2):
            jv_years[(a, b)].add(y)

    return firm_val, firm_office_years, office_firm_first, jv_years


# ------------------------------------------------------- temporal link pred.
def offices_upto(firm_office_years, f, T):
    """Offices firm f awarded in by year T, with the most recent award year."""
    out = {}
    for o, ys in firm_office_years[f].items():
        rec = [y for y in ys if y <= T]
        if rec:
            out[o] = max(rec)
    return out


def office_degree(office_firm_first, T):
    deg = {}
    for o, ff in office_firm_first.items():
        deg[o] = sum(1 for y in ff.values() if y <= T)
    return deg


def aa_scores(pairs, foff_T, deg_T, T, decay=True):
    """Time-decayed Adamic-Adar over shared offices for each firm pair."""
    scores = []
    for a, b in pairs:
        oa, ob = foff_T[a], foff_T[b]
        shared = oa.keys() & ob.keys()
        s = 0.0
        for o in shared:
            d = deg_T.get(o, 1)
            w = 1.0 / math.log(1 + d) if d > 1 else 1.0
            if decay:
                w *= math.exp(-LAMBDA * (T - oa[o])) * math.exp(-LAMBDA * (T - ob[o]))
            s += w
        scores.append(s)
    return np.array(scores)


def bipartite_rewire(edges, n_swaps, rng):
    """Degree-preserving swap on the firm-office bipartite edge set."""
    E = list(edges)
    eset = set(E)
    m = len(E)
    done = 0
    attempts = 0
    while done < n_swaps and attempts < n_swaps * 20:
        attempts += 1
        i, j = rng.integers(0, m), rng.integers(0, m)
        if i == j:
            continue
        (f1, o1), (f2, o2) = E[i], E[j]
        if o1 == o2 or f1 == f2:
            continue
        if (f1, o2) in eset or (f2, o1) in eset:
            continue
        eset.discard((f1, o1)); eset.discard((f2, o2))
        eset.add((f1, o2)); eset.add((f2, o1))
        E[i] = (f1, o2); E[j] = (f2, o1)
        done += 1
    return eset


def link_prediction(firm_val, firm_office_years, office_firm_first, jv_years, names):
    firms = {f for f, v in firm_val.items() if v >= BIG}
    jv_first = {p: min(ys) for p, ys in jv_years.items()}
    rng = np.random.default_rng(SEED)

    per_year = []
    for T in range(2018, 2025):  # predict T+1 in 2019..2025
        foff_T = {f: offices_upto(firm_office_years, f, T) for f in firms}
        deg_T = office_degree(office_firm_first, T)
        existing = {p for p, y in jv_first.items() if y <= T}

        # candidate universe: big-firm pairs, no JV yet, sharing >= 1 office by T
        cand = []
        for a, b in combinations(sorted(firms), 2):
            if (a, b) in existing:
                continue
            if foff_T[a].keys() & foff_T[b].keys():
                cand.append((a, b))
        if not cand:
            continue
        # positives: first JV in exactly T+1
        pos = {p for p, y in jv_first.items() if y == T + 1}
        labels = np.array([1 if p in pos else 0 for p in cand])
        n_pos = int(labels.sum())
        if n_pos < 2 or n_pos == len(cand):
            per_year.append({"train_upto": T, "predict": T + 1, "candidates": len(cand),
                             "new_jv": n_pos, "auc": None, "note": "too few positives to score"})
            continue

        real = aa_scores(cand, foff_T, deg_T, T, decay=True)
        auc = float(roc_auc_score(labels, real))

        # label-permutation null: is the ranking better than chance?
        n_perm = 500
        perm_auc = np.empty(n_perm)
        for k in range(n_perm):
            perm_auc[k] = roc_auc_score(rng.permutation(labels), real)
        p_perm = float((np.sum(perm_auc >= auc) + 1) / (n_perm + 1))

        # degree-preserving null: rebuild AA on rewired award graph
        edges = {(f, o) for f in firms for o in foff_T[f]}
        n_null = 120
        null_auc = np.empty(n_null)
        base_last = {(f, o): foff_T[f][o] for f in firms for o in foff_T[f]}
        for k in range(n_null):
            re = bipartite_rewire(edges, len(edges), rng)
            foff_r = defaultdict(dict)
            for (f, o) in re:
                # keep a plausible recency: reuse the firm's own last-year distribution
                foff_r[f][o] = base_last.get((f, o), T)
            deg_r = defaultdict(int)
            for (_f, o) in re:
                deg_r[o] += 1
            sc = aa_scores(cand, foff_r, deg_r, T, decay=True)
            try:
                null_auc[k] = roc_auc_score(labels, sc)
            except ValueError:
                null_auc[k] = 0.5
        p_null = float((np.sum(null_auc >= auc) + 1) / (n_null + 1))

        examples = sorted(
            [(names.get(a, a), names.get(b, b), float(s)) for (a, b), s, l in zip(cand, real, labels) if l == 1],
            key=lambda x: -x[2])[:5]

        per_year.append({
            "train_upto": T, "predict": T + 1, "candidates": len(cand), "new_jv": n_pos,
            "auc": round(auc, 3),
            "auc_null_mean": round(float(null_auc.mean()), 3),
            "p_label_perm": round(p_perm, 4),
            "p_degree_null": round(p_null, 4),
            "top_hits": [{"firms": [a, b], "score": round(s, 3)} for a, b, s in examples],
        })
        print(f"  T<={T} -> {T+1}: cand={len(cand)} newJV={n_pos} AUC={auc:.3f} "
              f"null~{null_auc.mean():.3f} p_perm={p_perm:.3f} p_null={p_null:.3f}")

    scored = [y for y in per_year if y.get("auc") is not None]
    macro = round(float(np.mean([y["auc"] for y in scored])), 3) if scored else None
    return {
        "_meta": {
            "method": (
                "Rolling chronological split: for each cut year T, score every sizeable "
                "firm pair (>= P1B flood-control value) that shares an office but has no "
                "recorded joint venture by T, using a time-decayed Adamic-Adar over their "
                "shared offices (half-life 2 years). Positives are pairs whose FIRST joint "
                "venture appears in T+1. Skill is ROC-AUC. Two nulls: a label-permutation "
                "test and a degree-preserving configuration-model rewiring of the award "
                "graph."),
            "disclaimer": DISCLAIMER,
        },
        "macro_auc": macro,
        "by_year": per_year,
    }


# ---------------------------------------------------------- dynamic communities
def firm_projection(firm_office_years, firms, T, min_shared=2):
    """Firms linked if they share >= min_shared offices by year T."""
    off = {f: {o for o, ys in firm_office_years[f].items() if any(y <= T for y in ys)} for f in firms}
    G = nx.Graph()
    G.add_nodes_from(firms)
    fl = sorted(firms)
    for i in range(len(fl)):
        for j in range(i + 1, len(fl)):
            s = len(off[fl[i]] & off[fl[j]])
            if s >= min_shared:
                G.add_edge(fl[i], fl[j], weight=s)
    return G


def dynamic_communities(firm_val, firm_office_years):
    from sklearn.metrics import adjusted_rand_score
    firms = {f for f, v in firm_val.items() if v >= BIG}
    prev = None
    series = []
    for T in range(2018, 2026):
        G = firm_projection(firm_office_years, firms, T)
        Gc = G.subgraph([n for n in G if G.degree(n) > 0]).copy()
        if Gc.number_of_nodes() == 0:
            continue
        comms = nx.community.louvain_communities(Gc, weight="weight", seed=SEED)
        member = {}
        for ci, c in enumerate(comms):
            for n in c:
                member[n] = ci
        sizes = sorted((len(c) for c in comms), reverse=True)
        stability = None
        if prev is not None:
            common = [n for n in member if n in prev]
            if len(common) > 3:
                stability = round(float(adjusted_rand_score(
                    [prev[n] for n in common], [member[n] for n in common])), 3)
        series.append({
            "year": T, "firms_linked": Gc.number_of_nodes(), "communities": len(comms),
            "largest": sizes[0] if sizes else 0, "top_sizes": sizes[:5],
            "stability_vs_prev": stability,
        })
        print(f"  {T}: linked={Gc.number_of_nodes()} comms={len(comms)} largest={sizes[0] if sizes else 0} stab={stability}")
        prev = member
    return {
        "_meta": {
            "method": (
                "Louvain communities on the cumulative firm co-location graph each year "
                "(firms linked when they share >= 2 flood-control district offices, among "
                "firms with >= P1B). Stability is the adjusted Rand index between one year's "
                "partition and the previous year's, on the firms present in both: higher "
                "means the cluster structure is settling."),
            "disclaimer": DISCLAIMER,
        },
        "by_year": series,
    }


# ------------------------------------------------------------- change-points
def pettitt(x):
    """Pettitt's non-parametric change-point test. Returns (change_index, approx_p)."""
    n = len(x)
    U = np.zeros(n)
    for t in range(n):
        s = 0
        for i in range(t + 1):
            for j in range(t + 1, n):
                s += np.sign(x[i] - x[j])
        U[t] = s
    k = int(np.argmax(np.abs(U)))
    K = float(np.abs(U[k]))
    p = 2.0 * math.exp((-6.0 * K * K) / (n ** 3 + n ** 2))
    return k, min(1.0, p)


def change_points(temporal):
    ys = temporal["years"]
    years = [y["year"] for y in ys]
    metrics = {
        "fc_value": [y["fc_value"] for y in ys],
        "named_share_pct": [y["named_share_pct"] for y in ys],
        "entrant_share_pct": [y["entrant_share_pct"] for y in ys],
        "cr10_pct": [y["cr10_pct"] for y in ys],
        "concentrated_deos": [y["concentrated_deos"] for y in ys],
        "jv_giant_component": [y["jv_giant_component"] for y in ys],
    }
    out = {}
    for name, series in metrics.items():
        k, p = pettitt(np.array(series, dtype=float))
        out[name] = {"change_year": years[k], "p_value": round(p, 4),
                     "before_mean": round(float(np.mean(series[:k + 1])), 2),
                     "after_mean": round(float(np.mean(series[k + 1:])), 2) if k + 1 < len(series) else None}
        print(f"  {name:20s} change @ {years[k]}  p={p:.3f}")
    return {
        "_meta": {
            "method": ("Pettitt's non-parametric single change-point test on each yearly "
                       "structural series. The change year is where the series most sharply "
                       "shifts level; the p-value is the approximate significance."),
            "disclaimer": DISCLAIMER,
        },
        "metrics": out,
    }


# --------------------------------------------------------------- temporal motifs
def temporal_motifs(firm_office_years, jv_years, firm_val, names):
    firms = {f for f, v in firm_val.items() if v >= BIG}
    before = after = concurrent = 0
    examples = []
    for (a, b), jys in jv_years.items():
        if a not in firms or b not in firms:
            continue
        jv_first = min(jys)
        oa = {o: [y for y in ys] for o, ys in firm_office_years[a].items()}
        ob = firm_office_years[b]
        shared_years = []
        for o in oa.keys() & ob.keys():
            ys = [y for y in oa[o]] + [y for y in ob[o]]
            shared_years.extend(ys)
        if len(shared_years) < 3:
            continue
        med = float(np.median(shared_years))
        rel = "concurrent"
        if jv_first < med - 0.5:
            before += 1; rel = "jv_before_awards"
        elif jv_first > med + 0.5:
            after += 1; rel = "awards_before_jv"
        else:
            concurrent += 1
        examples.append((names.get(a, a), names.get(b, b), jv_first, med, rel, len(shared_years)))
    examples.sort(key=lambda x: -x[5])
    return {
        "_meta": {
            "method": ("For each firm pair holding a recorded joint venture, compare the "
                       "JV's first year to the median year of their shared-office awards. "
                       "'JV before awards' means the partnership predates the bulk of the "
                       "shared money; 'awards before JV' the reverse. Sequence only, never a "
                       "claim of intent."),
            "disclaimer": DISCLAIMER,
        },
        "counts": {"jv_before_awards": before, "awards_before_jv": after, "concurrent": concurrent},
        "examples": [{"firms": [a, b], "jv_year": int(j), "awards_median_year": round(m, 1),
                      "relation": rel, "shared_awards": n} for a, b, j, m, rel, n in examples[:12]],
    }


# ------------------------------------------------ heterogeneous temporal schema
def hetero_schema():
    """Typed, dated edges from the sourced overlay only. Real data, ready to scale."""
    ov_path = OUT / "overlay.json"
    overlay = json.loads(ov_path.read_text()) if ov_path.exists() else {"persons": [], "firms": {}, "sources": {}}
    src = overlay.get("sources", {})

    def sdate(keys):
        for k in keys:
            d = src.get(k, {}).get("date")
            if d:
                return d
        return None

    nodes = {"Person": 0, "Firm": 0, "Institution": 0}
    edges = []  # (head, htype, relation, tail, ttype, date, source)
    persons = overlay.get("persons", [])
    nodes["Person"] = len(persons)
    for p in persons:
        for fk in p.get("firms", []):
            edges.append({"head": p["name"], "head_type": "Person", "relation": "linked_to",
                          "tail": fk, "tail_type": "Firm", "date": sdate(p.get("sources", [])),
                          "sources": p.get("sources", [])})
    for fk, f in overlay.get("firms", {}).items():
        nodes["Firm"] += 1
        for a in f.get("actions", []):
            edges.append({"head": fk, "head_type": "Firm", "relation": a.get("type"),
                          "tail": a.get("label", "")[:60], "tail_type": "Institution",
                          "date": a.get("date"), "sources": [a.get("source")]})
    return {
        "_meta": {
            "purpose": ("The money-and-power schema: Person, Firm, Office and Institution "
                        "nodes joined by typed, dated edges (linked_to, revoked, charged, "
                        "lookout, donated, ...). Populated ONLY from the sourced overlay. "
                        "Bulk SALN wealth and SOCE campaign-finance joins are not yet "
                        "machine-readable public data; this is the interface, filled with "
                        "the real, source-linked records that exist, ready to scale."),
            "node_types": ["Person", "Firm", "ProcuringEntity", "Institution"],
            "edge_types": ["linked_to", "awarded", "co_awarded", "revoked", "charged",
                           "lookout", "donated", "frozen", "cleared"],
            "disclaimer": DISCLAIMER,
        },
        "node_counts": nodes,
        "edge_count": len(edges),
        "edges": edges,
    }


def main():
    print("Loading contracts ...")
    rows, names = load_contracts()
    firm_val, foy, off_first, jvy = build_substrate(rows, names)
    n_quads = sum(len(ys) for f in foy for ys in foy[f].values())
    print(f"  {len(firm_val)} FC firms, {n_quads} firm-office-year quads, {len(jvy)} JV pairs")

    print("Temporal link prediction ...")
    lp = link_prediction(firm_val, foy, off_first, jvy, names)
    print("Dynamic communities ...")
    dc = dynamic_communities(firm_val, foy)
    print("Change-points ...")
    temporal = json.loads((OUT / "temporal.json").read_text())
    cp = change_points(temporal)
    print("Temporal motifs ...")
    mo = temporal_motifs(foy, jvy, firm_val, names)
    print("Heterogeneous schema ...")
    hs = hetero_schema()
    print(f"  hetero edges: {hs['edge_count']}  nodes: {hs['node_counts']}")

    out = {
        "_meta": {"disclaimer": DISCLAIMER,
                  "generated_note": "Temporal knowledge-graph analytics, computed offline and validated."},
        "link_prediction": lp,
        "dynamic_communities": dc,
        "change_points": cp,
        "motifs": mo,
        "hetero": hs,
    }
    p = OUT / "temporal-analysis.json"
    p.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    print(f"\nwrote {p.name} ({p.stat().st_size/1e3:.1f} kB)")
    print("motifs:", mo["counts"])
    print("macro AUC:", lp["macro_auc"])


if __name__ == "__main__":
    main()
