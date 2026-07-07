"""Build the recorded SEC corporate-registry layer.

Philippine SEC company data is not obtainable by automation: eSEARCH is a
paid, authenticated document channel, bulk scraping is not authorized under the
Revised Corporation Code, and the SEC API Marketplace is subscription-gated with
no public developer endpoint. So this layer is NOT scraped.

Instead it curates the primary SEC documents that PCIJ published for the top
flood-control contractors (General Information Sheets and Articles of
Incorporation, at pcij.org/2025/08/30/flood-control-records). Each figure below
was transcribed from the firm's own GIS PDF and links back to that document.
This is a recorded tier (recorded: SEC GIS, via PCIJ), kept separate from the
Node2Vec predicted tier.

Derived fields (contract-to-capital ratio, shared registered office, the
re-registration flag) are computed here from the transcribed capital and the
flood-control value already baked into graph-main.json, so every number on the
site reconciles to the same source. No figure is hand-written into the UI.

    python3 scripts/build_sec.py

writes public/data/sec.json
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "public" / "data"

# PCIJ is the provenance anchor: it obtained and published the SEC documents.
PCIJ_INDEX = "https://pcij.org/2025/08/30/flood-control-records/"

# Curated primary-source records, transcribed from each firm's SEC GIS PDF as
# published by PCIJ. paid_up_capital is the exact TOTAL PAID-UP figure on the
# 2025 GIS. sec_reg_no is verbatim; reg_year is the year encoded in the SEC
# registration number (SEC numbers carry the registration year). Officers are
# surfaced only where they corroborate an already-public owner (family control)
# or a notable absence; the full private board is not republished.
RECORDS = {
    "15906": {
        "name": "Sunwest, Inc.",
        "sec_reg_no": "I199700399",
        "reg_year": 1997,
        "company_type": "Stock corporation",
        "paid_up_capital": 5_562_500_000,
        "capital_note": "Total paid-up capital per the 2025 SEC GIS. Sunwest is well capitalized; the contract-to-capital ratio is low.",
        "registered_office": "Lidong, Sto. Domingo, Albay",
        "region": "Region V (Bicol)",
        "officer_note": "Elizaldy \"Zaldy\" Co, the reported co-founder, is not among the officers listed on the 2025 GIS.",
        "ratio": True,
        "gis_url": "https://drive.google.com/file/d/1i8Y5zkYa7UinqOVeWAbPq-CR76h3vkmY/view",
        "aoi_url": "https://drive.google.com/file/d/10SR-5iSmgjna2y0i__nOwWVx7t5hu56S/view",
    },
    "23385": {
        "name": "Hi-Tone Construction and Development Corporation",
        "sec_reg_no": "CS200726051",
        "reg_year": 2007,
        "company_type": "Stock corporation",
        "paid_up_capital": None,  # not legible in the published GIS; omitted, not guessed
        "capital_note": "Paid-up capital was not legible in the published GIS and is omitted rather than estimated.",
        "registered_office": "Lidong, Sto. Domingo, Albay",
        "region": "Region V (Bicol)",
        "ratio": False,
        "gis_url": "https://drive.google.com/file/d/1DgodTsIJIFOqlRPqS3l0NCqRMImq5Hma/view",
        "aoi_url": "https://drive.google.com/file/d/1fXNrDdmcRXwJ6D5EvVLVaRv3YZCCsRBF/view",
    },
    "34105": {
        "name": "Centerways Construction and Development Inc.",
        "sec_reg_no": "CS200926069",
        "reg_year": 2009,
        "company_type": "Stock corporation",
        "paid_up_capital": 45_000_000,
        "capital_note": "Total paid-up capital per the 2025 SEC GIS. Reported at about ₱1.25M at incorporation and later increased (Daily Tribune, Rappler).",
        "registered_office": "Sitio Sip-ac, Cabid-an, Sorsogon City",
        "region": "Region V (Bicol)",
        "president": "Lawrence R. Lubiano",
        "family_control": "Family-held: three Lubiano directors on the 2025 GIS (Lawrence R., Cynthia R., Lemuel R. Lubiano).",
        "ratio": True,
        "gis_url": "https://drive.google.com/file/d/1X2oXDsCjjNxkMSqCwfGxIZlGylEPNx1d/view",
        "aoi_url": "https://drive.google.com/file/d/1KA1T297aUyE_fs1pYfjaDAtg7RCEmwor/view",
    },
    "22465": {
        "name": "Legacy Construction Corporation",
        "sec_reg_no": "CS201615002",
        "reg_year": 2016,
        "company_type": "Stock corporation",
        "paid_up_capital": 380_000_000,
        "capital_note": "Total paid-up capital per the 2025 SEC GIS.",
        "registered_office": "1001 10th Flr, Tektite Tower, West Exchange Rd, San Antonio, Pasig City",
        "region": "NCR",
        "president": "Alex H. Abelido",
        "family_control": "Family-held: Alex H. Abelido (president) and Raymond H. Abelido (vice-president) on the 2025 GIS.",
        "ratio": True,
        "gis_url": "https://drive.google.com/file/d/16nkKZVa4X2YMri97iGvdjV7uoPYRH5dq/view",
        "aoi_url": "https://drive.google.com/file/d/1gBTwNRAVHYLqo-p--0xWWZ50xj1F_LID/view",
    },
    "33234": {
        "name": "M.G. Samidan Construction and Development Corporation",
        "sec_reg_no": "CS201903662",
        "reg_year": 2019,
        "company_type": "Stock corporation",
        "paid_up_capital": 250_000,
        "capital_note": "Total paid-up capital per the 2025 SEC GIS. Corroborates the ₱250,000-capital figure first reported by the Inquirer.",
        "registered_office": "M.G. Samidan Compound, Km 100, Sinto, Bauko, Mountain Province",
        "region": "CAR",
        "president": "Marjorie Samidan",
        "family_control": "Family-held: the four incorporators are all Samidan (Marjorie, Kliff, Kevin, Kamille).",
        "ratio": True,
        "gis_url": "https://drive.google.com/file/d/1xGDco4Zh5Y_7IBueRFjiy36NDQnEDGtc/view",
        "aoi_url": None,
    },
    "46535": {
        "name": "Wawao Builders Corporation",
        "sec_reg_no": "2025040198133-04",
        # The 2025 SEC number is an amendment reference, not an incorporation year,
        # so no registration year is asserted. News reporting: the firm has held DPWH
        # contracts since 2019 and amended its articles in May 2025 to move its office
        # to Occidental Mindoro. It is one continuous company, not a post-ban re-registration.
        "reg_year": None,
        "company_type": "Stock corporation",
        "paid_up_capital": 50_000_000,
        "capital_note": "Total paid-up capital per the firm's SEC GIS. The firm has held DPWH contracts since 2019; its 2025 SEC filing is an amendment of the articles of incorporation (an office move to Occidental Mindoro), not a new company.",
        "registered_office": "Rizal St, Brgy. Poblacion I, San Jose, Occidental Mindoro",
        "region": "MIMAROPA (Region IV-B)",
        "ratio": True,
        "gis_url": "https://drive.google.com/file/d/1okskHvdqbgrsYhMHdNwE699a_rCO8cn5/view",
        "aoi_url": None,
    },
}

DISCLAIMER = "Statistical indicators derived from public data. Patterns may have legitimate explanations."


def locality_key(addr: str) -> str:
    """Normalize a registered office to its barangay/municipality/province tail
    for co-location detection. Drops street/building and punctuation."""
    s = re.sub(r"[^A-Za-z0-9, ]+", " ", addr or "").upper()
    # Keep the last three comma-separated parts (roughly brgy, municipality, province).
    parts = [p.strip() for p in s.split(",") if p.strip()]
    tail = parts[-3:] if len(parts) >= 3 else parts
    return " / ".join(re.sub(r"\s+", " ", p) for p in tail)


def main() -> None:
    graph = json.loads((DATA / "graph-main.json").read_text())
    by_key = {}
    for n in graph["nodes"]:
        k = str(n.get("key"))
        if k not in by_key:
            by_key[k] = n

    firms = {}
    ratios = []
    localities = {}

    for key, rec in RECORDS.items():
        node = by_key.get(key)
        if node is None:
            raise SystemExit(f"SEC record {key} ({rec['name']}) has no firm in graph-main.json")
        fc_value = float(node.get("fc_value") or 0.0)

        entry = {
            "key": key,
            "name": rec["name"],
            "graph_label": node.get("label"),
            "sec_reg_no": rec["sec_reg_no"],
            "reg_year": rec["reg_year"],
            "company_type": rec["company_type"],
            "paid_up_capital": rec["paid_up_capital"],
            "capital_note": rec.get("capital_note"),
            "registered_office": rec["registered_office"],
            "region": rec["region"],
            "fc_value": round(fc_value, 2),
            "fc_contracts": node.get("fc_contracts"),
            "president": rec.get("president"),
            "family_control": rec.get("family_control"),
            "officer_note": rec.get("officer_note"),
            "gis_url": rec.get("gis_url"),
            "aoi_url": rec.get("aoi_url"),
            "tier": "recorded_sec",
        }

        # Contract-to-capital ratio: only where the capital belongs to the entity
        # that won the recorded contracts, and only from a transcribed capital figure.
        cap = rec.get("paid_up_capital")
        if rec.get("ratio") and cap:
            ratio = fc_value / cap
            entry["contract_to_capital"] = round(ratio, 1)
            ratios.append({
                "key": key,
                "name": rec["name"],
                "fc_value": round(fc_value, 2),
                "paid_up_capital": cap,
                "ratio": round(ratio, 1),
                "note": rec.get("capital_note"),
            })

        # Re-registration flag (structural, sourced).
        if rec.get("re_registration"):
            entry["re_registration"] = rec["re_registration"]

        firms[key] = entry
        localities.setdefault(locality_key(rec["registered_office"]), []).append(key)

    # Co-location: two or more recorded firms sharing a registered locality.
    co_location = []
    for loc, keys in localities.items():
        if len(keys) >= 2:
            co_location.append({
                "locality": firms[keys[0]]["registered_office"],
                "keys": keys,
                "firms": [firms[k]["name"] for k in keys],
                "note": "Registered principal office in the same barangay/municipality per their 2025 SEC GIS. A recorded co-location indicator, not evidence of a shared operation.",
            })

    re_registrations = [
        {"key": k, "name": firms[k]["name"], **firms[k]["re_registration"]}
        for k in firms if "re_registration" in firms[k]
    ]

    ratios.sort(key=lambda r: r["ratio"], reverse=True)

    out = {
        "_meta": {
            "purpose": "Recorded SEC corporate-registry facts for top flood-control contractors, transcribed from the primary General Information Sheets published by PCIJ. A recorded tier, kept separate from the Node2Vec predicted tier.",
            "tier": "recorded (SEC GIS, via PCIJ)",
            "obtainability_note": "Philippine SEC company data is not machine-readable in bulk: eSEARCH is a paid, authenticated document channel, automated scraping is not authorized under the Revised Corporation Code, and the SEC API Marketplace is subscription-gated. This layer is curated from the primary SEC documents PCIJ obtained and published, not scraped.",
            "provenance": {"label": "PCIJ: Records of flood-control contractors (SEC GIS and Articles of Incorporation)", "url": PCIJ_INDEX},
            "compiled": "2026-07",
            "count": len(firms),
            "disclaimer": DISCLAIMER,
            "presumption": "Charges and flags are allegations under the presumption of innocence. These are corporate-registry facts and structural indicators, not findings of wrongdoing about any person or firm.",
        },
        "firms": firms,
        "findings": {
            "contract_to_capital": {
                "definition": "Ratio of a firm's total flood-control contract value on the DPWH record to its paid-up capital per its 2025 SEC GIS. Contract totals span 2021 to 2025; paid-up capital is the latest 2025 figure, which for firms that raised capital over time is the most conservative denominator. A statistical indicator only.",
                "items": ratios,
            },
            "co_location": {
                "definition": "Recorded firms whose registered principal office is in the same barangay/municipality per their 2025 SEC GIS.",
                "items": co_location,
            },
            "re_registration": {
                "definition": "A firm registered with the SEC after a recorded blacklist or revocation, per the registration date on its own GIS.",
                "items": re_registrations,
            },
        },
    }

    (DATA / "sec.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"wrote public/data/sec.json: {len(firms)} firms, "
          f"{len(ratios)} contract-to-capital ratios, "
          f"{len(co_location)} co-location clusters, "
          f"{len(re_registrations)} re-registration flags")
    for r in ratios:
        print(f"  {r['name']}: {r['ratio']:,}x  (fc {r['fc_value']:,.0f} / capital {r['paid_up_capital']:,})")
    for c in co_location:
        print(f"  co-location: {', '.join(c['firms'])} @ {c['locality']}")


if __name__ == "__main__":
    main()
