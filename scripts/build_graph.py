"""Offline graph build for the static site.

Reads the DPWH transparency parquet, resolves contractor entities on the
DPWH numeric id, parses joint-venture co-awards, computes networkx metrics
(betweenness, PageRank, degree, Louvain communities, HHI per district office),
and bakes JSON the Next.js site loads directly. No Neo4j required.

All outputs are RECORDED facts from the DPWH dataset plus derived metrics
computed here. The curated person/case/blacklist overlay lives separately in
public/data/overlay.json and is primary-source verified, not produced here.

Run: python3 scripts/build_graph.py
"""

from __future__ import annotations

import json
import re
import math
from collections import defaultdict
from pathlib import Path

import pandas as pd
import networkx as nx

ROOT = Path(__file__).resolve().parent.parent
PARQUET = ROOT / "data" / "raw" / "dpwh" / "dpwh_transparency_data.parquet"
OUT = ROOT / "public" / "data"
OUT.mkdir(parents=True, exist_ok=True)

# Pin the flood-control definition to the exact DPWH category so every surface
# (README, methodology, UI, LinkedIn) reconciles to the same number.
FC_CATEGORY = "Flood Control and Drainage"
HHI_HIGH = 2500  # US DOJ "highly concentrated" threshold

# Marker parentheticals inside a contractor string: a DPWH id, a revoked tag,
# or a former-name note. Everything else is part of the name.
ID_PAREN = re.compile(r"\(\s*(?:\[REVOKED\]\s*)?(\d+)\s*\)")
FORMER_PAREN = re.compile(r"\(\s*FORMERLY[:\s]*([^)]*)\)", re.IGNORECASE)
MARKER_PAREN = re.compile(r"\(\s*(?:FORMERLY[^)]*|\[REVOKED\][^)]*|\d+)\s*\)", re.IGNORECASE)
REVOKED_TAG = re.compile(r"\[REVOKED\]", re.IGNORECASE)


def norm_name(s: str) -> str:
    """Normalize a firm name for fallback keying (no id present)."""
    s = REVOKED_TAG.sub("", s or "")
    s = MARKER_PAREN.sub("", s)
    s = re.sub(r"[^A-Za-z0-9]+", " ", s).strip().upper()
    return s


def clean_display(segment: str) -> str:
    """Human-readable base name: strip marker parentheticals and revoked tag."""
    s = MARKER_PAREN.sub("", segment or "")
    s = REVOKED_TAG.sub("", s)
    s = re.sub(r"\s+", " ", s).strip(" /.-,")
    return s.strip()


def parse_firms(raw: str) -> list[dict]:
    """Split a contractor cell into its firm segments (joint ventures on ' / ')."""
    if not raw or not isinstance(raw, str) or not raw.strip():
        return []
    firms = []
    for seg in raw.split(" / "):
        seg = seg.strip()
        if not seg:
            continue
        m = ID_PAREN.search(seg)
        fid = m.group(1) if m else None
        fm = FORMER_PAREN.search(seg)
        former = clean_display(fm.group(1)) if fm else None
        firms.append(
            {
                "raw": seg,
                "id": fid,
                "revoked": bool(REVOKED_TAG.search(seg)),
                "former": former,
                "display": clean_display(seg),
                "norm": norm_name(seg),
            }
        )
    return firms


