// Uniqueness constraints
CREATE CONSTRAINT contract_ref IF NOT EXISTS FOR (c:Contract) REQUIRE c.reference_number IS UNIQUE;
CREATE CONSTRAINT contractor_reg IF NOT EXISTS FOR (c:Contractor) REQUIRE c.registration_number IS UNIQUE;
CREATE CONSTRAINT agency_name IF NOT EXISTS FOR (a:Agency) REQUIRE a.name IS UNIQUE;
CREATE CONSTRAINT municipality_psgc IF NOT EXISTS FOR (m:Municipality) REQUIRE m.psgc_code IS UNIQUE;
CREATE CONSTRAINT bill_number IF NOT EXISTS FOR (b:Bill) REQUIRE b.number IS UNIQUE;

// Full-text search indexes
CREATE FULLTEXT INDEX entity_search IF NOT EXISTS FOR (n:Contractor|Agency|Politician|Municipality) ON EACH [n.name];

// B-tree indexes for range queries
CREATE INDEX contract_amount IF NOT EXISTS FOR (c:Contract) ON (c.amount);
CREATE INDEX contract_date IF NOT EXISTS FOR (c:Contract) ON (c.award_date);
CREATE INDEX contract_method IF NOT EXISTS FOR (c:Contract) ON (c.procurement_method);
CREATE INDEX audit_year IF NOT EXISTS FOR (a:AuditFinding) ON (a.year);
CREATE INDEX politician_province IF NOT EXISTS FOR (p:Politician) ON (p.province);

// Note: Property existence constraints require Enterprise Edition
// Enforced at application level instead
