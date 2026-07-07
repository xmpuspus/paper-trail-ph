"""Build the geographic jurisdiction layer.

Flood-control contract value by region, computed from the DPWH transparency
record's own location.region field. This is low-risk scaffolding: it maps the
money to jurisdictions using the field already in the record, and it reconciles
to the same flood-control total as the rest of the site.

Honestly deferred, not faked:
- Canonical PSGC province/municipality codes are not joined. The PSA publishes
  PSGC only as manual downloads behind Cloudflare (see scripts/collectors/psgc.py),
  so there is no automated join. Jurisdiction here uses the DPWH record's region.
- A point-level project map is a natural next step (the record carries latitude
  and longitude on most contracts) but is not built in this release.

    python3 scripts/build_geography.py

writes public/data/geography.json
"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "public" / "data"
PARQUET = ROOT / "data" / "raw" / "dpwh" / "dpwh_transparency_data.parquet"
FC_CATEGORY = "Flood Control and Drainage"
DISCLAIMER = "Statistical indicators derived from public data. Patterns may have legitimate explanations."


def main() -> None:
    df = pd.read_parquet(PARQUET, columns=["category", "location", "budget"])
    df["budget"] = pd.to_numeric(df["budget"], errors="coerce").fillna(0.0)
    fc = df[df["category"] == FC_CATEGORY].copy()
    fc["region"] = fc["location"].map(lambda d: d.get("region") if isinstance(d, dict) else None)

    total = float(fc["budget"].sum())
    grouped = (
        fc.groupby("region", dropna=True)
        .agg(fc_value=("budget", "sum"), fc_contracts=("budget", "size"))
        .sort_values("fc_value", ascending=False)
    )

    by_region = [
        {
            "region": region,
            "fc_value": round(float(row.fc_value), 2),
            "fc_contracts": int(row.fc_contracts),
            "share_pct": round(float(row.fc_value) / total * 100.0, 1),
        }
        for region, row in grouped.iterrows()
    ]

    null_region = int(fc["region"].isna().sum())

    out = {
        "_meta": {
            "purpose": "Flood-control contract value by region, computed from the DPWH transparency record's own location field. The jurisdiction breakdown of the money.",
            "method_note": "Region is the DPWH record's location.region. Canonical PSGC province and municipality codes are not joined: the PSA publishes PSGC only as manual downloads behind Cloudflare, so there is no automated join. A point-level map is a natural next step; the record carries latitude and longitude on most contracts.",
            "fc_total": round(total, 2),
            "fc_contracts": int(fc.shape[0]),
            "regions": len(by_region),
            "unmapped_contracts": null_region,
            "disclaimer": DISCLAIMER,
        },
        "by_region": by_region,
    }

    (DATA / "geography.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"wrote public/data/geography.json: {len(by_region)} regions, "
          f"FC total {total:,.0f}, {null_region} unmapped")
    for r in by_region[:5]:
        print(f"  {r['region']}: {r['fc_value']/1e9:.2f}B ({r['share_pct']}%), {r['fc_contracts']} contracts")


if __name__ == "__main__":
    main()