def main() -> None:
    print(f"Loading {PARQUET.name} ...")
    df = pd.read_parquet(PARQUET)
    df["budget"] = pd.to_numeric(df["budget"], errors="coerce").fillna(0.0)
    n_rows = len(df)
    total_value = float(df["budget"].sum())

    # ---- Pass 1: build a normalized-name -> canonical id map from rows that
    # carry an id, so id-less appearances of the same firm collapse to one node.
    name_to_id: dict[str, str] = {}
    id_name_votes: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    parsed_cache: list[list[dict]] = []
    for raw in df["contractor"].tolist():
        firms = parse_firms(raw)
        parsed_cache.append(firms)
        for f in firms:
            if f["id"]:
                if f["norm"]:
                    name_to_id.setdefault(f["norm"], f["id"])
                id_name_votes[f["id"]][f["display"]] += 1

    def canonical_key(f: dict) -> str | None:
        if f["id"]:
            return f["id"]
        if f["norm"] and f["norm"] in name_to_id:
            return name_to_id[f["norm"]]
        if f["norm"]:
            return "n:" + f["norm"]
        return None

    def canonical_name(cid: str, fallback: str) -> str:
        if cid in id_name_votes and id_name_votes[cid]:
            return max(id_name_votes[cid].items(), key=lambda kv: kv[1])[0]
        return fallback

    # ---- Pass 2: aggregate per firm and per district office (procuring entity).
    firm = defaultdict(lambda: {
        "id": None, "name": None, "revoked": False, "former": None,
        "n_all": 0, "val_all": 0.0, "n_fc": 0, "val_fc": 0.0,
        "deos": defaultdict(lambda: {"n": 0, "val": 0.0, "fc_n": 0, "fc_val": 0.0}),
        "regions": set(), "years": set(), "categories": defaultdict(int),
    })
    deo = defaultdict(lambda: {
        "name": None, "region": None, "n_all": 0, "val_all": 0.0,
        "n_fc": 0, "val_fc": 0.0, "firm_fc_val": defaultdict(float),
    })
    co_award = defaultdict(lambda: {"n": 0, "val": 0.0, "fc_n": 0})  # (a,b)->stats

    loc = df["location"].tolist()
    cats = df["category"].astype(str).tolist()
    budgets = df["budget"].tolist()
    years = df["infraYear"].astype(str).tolist()

    for i in range(n_rows):
        firms = parsed_cache[i]
        if not firms:
            continue
        keys = []
        for f in firms:
            k = canonical_key(f)
            if k is None:
                continue
            keys.append((k, f))
        if not keys:
            continue
        location = loc[i] if isinstance(loc[i], dict) else {}
        deo_name = (location or {}).get("province") or "Unspecified DEO"
        region = (location or {}).get("region") or "Unspecified"
        is_fc = cats[i] == FC_CATEGORY
        b = float(budgets[i] or 0.0)
        yr = years[i]

        drec = deo[deo_name]
        drec["name"] = deo_name
        drec["region"] = region
        drec["n_all"] += 1
        drec["val_all"] += b
        if is_fc:
            drec["n_fc"] += 1
            drec["val_fc"] += b

        seen = set()
        for k, f in keys:
            if k in seen:  # same firm listed twice on one contract
                continue
            seen.add(k)
            fr = firm[k]
            fr["id"] = k
            fr["name"] = canonical_name(k, f["display"])
            fr["revoked"] = fr["revoked"] or f["revoked"]
            fr["former"] = fr["former"] or f["former"]
            fr["n_all"] += 1
            fr["val_all"] += b
            fr["regions"].add(region)
            fr["years"].add(yr)
            fr["categories"][cats[i]] += 1
            d = fr["deos"][deo_name]
            d["n"] += 1
            d["val"] += b
            if is_fc:
                fr["n_fc"] += 1
                fr["val_fc"] += b
                d["fc_n"] += 1
                d["fc_val"] += b
                drec["firm_fc_val"][k] += b

        # Recorded co-award (joint venture) edges among all firms on this contract.
        uniq = sorted(seen)
        for a_i in range(len(uniq)):
            for b_i in range(a_i + 1, len(uniq)):
                pair = (uniq[a_i], uniq[b_i])
                co_award[pair]["n"] += 1
                co_award[pair]["val"] += b
                if is_fc:
                    co_award[pair]["fc_n"] += 1

    print(f"Resolved {len(firm)} firms, {len(deo)} district offices.")

    # ---- HHI per district office on flood-control awards (descriptive).
    for dname, d in deo.items():
        tot = sum(d["firm_fc_val"].values())
        if tot > 0:
            hhi = sum((v / tot * 100.0) ** 2 for v in d["firm_fc_val"].values())
        else:
            hhi = 0.0
        d["hhi_fc"] = round(hhi, 1)
        d["n_fc_firms"] = len(d["firm_fc_val"])

    # ---- Build the flood-control graph and compute networkx metrics.
    # Nodes: firms with any FC contract + DEOs with any FC contract.
    fc_firm_keys = {k for k, v in firm.items() if v["n_fc"] > 0}
    fc_deo_keys = {k for k, v in deo.items() if v["n_fc"] > 0}

    G = nx.Graph()
    for k in fc_firm_keys:
        G.add_node(("F", k))
    for k in fc_deo_keys:
        G.add_node(("D", k))
    # Recorded AWARDED_TO edges (firm <-> DEO) weighted by FC contract count.
    for k in fc_firm_keys:
        for dname, dd in firm[k]["deos"].items():
            if dd["fc_n"] > 0 and dname in fc_deo_keys:
                G.add_edge(("F", k), ("D", dname), weight=dd["fc_n"])
    # Recorded CO_AWARDED (firm <-> firm JV) edges within FC.
    for (a, b), st in co_award.items():
        if st["fc_n"] > 0 and a in fc_firm_keys and b in fc_firm_keys:
            G.add_edge(("F", a), ("F", b), weight=st["fc_n"] + 1)

    print(f"FC graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges. Computing metrics...")
    deg = dict(G.degree())
    # Approximate betweenness (k-sample) keeps runtime sane on a few-thousand-node graph.
    k_sample = min(600, G.number_of_nodes()) if G.number_of_nodes() else None
    btw = nx.betweenness_centrality(G, k=k_sample, weight=None, seed=42) if k_sample else {}
    pr = nx.pagerank(G, weight="weight") if G.number_of_nodes() else {}
    try:
        comms = nx.community.louvain_communities(G, weight="weight", seed=42)
    except Exception:
        comms = list(nx.community.greedy_modularity_communities(G))
    node_comm = {}
    for ci, cnodes in enumerate(comms):
        for nd in cnodes:
            node_comm[nd] = ci
    print(f"Louvain communities: {len(comms)}")

    def firm_node(k: str) -> dict:
        v = firm[k]
        nd = ("F", k)
        top_deos = sorted(v["deos"].items(), key=lambda kv: kv[1]["fc_val"], reverse=True)
        return {
            "id": f"C{k}",
            "key": k,
            "label": v["name"],
            "type": "Contractor",
            "revoked": v["revoked"],
            "former": v["former"],
            "n_contracts": v["n_all"],
            "value": round(v["val_all"], 2),
            "fc_contracts": v["n_fc"],
            "fc_value": round(v["val_fc"], 2),
            "n_regions": len(v["regions"]),
            "n_deos": len(v["deos"]),
            "community": node_comm.get(nd),
            "betweenness": round(btw.get(nd, 0.0), 6),
            "pagerank": round(pr.get(nd, 0.0), 6),
            "degree": deg.get(nd, 0),
            "top_deos": [
                {"deo": dn, "fc_contracts": dv["fc_n"], "fc_value": round(dv["fc_val"], 2)}
                for dn, dv in top_deos[:8] if dv["fc_n"] > 0
            ],
        }

    def deo_node(dname: str) -> dict:
        v = deo[dname]
        nd = ("D", dname)
        return {
            "id": f"D{abs(hash(dname)) % (10**10)}",
            "key": dname,
            "label": dname,
            "type": "ProcuringEntity",
            "region": v["region"],
            "n_contracts": v["n_all"],
            "value": round(v["val_all"], 2),
            "fc_contracts": v["n_fc"],
            "fc_value": round(v["val_fc"], 2),
            "hhi_fc": v["hhi_fc"],
            "concentrated": v["hhi_fc"] > HHI_HIGH,
            "n_fc_firms": v["n_fc_firms"],
            "community": node_comm.get(nd),
            "betweenness": round(btw.get(nd, 0.0), 6),
            "degree": deg.get(nd, 0),
        }

    deo_id = {dname: deo_node(dname)["id"] for dname in fc_deo_keys}

    def build_graph_json(firm_keys: set[str], deo_keys: set[str], include_colocated: bool = True) -> dict:
        fnodes = {k: firm_node(k) for k in firm_keys}
        dnodes = {k: deo_node(k) for k in deo_keys}
        fid = {k: fnodes[k]["id"] for k in firm_keys}
        did = {k: dnodes[k]["id"] for k in deo_keys}
        edges = []
        # recorded AWARDED_TO
        for k in firm_keys:
            for dname, dd in firm[k]["deos"].items():
                if dd["fc_n"] > 0 and dname in deo_keys:
                    edges.append({
                        "id": f"aw-{fid[k]}-{did[dname]}",
                        "source": fid[k], "target": did[dname],
                        "type": "AWARDED_TO", "tier": "recorded",
                        "weight": dd["fc_n"], "value": round(dd["fc_val"], 2),
                        "label": f"{dd['fc_n']} flood-control contracts",
                    })
        # recorded CO_AWARDED (JV)
        for (a, b), st in co_award.items():
            if st["fc_n"] > 0 and a in firm_keys and b in firm_keys:
                edges.append({
                    "id": f"co-{fid[a]}-{fid[b]}",
                    "source": fid[a], "target": fid[b],
                    "type": "CO_AWARDED_WITH", "tier": "recorded",
                    "weight": st["fc_n"],
                    "label": f"joint awardee on {st['fc_n']} flood-control contracts",
                })
        # derived CO_LOCATED (dashed): firm pairs sharing >=3 DEOs, both sizeable.
        if include_colocated:
            firm_deosets = {
                k: {dn for dn, dv in firm[k]["deos"].items() if dv["fc_n"] > 0 and dn in deo_keys}
                for k in firm_keys
            }
            big = [k for k in firm_keys if firm[k]["val_fc"] >= 1e9]
            seen_pairs = set()
            for i2 in range(len(big)):
                for j2 in range(i2 + 1, len(big)):
                    a, b = big[i2], big[j2]
                    if (a, b) in co_award or (b, a) in co_award:
                        continue  # already a recorded JV edge
                    shared = firm_deosets[a] & firm_deosets[b]
                    if len(shared) >= 3:
                        key = (a, b)
                        if key in seen_pairs:
                            continue
                        seen_pairs.add(key)
                        edges.append({
                            "id": f"cl-{fid[a]}-{fid[b]}",
                            "source": fid[a], "target": fid[b],
                            "type": "CO_LOCATED", "tier": "derived",
                            "weight": len(shared),
                            "label": f"inferred from records: both are top awardees in {len(shared)} shared district offices",
                        })
        nodes = list(fnodes.values()) + list(dnodes.values())
        return {"nodes": nodes, "edges": edges}

    # ---- Main scandal graph: cap to a readable size if needed.
    # Keep all FC firms if <= 3500, else top by fc_value + all revoked + all in JVs.
    if len(fc_firm_keys) <= 3500:
        main_firm_keys = set(fc_firm_keys)
    else:
        ranked = sorted(fc_firm_keys, key=lambda k: firm[k]["val_fc"], reverse=True)
        keep = set(ranked[:2800])
        keep |= {k for k in fc_firm_keys if firm[k]["revoked"]}
        keep |= {a for (a, b), st in co_award.items() if st["fc_n"] > 0 for a in (a, b)} & fc_firm_keys
        main_firm_keys = keep
    main_deo_keys = set(fc_deo_keys)
    graph_main = build_graph_json(main_firm_keys, main_deo_keys, include_colocated=True)

    # ---- Topnotch Catalyst ego graph (demo target): 2-hop.
    TOPNOTCH_ID = "34061"
    ego_firms = {TOPNOTCH_ID} if TOPNOTCH_ID in firm else set()
    ego_deos = set()
    if ego_firms:
        for dn, dv in firm[TOPNOTCH_ID]["deos"].items():
            if dv["fc_n"] > 0:
                ego_deos.add(dn)
        for (a, b), st in co_award.items():
            if st["fc_n"] > 0 and TOPNOTCH_ID in (a, b):
                other = b if a == TOPNOTCH_ID else a
                if other in fc_firm_keys:
                    ego_firms.add(other)
        # second hop: co-awardees' DEOs (limited)
        for k in list(ego_firms):
            for dn, dv in firm[k]["deos"].items():
                if dv["fc_n"] > 0:
                    ego_deos.add(dn)
    graph_topnotch = build_graph_json(ego_firms, ego_deos & fc_deo_keys, include_colocated=True)

    # ---- Scandal core graph: deliberately small and legible (not the full
    # dense network). The firms at the centre of the scandal + the district
    # offices they SHARE, so the picture reads as concentration, not a hairball.
    NAMED = {"34061", "31762", "38958", "39196", "40908", "45914", "49129",
             "52351", "45002", "49128", "15906", "46535", "48517", "34105",
             "33234", "22465"}  # the named scandal firms
    scandal_firm_keys = set(sorted(fc_firm_keys, key=lambda k: firm[k]["val_fc"], reverse=True)[:24])
    scandal_firm_keys |= {k for k in fc_firm_keys if firm[k]["revoked"]}
    scandal_firm_keys |= (NAMED & fc_firm_keys)
    # Each firm contributes only its top FC district offices; keep offices where
    # at least two scandal firms concentrate, plus the highest-value few.
    deo_hits: dict[str, int] = defaultdict(int)
    deo_val: dict[str, float] = defaultdict(float)
    for k in scandal_firm_keys:
        tops = sorted(
            [(dn, dv) for dn, dv in firm[k]["deos"].items() if dv["fc_n"] > 0 and dn in fc_deo_keys],
            key=lambda x: x[1]["fc_val"], reverse=True)[:6]
        for dn, dv in tops:
            deo_hits[dn] += 1
            deo_val[dn] += dv["fc_val"]
    scandal_deo_keys = {dn for dn, h in deo_hits.items() if h >= 2}
    extra = sorted([dn for dn in deo_hits if dn not in scandal_deo_keys],
                   key=lambda d: deo_val[d], reverse=True)[:36]
    scandal_deo_keys |= set(extra)
    scandal_deo_keys &= fc_deo_keys
    graph_scandal = build_graph_json(scandal_firm_keys, scandal_deo_keys, include_colocated=True)

    # ---- Full search index: every firm + every DEO (summary only).
    entities = []
    for k, v in firm.items():
        top_cat = max(v["categories"].items(), key=lambda kv: kv[1])[0] if v["categories"] else None
        entities.append({
            "id": f"C{k}", "key": k, "label": v["name"], "type": "Contractor",
            "revoked": v["revoked"], "former": v["former"],
            "n_contracts": v["n_all"], "value": round(v["val_all"], 2),
            "fc_contracts": v["n_fc"], "fc_value": round(v["val_fc"], 2),
            "n_regions": len(v["regions"]), "n_deos": len(v["deos"]),
            "top_category": top_cat,
            "top_deos": [
                {"deo": dn, "contracts": dv["n"], "value": round(dv["val"], 2),
                 "fc_contracts": dv["fc_n"], "fc_value": round(dv["fc_val"], 2)}
                for dn, dv in sorted(v["deos"].items(), key=lambda kv: kv[1]["val"], reverse=True)[:10]
            ],
            "coawardees": sorted(
                [{"key": (b if a == k else a),
                  "name": firm[(b if a == k else a)]["name"],
                  "shared": st["n"], "fc_shared": st["fc_n"]}
                 for (a, b), st in co_award.items() if k in (a, b)],
                key=lambda x: x["shared"], reverse=True)[:15],
        })
    for dname, v in deo.items():
        entities.append({
            "id": deo_id.get(dname, f"D{abs(hash(dname)) % (10**10)}"),
            "key": dname, "label": dname, "type": "ProcuringEntity",
            "region": v["region"], "n_contracts": v["n_all"], "value": round(v["val_all"], 2),
            "fc_contracts": v["n_fc"], "fc_value": round(v["val_fc"], 2),
            "hhi_fc": v.get("hhi_fc", 0.0), "concentrated": v.get("hhi_fc", 0.0) > HHI_HIGH,
            "n_fc_firms": v.get("n_fc_firms", 0),
        })
    entities.sort(key=lambda e: e["value"], reverse=True)

    # ---- Headline stats (reconciled, computed once — no JV double count).
    fc_mask = df["category"].astype(str) == FC_CATEGORY
    fc_value = float(df.loc[fc_mask, "budget"].sum())
    fc_count = int(fc_mask.sum())
    revoked_firms = [k for k, v in firm.items() if v["revoked"]]
    revoked_contracts = int(df["contractor"].astype(str).str.contains(r"\[REVOKED\]", regex=True, na=False).sum())
    revoked_value = float(df.loc[df["contractor"].astype(str).str.contains(r"\[REVOKED\]", regex=True, na=False), "budget"].sum())
    concentrated_deos = sorted(
        [{"deo": dn, "region": deo[dn]["region"], "hhi": deo[dn]["hhi_fc"],
          "fc_value": round(deo[dn]["val_fc"], 2), "fc_contracts": deo[dn]["n_fc"],
          "n_firms": deo[dn]["n_fc_firms"]}
         for dn in fc_deo_keys if deo[dn]["hhi_fc"] > HHI_HIGH],
        key=lambda x: x["hhi"], reverse=True)
    top_fc = sorted(
        [{"key": k, "name": firm[k]["name"], "revoked": firm[k]["revoked"],
          "fc_value": round(firm[k]["val_fc"], 2), "fc_contracts": firm[k]["n_fc"]}
         for k in fc_firm_keys],
        key=lambda x: x["fc_value"], reverse=True)[:25]

    stats = {
        "generated_note": "Descriptive statistics derived from public DPWH records. Patterns may have legitimate explanations.",
        "source": {
            "name": "DPWH Transparency Portal via BetterGov.PH (HuggingFace bettergovph/dpwh-transparency-data)",
            "license": "CC0 1.0 Universal (public domain)",
            "url": "https://huggingface.co/datasets/bettergovph/dpwh-transparency-data",
        },
        "totals": {
            "contracts": n_rows,
            "total_value": round(total_value, 2),
            "contractors": len(firm),
            "district_offices": len(deo),
        },
        "flood_control": {
            "category": FC_CATEGORY,
            "contracts": fc_count,
            "value": round(fc_value, 2),
            "firms": len(fc_firm_keys),
            "district_offices": len(fc_deo_keys),
        },
        "revoked": {
            "firms": len(revoked_firms),
            "contracts": revoked_contracts,
            "value": round(revoked_value, 2),
        },
        "concentration": {
            "threshold": HHI_HIGH,
            "concentrated_fc_deos": len(concentrated_deos),
            "top_concentrated": concentrated_deos[:15],
        },
        "communities": len(comms),
        "top_flood_control_firms": top_fc,
        "graph_main_nodes": len(graph_main["nodes"]),
        "graph_main_edges": len(graph_main["edges"]),
    }

    # ---- Write outputs.
    def dump(name: str, obj) -> None:
        p = OUT / name
        p.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))
        print(f"  wrote {name}  ({p.stat().st_size/1e6:.2f} MB)")

    stats["graph_scandal_nodes"] = len(graph_scandal["nodes"])
    stats["graph_scandal_edges"] = len(graph_scandal["edges"])

    dump("stats.json", stats)
    dump("graph-scandal.json", graph_scandal)
    dump("graph-main.json", graph_main)
    dump("graph-topnotch.json", graph_topnotch)
    dump("entities.json", {"entities": entities, "count": len(entities)})

    print("\nReconciliation:")
    print(f"  total contracts      : {n_rows}")
    print(f"  total value (T)      : {total_value/1e12:.3f}")
    print(f"  flood-control        : {fc_count} contracts / PHP {fc_value/1e12:.3f}T")
    print(f"  revoked-license      : {len(revoked_firms)} firms / {revoked_contracts} contracts / PHP {revoked_value/1e9:.1f}B")
    print(f"  concentrated FC DEOs : {len(concentrated_deos)} (HHI>{HHI_HIGH})")
    if TOPNOTCH_ID in firm:
        t = firm[TOPNOTCH_ID]
        print(f"  Topnotch(34061)      : {t['n_all']} contracts / PHP {t['val_all']/1e9:.2f}B  (FC: {t['n_fc']} / {t['val_fc']/1e9:.2f}B)")
    else:
        print("  Topnotch(34061)      : NOT FOUND")


if __name__ == "__main__":
    main()
