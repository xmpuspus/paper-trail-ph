// paper-trail-ph — graph schema and constraints
// NO DATA IS SEEDED. All data must be loaded via the pipeline from real sources:
//   - DPWH Transparency Portal (https://transparency.dpwh.gov.ph)
//   - PhilGEPS procurement data (https://notices.philgeps.gov.ph)
//   - PSA demographic data (https://openstat.psa.gov.ph)
//   - COA audit reports (https://coa.gov.ph/reports/annual-audit-reports)

// --- Constraints ---
CREATE CONSTRAINT IF NOT EXISTS FOR (c:Contract) REQUIRE c.reference_number IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (co:Contractor) REQUIRE co.registration_number IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (a:Agency) REQUIRE a.name IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (m:Municipality) REQUIRE m.psgc_code IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (p:Politician) REQUIRE (p.name, p.province) IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (pf:PoliticalFamily) REQUIRE (pf.name, pf.province) IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (b:Bill) REQUIRE b.number IS UNIQUE;

// --- Indexes ---
CREATE INDEX IF NOT EXISTS FOR (c:Contract) ON (c.amount);
CREATE INDEX IF NOT EXISTS FOR (c:Contract) ON (c.status);
CREATE INDEX IF NOT EXISTS FOR (c:Contract) ON (c.award_date);
CREATE INDEX IF NOT EXISTS FOR (co:Contractor) ON (co.name);
CREATE INDEX IF NOT EXISTS FOR (a:Agency) ON (a.department);
CREATE INDEX IF NOT EXISTS FOR (m:Municipality) ON (m.province);
CREATE INDEX IF NOT EXISTS FOR (m:Municipality) ON (m.region);
CREATE INDEX IF NOT EXISTS FOR (af:AuditFinding) ON (af.severity);
CREATE INDEX IF NOT EXISTS FOR (af:AuditFinding) ON (af.type);

// --- Node labels (for reference, no data created) ---
// Contract: reference_number, title, amount, procurement_method, award_date, notice_date, status, bid_count, category
// Contractor: name, registration_number, address, classification, total_contracts, total_value
// Agency: name, type, department, annual_budget
// Municipality: name, province, region, population, income_class, psgc_code
// Politician: name, position, term, party, province, saln_net_worth, dynasty_flag
// PoliticalFamily: name, province, member_count, dynasty_score, dynasty_type
// Person: name, role
// AuditFinding: type, severity, amount, year, description, recommendation, recommendation_status
// Bill: number, title, status, filed_date, committee, significance
// CampaignDonation: amount, election_year, election_type, source_entity, recipient
// BlacklistEntry: offense, sanction_period, procuring_entity, sanction_date
// SALNRecord: year, net_worth, real_property, personal_property, liabilities, annual_income
// ProjectSite: latitude, longitude, radius_m
// SatelliteObservation: date, source, ndbi_value, ndvi_value, change_detected, change_magnitude
// VerificationResult: status, confidence, before_ndbi, after_ndbi, before_ndvi, after_ndvi

// --- Relationship types (for reference, no data created) ---
// (:Agency)-[:PROCURED]->(:Contract)
// (:Contract)-[:AWARDED_TO]->(:Contractor)
// (:Contractor)-[:BID_ON]->(:Contract)
// (:Contractor)-[:CO_BID_WITH]->(:Contractor)
// (:Contractor)-[:SUBCONTRACTED_TO]->(:Contractor)
// (:Contractor)-[:OWNED_BY]->(:Person)
// (:Person)-[:FAMILY_OF]->(:Politician)
// (:Politician)-[:MEMBER_OF]->(:PoliticalFamily)
// (:Politician)-[:GOVERNS]->(:Municipality)
// (:Municipality)-[:HAS_AGENCY]->(:Agency)
// (:Contractor)-[:LOCATED_IN]->(:Municipality)
// (:Contractor)-[:ASSOCIATED_WITH]->(:Contractor)
// (:Agency)-[:AUDITED]->(:AuditFinding)
// (:AuditFinding)-[:INVOLVES_OFFICIAL]->(:Politician)
// (:Politician)-[:AUTHORED]->(:Bill)
// (:Politician)-[:CO_AUTHORED_WITH]->(:Politician)
// (:Contractor)-[:DONATED_TO]->(:CampaignDonation)
// (:CampaignDonation)-[:DONATED_TO]->(:Politician)
// (:Contractor)-[:BLACKLISTED]->(:BlacklistEntry)
// (:Politician)-[:DECLARED_WEALTH]->(:SALNRecord)
// (:Contractor)-[:RE_REGISTERED_AS]->(:Contractor)
// (:Contractor)-[:SAME_ADDRESS_AS]->(:Contractor)
// (:Contractor)-[:SHARES_DIRECTOR_WITH]->(:Contractor)
// (:Politician)-[:ALLIED_WITH]->(:Politician)
// (:Contract)-[:HAS_SITE]->(:ProjectSite)
// (:ProjectSite)-[:OBSERVED_AT]->(:SatelliteObservation)
// (:Contract)-[:VERIFIED_BY]->(:VerificationResult)
