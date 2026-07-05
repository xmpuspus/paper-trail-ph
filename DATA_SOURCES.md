# Data Sources

Every data point in Paper Trail PH comes from a verified public source. This document lists all sources, their access methods, and known limitations.

## Primary Data Sources

### 1. DPWH Transparency Portal

- **URL:** https://transparency.dpwh.gov.ph/
- **Data:** Infrastructure project contracts, contractors, budgets, progress, geolocation
- **Access method:** Pre-scraped Parquet dataset on HuggingFace (the live API is Cloudflare-protected)
- **HuggingFace dataset:** https://huggingface.co/datasets/bettergovph/dpwh-transparency-data
- **License:** CC0 1.0 Universal (public domain)
- **Maintainer:** BetterGov.PH (https://bettergov.ph)
- **Original scraper:** https://github.com/csiiiv/dpwh-transparency-data-api-scraper
- **Files:**
  - `dpwh_transparency_data.parquet` (24.3 MB) — base dataset
  - `dpwh_transparency_data_all_details.parquet` (115 MB) — detailed dataset
- **Pipeline command:** `python3 scripts/pipeline.py collect --source dpwh`
- **Limitations:** Cloudflare blocks direct API access. Dataset freshness depends on scraper update frequency.

### 2. PhilGEPS (Philippine Government Electronic Procurement System)

- **URL:** https://notices.philgeps.gov.ph / https://open.philgeps.gov.ph/
- **Data:** Government procurement notices, contract awards, bidders
- **Access method:** Manual XLSX download (no public API)
- **License:** Philippine government public records
- **Pipeline command:** `python3 scripts/pipeline.py collect --source philgeps`
- **Limitations:** No API. Excel files must be manually downloaded and placed in `data/raw/philgeps/`. Column names vary across releases — the parser handles multiple formats.

### 3. Open Congress API (BetterGov.PH)

- **URL:** https://open-congress-api.bettergov.ph/api/v1
- **API docs:** https://open-congress-api.bettergov.ph/api/scalar
- **Data:** Philippine legislators (senators and representatives), bills, committees
- **Access method:** REST API (public, no authentication required)
- **License:** Open data, maintained by BetterGov.PH volunteers
- **Coverage:** Congresses 8-20, 165,162 bills, 1,179 legislators, 200 committees
- **Pipeline command:** `python3 scripts/pipeline.py collect --source congress`
- **Limitations:** Data is manually encoded by volunteers. The API includes a disclaimer about potential inaccuracies. Rate limit: 2 requests/second.

### 4. PSA Philippine Standard Geographic Code (PSGC)

- **URL:** https://psa.gov.ph/classification/psgc
- **Data:** Official geographic codes for regions, provinces, municipalities, barangays
- **Access method:** Manual download (Excel/CSV from PSA website, Cloudflare-protected)
- **License:** Philippine government public records
- **Pipeline command:** `python3 scripts/pipeline.py collect --source psgc`
- **Limitations:** Cloudflare blocks automated download. Must be manually obtained.

### 5. COMELEC Election Results

- **URL:** https://comelec.gov.ph/
- **Data:** Official certified election results
- **Access method:** Manual download from COMELEC or partner sites
- **License:** Philippine government public records
- **Pipeline command:** `python3 scripts/pipeline.py collect --source dynasties`
- **Limitations:** No API. Data must be manually downloaded. Dynasty detection runs on congress member data as a fallback.

## Secondary / Reference Sources

### 6. Philippine Open Data Portal

- **URL:** https://data.gov.ph
- **Data:** Various government datasets
- **Status:** Accessible (nginx, HSTS enabled)

### 7. COA Annual Audit Reports

- **URL:** https://coa.gov.ph/reports/annual-audit-reports
- **Data:** Commission on Audit findings for government agencies
- **Status:** Phase 2 — unstructured PDF extraction (pilot: 10-20 reports)

## Published Research (for context, not seeded as data)

These studies provide context for dynasty analysis. Their findings are referenced in documentation only — no statistics from these papers are hardcoded in the database or frontend.

### Mendoza et al. (2019)
- **Citation:** Ronald U. Mendoza, Leonardo M. Jaminola, and Jurel K. Yap. "From Fat to Obese: Political Dynasties after the 2019 Midterm Elections." Ateneo School of Government Working Paper, September 2019. SSRN: 3449201.
- **Key finding:** Fat dynasty share of local posts grew from 19% (1988) to 29% (2017 election data).
- **Key finding:** Approximately 67% of House seats held by members of "fat" dynasties (families with multiple simultaneous elected members).

### Querubin (2016)
- **Citation:** Pablo Querubin. "Family and Politics: Dynastic Persistence in the Philippines." Quarterly Journal of Political Science, Vol. 11, No. 2, pp. 151-181, 2016.
- **Note:** Published in QJPS (not APSR as sometimes misattributed).
- **Key finding:** Average of 31.3% of all congressmen were replaced by relatives (1995-2007).

### Mendoza et al. (2016)
- **Citation:** Ronald U. Mendoza, Edsel L. Beja Jr., Victor S. Venida, and David B. Yap. "Political Dynasties and Poverty: Measurement and Evidence of Linkages in the Philippines." Oxford Development Studies, Vol. 44, No. 2, pp. 189-201, April 2016.
- **Key finding:** Positive correlation between dynasty concentration and poverty incidence. Pearson r value reported in paper (paywalled — full verification requires journal access).

### PCIJ Dynasty Database (2024-2025)
- **Source:** Philippine Center for Investigative Journalism
- **Governor data (Dec 8, 2024):** 71 of 82 provincial governors (86.6%) belong to political families.
- **Representative data (Oct 2024):** 8 in 10 district representatives come from political families.
- **City mayor data (Jan 26, 2025):** 113 of 149 city mayors (75.8%) from political families.
- **Note:** Different installments published across Oct 2024 - Jan 2025. Dates above are per-article.

## Data Integrity Principles

1. **No hardcoded data.** All data in the graph comes from the pipeline (`scripts/pipeline.py`), not from seed files or constants.
2. **No fabricated statistics.** The `INSIGHT_BANNERS` array in `constants.ts` is empty — populated dynamically from actual graph analysis, not hardcoded.
3. **Source attribution.** Every record loaded into Neo4j includes a `data_source` field tracing it to its origin.
4. **Disclaimer on every page.** Red flags are statistical indicators, not accusations of wrongdoing.
