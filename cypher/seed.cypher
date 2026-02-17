// paper-trail-ph — initial graph data
// Philippine government procurement, political families, audit findings
// Sources: PhilGEPS, Open Congress API, COA Annual Reports, PSA PSGC

// --- Political Families ---
CREATE (pf1:PoliticalFamily {name: "Revilla", province: "Cavite", member_count: 4, dynasty_score: 0.85, dynasty_type: "fat"})
CREATE (pf2:PoliticalFamily {name: "Estrada", province: "Manila/San Juan", member_count: 5, dynasty_score: 0.92, dynasty_type: "fat"})
CREATE (pf3:PoliticalFamily {name: "Villar", province: "Las Pinas/Bulacan", member_count: 3, dynasty_score: 0.78, dynasty_type: "thin"})
CREATE (pf4:PoliticalFamily {name: "Marcos", province: "Ilocos Norte", member_count: 6, dynasty_score: 0.95, dynasty_type: "fat"})
CREATE (pf5:PoliticalFamily {name: "Duterte", province: "Davao", member_count: 4, dynasty_score: 0.88, dynasty_type: "fat"})
CREATE (pf6:PoliticalFamily {name: "Binay", province: "Makati", member_count: 3, dynasty_score: 0.82, dynasty_type: "fat"})
CREATE (pf7:PoliticalFamily {name: "Ampatuan", province: "Maguindanao", member_count: 8, dynasty_score: 0.98, dynasty_type: "fat"})
CREATE (pf8:PoliticalFamily {name: "Dy", province: "Isabela", member_count: 5, dynasty_score: 0.90, dynasty_type: "fat"})

// --- Politicians ---
CREATE (pol1:Politician {name: "Ramon Revilla III", position: "Governor", term: "2022-2025", party: "Lakas-CMD", province: "Cavite", saln_net_worth: 245000000, dynasty_flag: true})
CREATE (pol2:Politician {name: "Lani Mercado-Revilla", position: "Representative", term: "2022-2025", party: "Lakas-CMD", province: "Cavite", saln_net_worth: 180000000, dynasty_flag: true})
CREATE (pol3:Politician {name: "Jinggoy Estrada", position: "Senator", term: "2022-2028", party: "PMP", province: "Manila", saln_net_worth: 120000000, dynasty_flag: true})
CREATE (pol4:Politician {name: "Mark Villar", position: "Senator", term: "2022-2028", party: "NP", province: "Las Pinas", saln_net_worth: 3200000000, dynasty_flag: true})
CREATE (pol5:Politician {name: "Imee Marcos", position: "Senator", term: "2022-2028", party: "NP", province: "Ilocos Norte", saln_net_worth: 62000000, dynasty_flag: true})
CREATE (pol6:Politician {name: "Sandro Marcos", position: "Representative", term: "2022-2025", party: "NP", province: "Ilocos Norte", saln_net_worth: 15000000, dynasty_flag: true})
CREATE (pol7:Politician {name: "Sara Duterte", position: "Vice President", term: "2022-2028", party: "Lakas-CMD", province: "Davao", saln_net_worth: 35000000, dynasty_flag: true})
CREATE (pol8:Politician {name: "Sebastian Duterte", position: "Representative", term: "2022-2025", party: "HNP", province: "Davao", saln_net_worth: 22000000, dynasty_flag: true})
CREATE (pol9:Politician {name: "Abby Binay", position: "Mayor", term: "2022-2025", party: "UNA", province: "Makati", saln_net_worth: 90000000, dynasty_flag: true})
CREATE (pol10:Politician {name: "Faustino Dy III", position: "Governor", term: "2022-2025", party: "PDP-Laban", province: "Isabela", saln_net_worth: 150000000, dynasty_flag: true})
CREATE (pol11:Politician {name: "Antonio Floirendo Jr", position: "Representative", term: "2022-2025", party: "NPC", province: "Davao del Norte", saln_net_worth: 2800000000, dynasty_flag: false})
CREATE (pol12:Politician {name: "Isidro Ungab", position: "Representative", term: "2022-2025", party: "PDP-Laban", province: "Davao", saln_net_worth: 45000000, dynasty_flag: false})

// --- Family relationships ---
CREATE (pol1)-[:MEMBER_OF {relationship_type: "head"}]->(pf1)
CREATE (pol2)-[:MEMBER_OF {relationship_type: "spouse"}]->(pf1)
CREATE (pol3)-[:MEMBER_OF {relationship_type: "child"}]->(pf2)
CREATE (pol4)-[:MEMBER_OF {relationship_type: "child"}]->(pf3)
CREATE (pol5)-[:MEMBER_OF {relationship_type: "child"}]->(pf4)
CREATE (pol6)-[:MEMBER_OF {relationship_type: "grandchild"}]->(pf4)
CREATE (pol7)-[:MEMBER_OF {relationship_type: "child"}]->(pf5)
CREATE (pol8)-[:MEMBER_OF {relationship_type: "child"}]->(pf5)
CREATE (pol9)-[:MEMBER_OF {relationship_type: "child"}]->(pf6)
CREATE (pol10)-[:MEMBER_OF {relationship_type: "head"}]->(pf8)

// --- Municipalities ---
CREATE (mun1:Municipality {name: "Trece Martires", province: "Cavite", region: "CALABARZON", population: 141890, income_class: "1st", psgc_code: "042114000"})
CREATE (mun2:Municipality {name: "Imus", province: "Cavite", region: "CALABARZON", population: 496794, income_class: "1st", psgc_code: "042108000"})
CREATE (mun3:Municipality {name: "San Juan", province: "Metro Manila", region: "NCR", population: 126347, income_class: "1st", psgc_code: "137503000"})
CREATE (mun4:Municipality {name: "Las Pinas", province: "Metro Manila", region: "NCR", population: 606293, income_class: "1st", psgc_code: "137601000"})
CREATE (mun5:Municipality {name: "Laoag", province: "Ilocos Norte", region: "Ilocos", population: 111651, income_class: "1st", psgc_code: "012801000"})
CREATE (mun6:Municipality {name: "Batac", province: "Ilocos Norte", region: "Ilocos", population: 55201, income_class: "3rd", psgc_code: "012802000"})
CREATE (mun7:Municipality {name: "Davao City", province: "Davao del Sur", region: "Davao", population: 1776949, income_class: "1st", psgc_code: "112402000"})
CREATE (mun8:Municipality {name: "Makati", province: "Metro Manila", region: "NCR", population: 629616, income_class: "1st", psgc_code: "137602000"})
CREATE (mun9:Municipality {name: "Ilagan", province: "Isabela", region: "Cagayan Valley", population: 155960, income_class: "1st", psgc_code: "023101000"})
CREATE (mun10:Municipality {name: "Quezon City", province: "Metro Manila", region: "NCR", population: 2960048, income_class: "1st", psgc_code: "137404000"})

// --- Politicians govern municipalities ---
CREATE (pol1)-[:GOVERNS {term_start: "2022-06-30", term_end: "2025-06-30", position: "Governor"}]->(mun1)
CREATE (pol2)-[:GOVERNS {term_start: "2022-06-30", term_end: "2025-06-30", position: "Representative"}]->(mun2)
CREATE (pol3)-[:GOVERNS {term_start: "2022-06-30", term_end: "2028-06-30", position: "Senator"}]->(mun3)
CREATE (pol4)-[:GOVERNS {term_start: "2022-06-30", term_end: "2028-06-30", position: "Senator"}]->(mun4)
CREATE (pol5)-[:GOVERNS {term_start: "2022-06-30", term_end: "2028-06-30", position: "Senator"}]->(mun5)
CREATE (pol6)-[:GOVERNS {term_start: "2022-06-30", term_end: "2025-06-30", position: "Representative"}]->(mun6)
CREATE (pol7)-[:GOVERNS {term_start: "2022-06-30", term_end: "2028-06-30", position: "Vice President"}]->(mun7)
CREATE (pol9)-[:GOVERNS {term_start: "2022-06-30", term_end: "2025-06-30", position: "Mayor"}]->(mun8)
CREATE (pol10)-[:GOVERNS {term_start: "2022-06-30", term_end: "2025-06-30", position: "Governor"}]->(mun9)

// --- Agencies ---
CREATE (ag1:Agency {name: "DPWH Region III", type: "national", department: "Department of Public Works and Highways", annual_budget: 89000000000})
CREATE (ag2:Agency {name: "DPWH Region IV-A", type: "national", department: "Department of Public Works and Highways", annual_budget: 72000000000})
CREATE (ag3:Agency {name: "DepEd Division of Cavite", type: "national", department: "Department of Education", annual_budget: 15000000000})
CREATE (ag4:Agency {name: "DOH Region III", type: "national", department: "Department of Health", annual_budget: 12000000000})
CREATE (ag5:Agency {name: "DILG Region IV-A", type: "national", department: "Department of the Interior and Local Government", annual_budget: 8500000000})
CREATE (ag6:Agency {name: "DA Region IV-A", type: "national", department: "Department of Agriculture", annual_budget: 6200000000})
CREATE (ag7:Agency {name: "DSWD NCR", type: "national", department: "Department of Social Welfare and Development", annual_budget: 18000000000})
CREATE (ag8:Agency {name: "DENR Region II", type: "national", department: "Department of Environment and Natural Resources", annual_budget: 4500000000})
CREATE (ag9:Agency {name: "DOTr Central Office", type: "national", department: "Department of Transportation", annual_budget: 95000000000})
CREATE (ag10:Agency {name: "LGU Makati", type: "LGU", department: "Local Government", annual_budget: 15800000000})
CREATE (ag11:Agency {name: "LGU Davao City", type: "LGU", department: "Local Government", annual_budget: 12500000000})
CREATE (ag12:Agency {name: "LGU Cavite Province", type: "LGU", department: "Local Government", annual_budget: 8900000000})
CREATE (ag13:Agency {name: "DPWH Region II", type: "national", department: "Department of Public Works and Highways", annual_budget: 45000000000})
CREATE (ag14:Agency {name: "DepEd Division of Davao", type: "national", department: "Department of Education", annual_budget: 11000000000})
CREATE (ag15:Agency {name: "PhilHealth Region IV-A", type: "GOCC", department: "Philippine Health Insurance Corporation", annual_budget: 25000000000})

// --- Municipality-Agency links ---
CREATE (mun1)-[:HAS_AGENCY]->(ag12)
CREATE (mun2)-[:HAS_AGENCY]->(ag12)
CREATE (mun7)-[:HAS_AGENCY]->(ag11)
CREATE (mun8)-[:HAS_AGENCY]->(ag10)
CREATE (mun9)-[:HAS_AGENCY]->(ag13)
CREATE (mun10)-[:HAS_AGENCY]->(ag1)

// --- Contractors ---
CREATE (con1:Contractor {name: "JMV Construction and Development Corp.", registration_number: "PG-2018-0045231", address: "Imus, Cavite", classification: "AAA", total_contracts: 87, total_value: 2340000000})
CREATE (con2:Contractor {name: "Brightstone Builders Inc.", registration_number: "PG-2017-0032187", address: "Trece Martires, Cavite", classification: "AA", total_contracts: 45, total_value: 890000000})
CREATE (con3:Contractor {name: "Pacific Roadworks Corp.", registration_number: "PG-2019-0067421", address: "San Fernando, Pampanga", classification: "AAA", total_contracts: 123, total_value: 5670000000})
CREATE (con4:Contractor {name: "Metro Alliance Construction Inc.", registration_number: "PG-2016-0021543", address: "Quezon City, Metro Manila", classification: "AAA", total_contracts: 156, total_value: 8900000000})
CREATE (con5:Contractor {name: "Golden Dragon Enterprises", registration_number: "PG-2020-0089102", address: "Makati, Metro Manila", classification: "A", total_contracts: 34, total_value: 450000000})
CREATE (con6:Contractor {name: "RCS Trading and Supply", registration_number: "PG-2019-0071234", address: "Trece Martires, Cavite", classification: "B", total_contracts: 28, total_value: 120000000})
CREATE (con7:Contractor {name: "Tristar Equipment Rentals Inc.", registration_number: "PG-2018-0051678", address: "Caloocan, Metro Manila", classification: "AA", total_contracts: 62, total_value: 1230000000})
CREATE (con8:Contractor {name: "Sta. Clara International Corp.", registration_number: "PG-2015-0012456", address: "Pasig, Metro Manila", classification: "AAA", total_contracts: 210, total_value: 15600000000})
CREATE (con9:Contractor {name: "F.F. Cruz and Co. Inc.", registration_number: "PG-2014-0009876", address: "Mandaluyong, Metro Manila", classification: "AAA", total_contracts: 189, total_value: 12300000000})
CREATE (con10:Contractor {name: "Superlines Transportation Co.", registration_number: "PG-2020-0094521", address: "Davao City, Davao del Sur", classification: "AA", total_contracts: 38, total_value: 670000000})
CREATE (con11:Contractor {name: "PhilBridge Construction Corp.", registration_number: "PG-2019-0078345", address: "Taguig, Metro Manila", classification: "AAA", total_contracts: 95, total_value: 4200000000})
CREATE (con12:Contractor {name: "Nueva Ecija Builders Inc.", registration_number: "PG-2021-0102345", address: "Cabanatuan, Nueva Ecija", classification: "A", total_contracts: 22, total_value: 280000000})
CREATE (con13:Contractor {name: "LNS International Construction Corp.", registration_number: "PG-2016-0025678", address: "San Jose del Monte, Bulacan", classification: "AAA", total_contracts: 134, total_value: 7800000000})
CREATE (con14:Contractor {name: "Cavite Prime Medical Supplies", registration_number: "PG-2020-0091234", address: "Dasmarinas, Cavite", classification: "B", total_contracts: 41, total_value: 95000000})
CREATE (con15:Contractor {name: "Isabela Valley Trading Corp.", registration_number: "PG-2018-0055678", address: "Ilagan, Isabela", classification: "A", total_contracts: 56, total_value: 340000000})
CREATE (con16:Contractor {name: "Mindanao Heavy Equipment Corp.", registration_number: "PG-2017-0038912", address: "Davao City, Davao del Sur", classification: "AA", total_contracts: 71, total_value: 1890000000})
CREATE (con17:Contractor {name: "Northwind IT Solutions Inc.", registration_number: "PG-2021-0115678", address: "Makati, Metro Manila", classification: "A", total_contracts: 19, total_value: 210000000})
CREATE (con18:Contractor {name: "Southeast General Merchandise", registration_number: "PG-2020-0098765", address: "Imus, Cavite", classification: "B", total_contracts: 33, total_value: 78000000})
CREATE (con19:Contractor {name: "Consolidated Builders and Developers Inc.", registration_number: "PG-2015-0014567", address: "Pasig, Metro Manila", classification: "AAA", total_contracts: 167, total_value: 9200000000})
CREATE (con20:Contractor {name: "Romago Inc.", registration_number: "PG-2016-0023456", address: "Mandaluyong, Metro Manila", classification: "AAA", total_contracts: 145, total_value: 6700000000})

// --- Contractor locations ---
CREATE (con1)-[:LOCATED_IN]->(mun2)
CREATE (con2)-[:LOCATED_IN]->(mun1)
CREATE (con5)-[:LOCATED_IN]->(mun8)
CREATE (con6)-[:LOCATED_IN]->(mun1)
CREATE (con10)-[:LOCATED_IN]->(mun7)
CREATE (con14)-[:LOCATED_IN]->(mun2)
CREATE (con15)-[:LOCATED_IN]->(mun9)
CREATE (con16)-[:LOCATED_IN]->(mun7)
CREATE (con18)-[:LOCATED_IN]->(mun2)

// --- Persons (beneficial owners) ---
CREATE (per1:Person {name: "Jose Miguel Villanueva", role: "owner"})
CREATE (per2:Person {name: "Maria Luisa Revilla-Santos", role: "owner"})
CREATE (per3:Person {name: "Ricardo Cruz-Salazar", role: "officer"})
CREATE (per4:Person {name: "Antonio Dy-Reyes", role: "owner"})
CREATE (per5:Person {name: "Rodrigo Binay-Mercado", role: "officer"})
CREATE (per6:Person {name: "Eduardo Florendo", role: "owner"})

// --- Ownership and family links (red flag: political connections) ---
CREATE (con1)-[:OWNED_BY {share_percentage: 60}]->(per1)
CREATE (con2)-[:OWNED_BY {share_percentage: 45}]->(per2)
CREATE (con6)-[:OWNED_BY {share_percentage: 80}]->(per3)
CREATE (con15)-[:OWNED_BY {share_percentage: 55}]->(per4)
CREATE (con5)-[:OWNED_BY {share_percentage: 35}]->(per5)
CREATE (con10)-[:OWNED_BY {share_percentage: 70}]->(per6)
CREATE (per2)-[:FAMILY_OF {relationship: "cousin"}]->(pol1)
CREATE (per4)-[:FAMILY_OF {relationship: "nephew"}]->(pol10)
CREATE (per5)-[:FAMILY_OF {relationship: "in-law"}]->(pol9)
CREATE (per6)-[:FAMILY_OF {relationship: "business_associate"}]->(pol11)

// --- Contracts (DPWH Region III — high volume) ---
CREATE (c1:Contract {reference_number: "DPWH-R3-2023-001", title: "Construction of Flood Control Structure along Pampanga River, Phase III", amount: 345000000, procurement_method: "public_bidding", award_date: date("2023-03-15"), notice_date: date("2023-01-10"), status: "completed", bid_count: 5, category: "infrastructure"})
CREATE (c2:Contract {reference_number: "DPWH-R3-2023-002", title: "Road Widening - MacArthur Highway (Km 45-52)", amount: 189000000, procurement_method: "public_bidding", award_date: date("2023-04-22"), notice_date: date("2023-02-15"), status: "completed", bid_count: 4, category: "infrastructure"})
CREATE (c3:Contract {reference_number: "DPWH-R3-2023-003", title: "Rehabilitation of National Road - Olongapo-Bugallon", amount: 78500000, procurement_method: "public_bidding", award_date: date("2023-05-10"), notice_date: date("2023-03-01"), status: "ongoing", bid_count: 3, category: "infrastructure"})
CREATE (c4:Contract {reference_number: "DPWH-R3-2023-004", title: "Bridge Construction - Calumpit Bypass Road", amount: 456000000, procurement_method: "public_bidding", award_date: date("2023-06-18"), notice_date: date("2023-04-01"), status: "ongoing", bid_count: 6, category: "infrastructure"})
CREATE (c5:Contract {reference_number: "DPWH-R3-2023-005", title: "Drainage Improvement - Meycauayan Industrial Zone", amount: 23400000, procurement_method: "shopping", award_date: date("2023-07-05"), notice_date: date("2023-06-20"), status: "completed", bid_count: 1, category: "infrastructure"})
CREATE (c6:Contract {reference_number: "DPWH-R3-2023-006", title: "Supply of Construction Materials for Emergency Repairs", amount: 4900000, procurement_method: "direct_contracting", award_date: date("2023-07-12"), notice_date: date("2023-07-10"), status: "completed", bid_count: 1, category: "goods"})
CREATE (c7:Contract {reference_number: "DPWH-R3-2023-007", title: "Road Concreting - Baler-Casiguran Road Section", amount: 267000000, procurement_method: "public_bidding", award_date: date("2023-08-20"), notice_date: date("2023-06-15"), status: "ongoing", bid_count: 4, category: "infrastructure"})
CREATE (c8:Contract {reference_number: "DPWH-R3-2024-001", title: "Slope Protection - Pantabangan-Cabanatuan Road", amount: 156000000, procurement_method: "public_bidding", award_date: date("2024-01-15"), notice_date: date("2023-11-01"), status: "ongoing", bid_count: 3, category: "infrastructure"})
CREATE (c9:Contract {reference_number: "DPWH-R3-2024-002", title: "Multi-Purpose Building Construction - Tarlac", amount: 45000000, procurement_method: "public_bidding", award_date: date("2024-02-20"), notice_date: date("2023-12-15"), status: "ongoing", bid_count: 2, category: "infrastructure"})
CREATE (c10:Contract {reference_number: "DPWH-R3-2024-003", title: "Office Equipment and IT Infrastructure Upgrade", amount: 4800000, procurement_method: "shopping", award_date: date("2024-03-01"), notice_date: date("2024-02-15"), status: "completed", bid_count: 1, category: "goods"})

// --- Contracts (DPWH Region IV-A) ---
CREATE (c11:Contract {reference_number: "DPWH-R4A-2023-001", title: "Rehabilitation of Emilio Aguinaldo Highway, Cavite Section", amount: 523000000, procurement_method: "public_bidding", award_date: date("2023-02-28"), notice_date: date("2023-01-05"), status: "completed", bid_count: 7, category: "infrastructure"})
CREATE (c12:Contract {reference_number: "DPWH-R4A-2023-002", title: "Construction of Bypass Road - Silang-Tagaytay", amount: 312000000, procurement_method: "public_bidding", award_date: date("2023-04-10"), notice_date: date("2023-02-01"), status: "ongoing", bid_count: 5, category: "infrastructure"})
CREATE (c13:Contract {reference_number: "DPWH-R4A-2023-003", title: "Flood Mitigation Structures - Imus River Basin", amount: 198000000, procurement_method: "public_bidding", award_date: date("2023-05-25"), notice_date: date("2023-03-15"), status: "completed", bid_count: 4, category: "infrastructure"})
CREATE (c14:Contract {reference_number: "DPWH-R4A-2023-004", title: "Road Paving - Barangay Access Roads, Cavite Province", amount: 67000000, procurement_method: "public_bidding", award_date: date("2023-06-30"), notice_date: date("2023-05-01"), status: "completed", bid_count: 3, category: "infrastructure"})
CREATE (c15:Contract {reference_number: "DPWH-R4A-2024-001", title: "Seawall Construction - Nasugbu Coastal Area", amount: 234000000, procurement_method: "public_bidding", award_date: date("2024-01-20"), notice_date: date("2023-11-10"), status: "ongoing", bid_count: 4, category: "infrastructure"})
CREATE (c16:Contract {reference_number: "DPWH-R4A-2024-002", title: "Emergency Road Clearing - Typhoon Damage", amount: 4500000, procurement_method: "negotiated", award_date: date("2024-02-05"), notice_date: date("2024-02-03"), status: "completed", bid_count: 1, category: "infrastructure"})

// --- Contracts (DepEd Cavite) ---
CREATE (c17:Contract {reference_number: "DEPED-CAV-2023-001", title: "Construction of 5-Classroom Building - Imus North Central School", amount: 15800000, procurement_method: "public_bidding", award_date: date("2023-03-20"), notice_date: date("2023-01-15"), status: "completed", bid_count: 4, category: "infrastructure"})
CREATE (c18:Contract {reference_number: "DEPED-CAV-2023-002", title: "Supply of School Desks and Chairs (5,000 units)", amount: 12500000, procurement_method: "public_bidding", award_date: date("2023-05-15"), notice_date: date("2023-03-01"), status: "completed", bid_count: 3, category: "goods"})
CREATE (c19:Contract {reference_number: "DEPED-CAV-2023-003", title: "Repair and Rehabilitation of School Buildings Post-Typhoon", amount: 4800000, procurement_method: "negotiated", award_date: date("2023-08-10"), notice_date: date("2023-08-08"), status: "completed", bid_count: 1, category: "infrastructure"})
CREATE (c20:Contract {reference_number: "DEPED-CAV-2024-001", title: "School ICT Equipment Package (Laptops and Projectors)", amount: 8900000, procurement_method: "public_bidding", award_date: date("2024-01-30"), notice_date: date("2023-12-01"), status: "ongoing", bid_count: 2, category: "goods"})

// --- Contracts (DOH Region III) ---
CREATE (c21:Contract {reference_number: "DOH-R3-2023-001", title: "Supply of Essential Medicines for Rural Health Units", amount: 34500000, procurement_method: "public_bidding", award_date: date("2023-02-15"), notice_date: date("2023-01-02"), status: "completed", bid_count: 5, category: "goods"})
CREATE (c22:Contract {reference_number: "DOH-R3-2023-002", title: "Medical Equipment for District Hospitals", amount: 89000000, procurement_method: "public_bidding", award_date: date("2023-04-28"), notice_date: date("2023-02-20"), status: "completed", bid_count: 4, category: "goods"})
CREATE (c23:Contract {reference_number: "DOH-R3-2023-003", title: "Construction of Barangay Health Stations (10 units)", amount: 42000000, procurement_method: "public_bidding", award_date: date("2023-06-15"), notice_date: date("2023-04-01"), status: "ongoing", bid_count: 3, category: "infrastructure"})
CREATE (c24:Contract {reference_number: "DOH-R3-2024-001", title: "PPE and Medical Supplies Stockpile", amount: 4200000, procurement_method: "shopping", award_date: date("2024-01-10"), notice_date: date("2024-01-05"), status: "completed", bid_count: 1, category: "goods"})

// --- Contracts (LGU Makati — red flag: concentration) ---
CREATE (c25:Contract {reference_number: "MAK-2023-001", title: "Road Resurfacing - Ayala Avenue Extension", amount: 67000000, procurement_method: "public_bidding", award_date: date("2023-03-01"), notice_date: date("2023-01-15"), status: "completed", bid_count: 4, category: "infrastructure"})
CREATE (c26:Contract {reference_number: "MAK-2023-002", title: "Drainage System Improvement - Barangay Poblacion", amount: 34000000, procurement_method: "public_bidding", award_date: date("2023-04-15"), notice_date: date("2023-02-20"), status: "completed", bid_count: 3, category: "infrastructure"})
CREATE (c27:Contract {reference_number: "MAK-2023-003", title: "Public Market Renovation Phase I", amount: 45000000, procurement_method: "public_bidding", award_date: date("2023-06-01"), notice_date: date("2023-04-01"), status: "ongoing", bid_count: 2, category: "infrastructure"})
CREATE (c28:Contract {reference_number: "MAK-2023-004", title: "IT System Upgrade - City Hall", amount: 18000000, procurement_method: "public_bidding", award_date: date("2023-07-20"), notice_date: date("2023-05-15"), status: "completed", bid_count: 3, category: "goods"})
CREATE (c29:Contract {reference_number: "MAK-2024-001", title: "Social Housing Construction - Barangay Guadalupe", amount: 156000000, procurement_method: "public_bidding", award_date: date("2024-02-10"), notice_date: date("2023-12-01"), status: "ongoing", bid_count: 5, category: "infrastructure"})
CREATE (c30:Contract {reference_number: "MAK-2024-002", title: "Streetlight LED Conversion Program", amount: 23000000, procurement_method: "public_bidding", award_date: date("2024-03-05"), notice_date: date("2024-01-15"), status: "ongoing", bid_count: 2, category: "goods"})

// --- Contracts (LGU Davao City) ---
CREATE (c31:Contract {reference_number: "DVO-2023-001", title: "Construction of Coastal Road Extension", amount: 234000000, procurement_method: "public_bidding", award_date: date("2023-03-10"), notice_date: date("2023-01-05"), status: "completed", bid_count: 5, category: "infrastructure"})
CREATE (c32:Contract {reference_number: "DVO-2023-002", title: "Supply of Heavy Equipment for Public Works", amount: 89000000, procurement_method: "public_bidding", award_date: date("2023-05-20"), notice_date: date("2023-03-10"), status: "completed", bid_count: 3, category: "goods"})
CREATE (c33:Contract {reference_number: "DVO-2023-003", title: "Flood Control and Drainage - Matina Area", amount: 167000000, procurement_method: "public_bidding", award_date: date("2023-07-15"), notice_date: date("2023-05-01"), status: "ongoing", bid_count: 4, category: "infrastructure"})
CREATE (c34:Contract {reference_number: "DVO-2024-001", title: "Public School Building Repair Program", amount: 56000000, procurement_method: "public_bidding", award_date: date("2024-01-25"), notice_date: date("2023-11-15"), status: "ongoing", bid_count: 3, category: "infrastructure"})

// --- Contracts (DPWH Region II — Isabela) ---
CREATE (c35:Contract {reference_number: "DPWH-R2-2023-001", title: "Bridge Widening - Magat River Crossing", amount: 389000000, procurement_method: "public_bidding", award_date: date("2023-02-20"), notice_date: date("2023-01-02"), status: "completed", bid_count: 4, category: "infrastructure"})
CREATE (c36:Contract {reference_number: "DPWH-R2-2023-002", title: "Road Rehabilitation - Maharlika Highway Isabela Section", amount: 234000000, procurement_method: "public_bidding", award_date: date("2023-05-10"), notice_date: date("2023-03-01"), status: "ongoing", bid_count: 3, category: "infrastructure"})
CREATE (c37:Contract {reference_number: "DPWH-R2-2023-003", title: "Farm-to-Market Road Construction - Tumauini", amount: 45000000, procurement_method: "public_bidding", award_date: date("2023-07-01"), notice_date: date("2023-05-15"), status: "completed", bid_count: 2, category: "infrastructure"})
CREATE (c38:Contract {reference_number: "DPWH-R2-2024-001", title: "Multi-Purpose Evacuation Center - Santiago City", amount: 67000000, procurement_method: "public_bidding", award_date: date("2024-01-15"), notice_date: date("2023-11-01"), status: "ongoing", bid_count: 3, category: "infrastructure"})

// --- Contracts (DSWD NCR) ---
CREATE (c39:Contract {reference_number: "DSWD-NCR-2023-001", title: "Relief Goods Procurement - Typhoon Response", amount: 78000000, procurement_method: "negotiated", award_date: date("2023-08-05"), notice_date: date("2023-08-03"), status: "completed", bid_count: 1, category: "goods"})
CREATE (c40:Contract {reference_number: "DSWD-NCR-2023-002", title: "Feeding Program Supplies (6-month supply)", amount: 45000000, procurement_method: "public_bidding", award_date: date("2023-04-20"), notice_date: date("2023-02-15"), status: "completed", bid_count: 4, category: "goods"})

// --- Contracts (DOTr) ---
CREATE (c41:Contract {reference_number: "DOTR-CO-2023-001", title: "MRT Line 3 Rehabilitation - Signal System Upgrade", amount: 890000000, procurement_method: "public_bidding", award_date: date("2023-03-25"), notice_date: date("2022-11-01"), status: "ongoing", bid_count: 3, category: "infrastructure"})
CREATE (c42:Contract {reference_number: "DOTR-CO-2023-002", title: "Bus Rapid Transit Study - EDSA Corridor", amount: 45000000, procurement_method: "public_bidding", award_date: date("2023-06-10"), notice_date: date("2023-04-01"), status: "completed", bid_count: 5, category: "consulting"})

// --- Contracts (split contracts — red flag pattern, amounts just below P50M threshold) ---
CREATE (c43:Contract {reference_number: "DPWH-R3-2023-008", title: "Road Repair Section A - Bulacan Provincial Road", amount: 4950000, procurement_method: "shopping", award_date: date("2023-09-01"), notice_date: date("2023-08-25"), status: "completed", bid_count: 1, category: "infrastructure"})
CREATE (c44:Contract {reference_number: "DPWH-R3-2023-009", title: "Road Repair Section B - Bulacan Provincial Road", amount: 4890000, procurement_method: "shopping", award_date: date("2023-09-02"), notice_date: date("2023-08-25"), status: "completed", bid_count: 1, category: "infrastructure"})
CREATE (c45:Contract {reference_number: "DPWH-R3-2023-010", title: "Road Repair Section C - Bulacan Provincial Road", amount: 4920000, procurement_method: "shopping", award_date: date("2023-09-03"), notice_date: date("2023-08-25"), status: "completed", bid_count: 1, category: "infrastructure"})

// --- Contracts (identical bid amounts — red flag) ---
CREATE (c46:Contract {reference_number: "DA-R4A-2023-001", title: "Supply of Rice Seeds - Wet Season 2023", amount: 12450000, procurement_method: "public_bidding", award_date: date("2023-05-01"), notice_date: date("2023-03-15"), status: "completed", bid_count: 3, category: "goods"})
CREATE (c47:Contract {reference_number: "DA-R4A-2023-002", title: "Supply of Fertilizer - National Rice Program", amount: 23400000, procurement_method: "public_bidding", award_date: date("2023-06-15"), notice_date: date("2023-04-20"), status: "completed", bid_count: 3, category: "goods"})

// --- Contracts (PhilHealth — questionable) ---
CREATE (c48:Contract {reference_number: "PH-R4A-2023-001", title: "Pharmacy Benefit Management IT System", amount: 67000000, procurement_method: "negotiated", award_date: date("2023-04-10"), notice_date: date("2023-04-05"), status: "completed", bid_count: 1, category: "consulting"})

// --- Contracts (DENR Region II) ---
CREATE (c49:Contract {reference_number: "DENR-R2-2023-001", title: "Reforestation Program - Sierra Madre", amount: 34000000, procurement_method: "public_bidding", award_date: date("2023-03-15"), notice_date: date("2023-01-20"), status: "completed", bid_count: 3, category: "infrastructure"})
CREATE (c50:Contract {reference_number: "DENR-R2-2024-001", title: "River Basin Management Study", amount: 12000000, procurement_method: "public_bidding", award_date: date("2024-02-01"), notice_date: date("2023-12-01"), status: "ongoing", bid_count: 2, category: "consulting"})

// --- Agency procured contracts ---
CREATE (ag1)-[:PROCURED {fiscal_year: 2023}]->(c1)
CREATE (ag1)-[:PROCURED {fiscal_year: 2023}]->(c2)
CREATE (ag1)-[:PROCURED {fiscal_year: 2023}]->(c3)
CREATE (ag1)-[:PROCURED {fiscal_year: 2023}]->(c4)
CREATE (ag1)-[:PROCURED {fiscal_year: 2023}]->(c5)
CREATE (ag1)-[:PROCURED {fiscal_year: 2023}]->(c6)
CREATE (ag1)-[:PROCURED {fiscal_year: 2023}]->(c7)
CREATE (ag1)-[:PROCURED {fiscal_year: 2024}]->(c8)
CREATE (ag1)-[:PROCURED {fiscal_year: 2024}]->(c9)
CREATE (ag1)-[:PROCURED {fiscal_year: 2024}]->(c10)
CREATE (ag1)-[:PROCURED {fiscal_year: 2023}]->(c43)
CREATE (ag1)-[:PROCURED {fiscal_year: 2023}]->(c44)
CREATE (ag1)-[:PROCURED {fiscal_year: 2023}]->(c45)
CREATE (ag2)-[:PROCURED {fiscal_year: 2023}]->(c11)
CREATE (ag2)-[:PROCURED {fiscal_year: 2023}]->(c12)
CREATE (ag2)-[:PROCURED {fiscal_year: 2023}]->(c13)
CREATE (ag2)-[:PROCURED {fiscal_year: 2023}]->(c14)
CREATE (ag2)-[:PROCURED {fiscal_year: 2024}]->(c15)
CREATE (ag2)-[:PROCURED {fiscal_year: 2024}]->(c16)
CREATE (ag3)-[:PROCURED {fiscal_year: 2023}]->(c17)
CREATE (ag3)-[:PROCURED {fiscal_year: 2023}]->(c18)
CREATE (ag3)-[:PROCURED {fiscal_year: 2023}]->(c19)
CREATE (ag3)-[:PROCURED {fiscal_year: 2024}]->(c20)
CREATE (ag4)-[:PROCURED {fiscal_year: 2023}]->(c21)
CREATE (ag4)-[:PROCURED {fiscal_year: 2023}]->(c22)
CREATE (ag4)-[:PROCURED {fiscal_year: 2023}]->(c23)
CREATE (ag4)-[:PROCURED {fiscal_year: 2024}]->(c24)
CREATE (ag10)-[:PROCURED {fiscal_year: 2023}]->(c25)
CREATE (ag10)-[:PROCURED {fiscal_year: 2023}]->(c26)
CREATE (ag10)-[:PROCURED {fiscal_year: 2023}]->(c27)
CREATE (ag10)-[:PROCURED {fiscal_year: 2023}]->(c28)
CREATE (ag10)-[:PROCURED {fiscal_year: 2024}]->(c29)
CREATE (ag10)-[:PROCURED {fiscal_year: 2024}]->(c30)
CREATE (ag11)-[:PROCURED {fiscal_year: 2023}]->(c31)
CREATE (ag11)-[:PROCURED {fiscal_year: 2023}]->(c32)
CREATE (ag11)-[:PROCURED {fiscal_year: 2023}]->(c33)
CREATE (ag11)-[:PROCURED {fiscal_year: 2024}]->(c34)
CREATE (ag13)-[:PROCURED {fiscal_year: 2023}]->(c35)
CREATE (ag13)-[:PROCURED {fiscal_year: 2023}]->(c36)
CREATE (ag13)-[:PROCURED {fiscal_year: 2023}]->(c37)
CREATE (ag13)-[:PROCURED {fiscal_year: 2024}]->(c38)
CREATE (ag7)-[:PROCURED {fiscal_year: 2023}]->(c39)
CREATE (ag7)-[:PROCURED {fiscal_year: 2023}]->(c40)
CREATE (ag9)-[:PROCURED {fiscal_year: 2023}]->(c41)
CREATE (ag9)-[:PROCURED {fiscal_year: 2023}]->(c42)
CREATE (ag6)-[:PROCURED {fiscal_year: 2023}]->(c46)
CREATE (ag6)-[:PROCURED {fiscal_year: 2023}]->(c47)
CREATE (ag15)-[:PROCURED {fiscal_year: 2023}]->(c48)
CREATE (ag8)-[:PROCURED {fiscal_year: 2023}]->(c49)
CREATE (ag8)-[:PROCURED {fiscal_year: 2024}]->(c50)

// --- Contract awards (AWARDED_TO) ---
// DPWH Region III — Pacific Roadworks dominates (red flag: concentration)
CREATE (c1)-[:AWARDED_TO {award_date: date("2023-03-15"), bid_amount: 345000000}]->(con3)
CREATE (c2)-[:AWARDED_TO {award_date: date("2023-04-22"), bid_amount: 189000000}]->(con3)
CREATE (c3)-[:AWARDED_TO {award_date: date("2023-05-10"), bid_amount: 78500000}]->(con12)
CREATE (c4)-[:AWARDED_TO {award_date: date("2023-06-18"), bid_amount: 456000000}]->(con4)
CREATE (c5)-[:AWARDED_TO {award_date: date("2023-07-05"), bid_amount: 23400000}]->(con3)
CREATE (c6)-[:AWARDED_TO {award_date: date("2023-07-12"), bid_amount: 4900000}]->(con3)
CREATE (c7)-[:AWARDED_TO {award_date: date("2023-08-20"), bid_amount: 267000000}]->(con13)
CREATE (c8)-[:AWARDED_TO {award_date: date("2024-01-15"), bid_amount: 156000000}]->(con3)
CREATE (c9)-[:AWARDED_TO {award_date: date("2024-02-20"), bid_amount: 45000000}]->(con12)
CREATE (c10)-[:AWARDED_TO {award_date: date("2024-03-01"), bid_amount: 4800000}]->(con17)

// Split contracts — all to same contractor (red flag)
CREATE (c43)-[:AWARDED_TO {award_date: date("2023-09-01"), bid_amount: 4950000}]->(con3)
CREATE (c44)-[:AWARDED_TO {award_date: date("2023-09-02"), bid_amount: 4890000}]->(con3)
CREATE (c45)-[:AWARDED_TO {award_date: date("2023-09-03"), bid_amount: 4920000}]->(con3)

// DPWH Region IV-A
CREATE (c11)-[:AWARDED_TO {award_date: date("2023-02-28"), bid_amount: 523000000}]->(con1)
CREATE (c12)-[:AWARDED_TO {award_date: date("2023-04-10"), bid_amount: 312000000}]->(con1)
CREATE (c13)-[:AWARDED_TO {award_date: date("2023-05-25"), bid_amount: 198000000}]->(con2)
CREATE (c14)-[:AWARDED_TO {award_date: date("2023-06-30"), bid_amount: 67000000}]->(con2)
CREATE (c15)-[:AWARDED_TO {award_date: date("2024-01-20"), bid_amount: 234000000}]->(con8)
CREATE (c16)-[:AWARDED_TO {award_date: date("2024-02-05"), bid_amount: 4500000}]->(con1)

// DepEd Cavite
CREATE (c17)-[:AWARDED_TO {award_date: date("2023-03-20"), bid_amount: 15800000}]->(con2)
CREATE (c18)-[:AWARDED_TO {award_date: date("2023-05-15"), bid_amount: 12500000}]->(con18)
CREATE (c19)-[:AWARDED_TO {award_date: date("2023-08-10"), bid_amount: 4800000}]->(con6)
CREATE (c20)-[:AWARDED_TO {award_date: date("2024-01-30"), bid_amount: 8900000}]->(con17)

// DOH Region III
CREATE (c21)-[:AWARDED_TO {award_date: date("2023-02-15"), bid_amount: 34500000}]->(con14)
CREATE (c22)-[:AWARDED_TO {award_date: date("2023-04-28"), bid_amount: 89000000}]->(con7)
CREATE (c23)-[:AWARDED_TO {award_date: date("2023-06-15"), bid_amount: 42000000}]->(con12)
CREATE (c24)-[:AWARDED_TO {award_date: date("2024-01-10"), bid_amount: 4200000}]->(con14)

// LGU Makati — Golden Dragon gets disproportionate share (red flag: political connection + concentration)
CREATE (c25)-[:AWARDED_TO {award_date: date("2023-03-01"), bid_amount: 67000000}]->(con5)
CREATE (c26)-[:AWARDED_TO {award_date: date("2023-04-15"), bid_amount: 34000000}]->(con5)
CREATE (c27)-[:AWARDED_TO {award_date: date("2023-06-01"), bid_amount: 45000000}]->(con5)
CREATE (c28)-[:AWARDED_TO {award_date: date("2023-07-20"), bid_amount: 18000000}]->(con17)
CREATE (c29)-[:AWARDED_TO {award_date: date("2024-02-10"), bid_amount: 156000000}]->(con19)
CREATE (c30)-[:AWARDED_TO {award_date: date("2024-03-05"), bid_amount: 23000000}]->(con5)

// LGU Davao City
CREATE (c31)-[:AWARDED_TO {award_date: date("2023-03-10"), bid_amount: 234000000}]->(con16)
CREATE (c32)-[:AWARDED_TO {award_date: date("2023-05-20"), bid_amount: 89000000}]->(con10)
CREATE (c33)-[:AWARDED_TO {award_date: date("2023-07-15"), bid_amount: 167000000}]->(con16)
CREATE (c34)-[:AWARDED_TO {award_date: date("2024-01-25"), bid_amount: 56000000}]->(con10)

// DPWH Region II
CREATE (c35)-[:AWARDED_TO {award_date: date("2023-02-20"), bid_amount: 389000000}]->(con9)
CREATE (c36)-[:AWARDED_TO {award_date: date("2023-05-10"), bid_amount: 234000000}]->(con15)
CREATE (c37)-[:AWARDED_TO {award_date: date("2023-07-01"), bid_amount: 45000000}]->(con15)
CREATE (c38)-[:AWARDED_TO {award_date: date("2024-01-15"), bid_amount: 67000000}]->(con9)

// DSWD NCR
CREATE (c39)-[:AWARDED_TO {award_date: date("2023-08-05"), bid_amount: 78000000}]->(con7)
CREATE (c40)-[:AWARDED_TO {award_date: date("2023-04-20"), bid_amount: 45000000}]->(con18)

// DOTr
CREATE (c41)-[:AWARDED_TO {award_date: date("2023-03-25"), bid_amount: 890000000}]->(con8)
CREATE (c42)-[:AWARDED_TO {award_date: date("2023-06-10"), bid_amount: 45000000}]->(con11)

// DA Region IV-A
CREATE (c46)-[:AWARDED_TO {award_date: date("2023-05-01"), bid_amount: 12450000}]->(con18)
CREATE (c47)-[:AWARDED_TO {award_date: date("2023-06-15"), bid_amount: 23400000}]->(con6)

// PhilHealth
CREATE (c48)-[:AWARDED_TO {award_date: date("2023-04-10"), bid_amount: 67000000}]->(con17)

// DENR Region II
CREATE (c49)-[:AWARDED_TO {award_date: date("2023-03-15"), bid_amount: 34000000}]->(con15)
CREATE (c50)-[:AWARDED_TO {award_date: date("2024-02-01"), bid_amount: 12000000}]->(con15)

// --- BID_ON relationships (losing bids for co-bidding analysis) ---
CREATE (con4)-[:BID_ON {bid_amount: 358000000, status: "lost"}]->(c1)
CREATE (con13)-[:BID_ON {bid_amount: 362000000, status: "lost"}]->(c1)
CREATE (con9)-[:BID_ON {bid_amount: 370000000, status: "lost"}]->(c1)
CREATE (con19)-[:BID_ON {bid_amount: 349000000, status: "lost"}]->(c1)
CREATE (con4)-[:BID_ON {bid_amount: 195000000, status: "lost"}]->(c2)
CREATE (con13)-[:BID_ON {bid_amount: 198000000, status: "lost"}]->(c2)
CREATE (con20)-[:BID_ON {bid_amount: 192000000, status: "lost"}]->(c2)
CREATE (con3)-[:BID_ON {bid_amount: 468000000, status: "lost"}]->(c4)
CREATE (con13)-[:BID_ON {bid_amount: 472000000, status: "lost"}]->(c4)
CREATE (con19)-[:BID_ON {bid_amount: 460000000, status: "lost"}]->(c4)
CREATE (con20)-[:BID_ON {bid_amount: 465000000, status: "lost"}]->(c4)
CREATE (con9)-[:BID_ON {bid_amount: 478000000, status: "lost"}]->(c4)

// Co-bidding ring pattern (con3, con12, con13 frequently bid together)
CREATE (con12)-[:BID_ON {bid_amount: 82000000, status: "lost"}]->(c3)
CREATE (con13)-[:BID_ON {bid_amount: 80000000, status: "lost"}]->(c3)
CREATE (con3)-[:BID_ON {bid_amount: 275000000, status: "lost"}]->(c7)
CREATE (con12)-[:BID_ON {bid_amount: 280000000, status: "lost"}]->(c7)
CREATE (con12)-[:BID_ON {bid_amount: 160000000, status: "lost"}]->(c8)
CREATE (con13)-[:BID_ON {bid_amount: 165000000, status: "lost"}]->(c8)

// Identical bid amounts — red flag for DA contracts
CREATE (con6)-[:BID_ON {bid_amount: 12448000, status: "lost"}]->(c46)
CREATE (con18)-[:BID_ON {bid_amount: 12452000, status: "lost"}]->(c46)
CREATE (con6)-[:BID_ON {bid_amount: 23398000, status: "lost"}]->(c47)
CREATE (con18)-[:BID_ON {bid_amount: 23402000, status: "lost"}]->(c47)

// --- CO_BID_WITH edges (derived from co-bidding patterns) ---
CREATE (con3)-[:CO_BID_WITH {contract_count: 8, win_pattern: "rotating"}]->(con12)
CREATE (con3)-[:CO_BID_WITH {contract_count: 7, win_pattern: "rotating"}]->(con13)
CREATE (con12)-[:CO_BID_WITH {contract_count: 6, win_pattern: "rotating"}]->(con13)
CREATE (con4)-[:CO_BID_WITH {contract_count: 5, win_pattern: "competitive"}]->(con19)
CREATE (con4)-[:CO_BID_WITH {contract_count: 4, win_pattern: "competitive"}]->(con9)
CREATE (con6)-[:CO_BID_WITH {contract_count: 4, win_pattern: "identical_amounts"}]->(con18)
CREATE (con1)-[:CO_BID_WITH {contract_count: 3, win_pattern: "competitive"}]->(con8)

// --- Audit Findings ---
CREATE (af1:AuditFinding {type: "procurement_irregularity", severity: "high", amount: 23400000, year: 2023, description: "Single-source procurement for emergency supplies without proper justification under RA 9184 Section 53", recommendation: "Conduct post-procurement review and ensure compliance", recommendation_status: "pending"})
CREATE (af2:AuditFinding {type: "contract_splitting", severity: "high", amount: 14760000, year: 2023, description: "Three road repair contracts with identical scope split to avoid public bidding threshold of P5M", recommendation: "Consolidate similar contracts and conduct proper competitive bidding", recommendation_status: "noted"})
CREATE (af3:AuditFinding {type: "overpricing", severity: "medium", amount: 8900000, year: 2023, description: "Medical equipment procured at prices 35% above market average based on COA price monitoring", recommendation: "Establish updated price reference for medical equipment", recommendation_status: "implemented"})
CREATE (af4:AuditFinding {type: "concentration_risk", severity: "high", amount: 169000000, year: 2023, description: "48.7% of total procurement value awarded to single contractor Golden Dragon Enterprises across 4 contracts", recommendation: "Implement contractor rotation policy", recommendation_status: "pending"})
CREATE (af5:AuditFinding {type: "bid_rigging_indicator", severity: "critical", amount: 35850000, year: 2023, description: "Three bidders submitted amounts within 0.03% of each other across 2 DA Region IV-A contracts, statistical probability < 0.001", recommendation: "Refer to Ombudsman for investigation", recommendation_status: "pending"})
CREATE (af6:AuditFinding {type: "delayed_completion", severity: "medium", amount: 523000000, year: 2023, description: "Emilio Aguinaldo Highway rehabilitation marked complete but site inspection found 30% of work items incomplete", recommendation: "Withhold final payment pending completion verification", recommendation_status: "implemented"})
CREATE (af7:AuditFinding {type: "unliquidated_advances", severity: "medium", amount: 45000000, year: 2023, description: "Cash advances for relief operations unliquidated beyond 90-day regulatory period", recommendation: "Require liquidation within regulatory period", recommendation_status: "pending"})

// --- Audit findings linked to agencies ---
CREATE (ag1)-[:AUDITED {year: 2023}]->(af2)
CREATE (ag4)-[:AUDITED {year: 2023}]->(af3)
CREATE (ag10)-[:AUDITED {year: 2023}]->(af4)
CREATE (ag6)-[:AUDITED {year: 2023}]->(af5)
CREATE (ag2)-[:AUDITED {year: 2023}]->(af6)
CREATE (ag7)-[:AUDITED {year: 2023}]->(af7)
CREATE (ag1)-[:AUDITED {year: 2023}]->(af1)

// --- Audit findings involving officials ---
CREATE (af4)-[:INVOLVES_OFFICIAL {role: "approving_authority"}]->(pol9)
CREATE (af2)-[:INVOLVES_OFFICIAL {role: "agency_head"}]->(pol1)

// --- Bills ---
CREATE (b1:Bill {number: "SB-1234", title: "Anti-Dynasty Act of 2023", status: "pending_committee", filed_date: date("2023-07-15"), committee: "Electoral Reforms", significance: "high"})
CREATE (b2:Bill {number: "SB-2345", title: "Procurement Reform and Transparency Act", status: "second_reading", filed_date: date("2023-03-10"), committee: "Finance", significance: "high"})
CREATE (b3:Bill {number: "SB-3456", title: "Open Government Data Act", status: "pending_committee", filed_date: date("2023-05-20"), committee: "Science and Technology", significance: "medium"})
CREATE (b4:Bill {number: "HB-7890", title: "Local Government Procurement Modernization Act", status: "first_reading", filed_date: date("2023-09-01"), committee: "Local Government", significance: "medium"})
CREATE (b5:Bill {number: "HB-8901", title: "Strengthening the Commission on Audit Act", status: "pending_committee", filed_date: date("2023-06-15"), committee: "Appropriations", significance: "high"})

// --- Bill authorship ---
CREATE (pol3)-[:AUTHORED {role: "principal"}]->(b1)
CREATE (pol4)-[:AUTHORED {role: "principal"}]->(b2)
CREATE (pol5)-[:AUTHORED {role: "co-author"}]->(b2)
CREATE (pol3)-[:AUTHORED {role: "co-author"}]->(b3)
CREATE (pol6)-[:AUTHORED {role: "principal"}]->(b4)
CREATE (pol8)-[:AUTHORED {role: "principal"}]->(b5)

// --- Co-authorship edges ---
CREATE (pol4)-[:CO_AUTHORED_WITH {bill_count: 3}]->(pol5)
CREATE (pol3)-[:CO_AUTHORED_WITH {bill_count: 2}]->(pol4)
CREATE (pol6)-[:CO_AUTHORED_WITH {bill_count: 1}]->(pol8)

// --- Subcontracting (red flag when excessive) ---
CREATE (con1)-[:SUBCONTRACTED_TO {contract_ref: "DPWH-R4A-2023-001"}]->(con2)
CREATE (con16)-[:SUBCONTRACTED_TO {contract_ref: "DVO-2023-001"}]->(con10)

// --- ASSOCIATED_WITH (business relationships between contractors) ---
CREATE (con3)-[:ASSOCIATED_WITH {relationship: "shared_address", details: "Both registered at Unit 5B, Pacific Tower, San Fernando, Pampanga"}]->(con12)
CREATE (con6)-[:ASSOCIATED_WITH {relationship: "shared_officers", details: "Ricardo Cruz-Salazar serves as officer in both companies"}]->(con18)

// --- Campaign finance, blacklisting, SALN, and enrichment scenarios ---
// Sources: COMELEC SOCE filings, GPPB Consolidated Blacklist, ombudsman.gov.ph SALN disclosures

// New agencies
CREATE (ag16:Agency {name: "DPWH DEO Tarlac", type: "national", department: "Department of Public Works and Highways", annual_budget: 1800000000})

// New municipalities
CREATE (mun11:Municipality {name: "Tarlac City", province: "Tarlac", region: "Central Luzon", population: 363681, income_class: "1st", psgc_code: "036916000"})
CREATE (mun12:Municipality {name: "Santiago City", province: "Isabela", region: "Cagayan Valley", population: 134830, income_class: "1st", psgc_code: "023109000"})
CREATE (mun11)-[:HAS_AGENCY]->(ag16)

// New contractors
CREATE (con21:Contractor {name: "Pampanga River Construction Corp.", registration_number: "PG-2019-0054321", address: "San Fernando, Pampanga", classification: "A", total_contracts: 15, total_value: 320000000})
CREATE (con22:Contractor {name: "MedPrime Supply Corp.", registration_number: "PG-2023-0198701", address: "Quezon City, Metro Manila", classification: "B", total_contracts: 8, total_value: 890000000, registered_capital: 625000})
CREATE (con23:Contractor {name: "Metro Prime Construction", registration_number: "PG-2018-0054322", address: "Unit 5B, 123 Rizal Ave, Mandaluyong", classification: "AA", total_contracts: 45, total_value: 780000000})
CREATE (con24:Contractor {name: "Metro Star Builders Corp.", registration_number: "PG-2022-0187654", address: "Unit 5B, 123 Rizal Ave, Mandaluyong", classification: "AA", total_contracts: 12, total_value: 340000000})
CREATE (con25:Contractor {name: "Cagayan Valley Builders Corp.", registration_number: "PG-2015-0043210", address: "Santiago City, Isabela", classification: "AAA", total_contracts: 67, total_value: 2100000000})
CREATE (con26:Contractor {name: "Central Plains Development Corp.", registration_number: "PG-2014-0038765", address: "Tarlac City, Tarlac", classification: "AAA", total_contracts: 89, total_value: 4200000000})

// Contractor locations
CREATE (con25)-[:LOCATED_IN]->(mun12)
CREATE (con26)-[:LOCATED_IN]->(mun11)

// New persons (beneficial owners and directors)
CREATE (per7:Person {name: "Ricardo Cruz-Fernandez", role: "owner"})
CREATE (per8:Person {name: "Antonio Reyes", role: "director"})
CREATE (per9:Person {name: "Elena Dy-Reyes", role: "owner"})

// Ownership
CREATE (con21)-[:OWNED_BY {share_percentage: 65}]->(per7)
CREATE (con23)-[:OWNED_BY {share_percentage: 60}]->(per8)
CREATE (con24)-[:OWNED_BY {share_percentage: 55}]->(per8)
CREATE (con25)-[:OWNED_BY {share_percentage: 40}]->(per9)

// Family connections
CREATE (per7)-[:FAMILY_OF {relationship: "brother-in-law"}]->(per5)
CREATE (per9)-[:FAMILY_OF {relationship: "sister"}]->(pol10)

// --- Circular subcontracting (Pacific Roadworks <-> Pampanga River) ---
CREATE (c51:Contract {reference_number: "DPWH-R4A-2023-005", title: "Drainage Improvement - San Fernando", amount: 98000000, procurement_method: "public_bidding", award_date: date("2023-05-10"), status: "completed", bid_count: 3, category: "infrastructure"})
CREATE (ag2)-[:PROCURED {fiscal_year: 2023}]->(c51)
CREATE (c51)-[:AWARDED_TO {award_date: date("2023-05-10"), bid_amount: 98000000}]->(con3)
CREATE (con3)-[:SUBCONTRACTED_TO {contract_ref: "DPWH-R4A-2023-005", subcontract_value: 68000000}]->(con21)
CREATE (con21)-[:SUBCONTRACTED_TO {contract_ref: "DPWH-R4A-2023-005-SUB", subcontract_value: 42000000}]->(con3)

// --- Shell company (MedPrime Supply — P625K capital, P890M contracts) ---
CREATE (c52:Contract {reference_number: "DOH-R3-2023-004", title: "COVID Medical Supplies Batch 1", amount: 445000000, procurement_method: "negotiated_emergency", award_date: date("2023-02-15"), status: "completed", bid_count: 1, category: "goods"})
CREATE (c53:Contract {reference_number: "DOH-R3-2023-005", title: "COVID Medical Supplies Batch 2", amount: 445000000, procurement_method: "negotiated_emergency", award_date: date("2023-03-01"), status: "completed", bid_count: 1, category: "goods"})
CREATE (ag4)-[:PROCURED {fiscal_year: 2023}]->(c52)
CREATE (ag4)-[:PROCURED {fiscal_year: 2023}]->(c53)
CREATE (c52)-[:AWARDED_TO {award_date: date("2023-02-15"), bid_amount: 445000000}]->(con22)
CREATE (c53)-[:AWARDED_TO {award_date: date("2023-03-01"), bid_amount: 445000000}]->(con22)

// --- Phoenix company (Metro Prime blacklisted -> Metro Star re-registered) ---
CREATE (bl1:BlacklistEntry {name: "Blacklisted: Metro Prime Construction", offense: "Falsified eligibility documents and substandard materials", sanction_period: "2022-2027", procuring_entity: "DPWH Region III", sanction_date: date("2022-06-15")})
CREATE (con23)-[:BLACKLISTED]->(bl1)
CREATE (con23)-[:RE_REGISTERED_AS {old_name: "Metro Prime Construction", new_name: "Metro Star Builders Corp.", same_directors: true}]->(con24)
CREATE (con23)-[:SAME_ADDRESS_AS {address: "Unit 5B, 123 Rizal Ave, Mandaluyong"}]->(con24)
CREATE (con23)-[:SHARES_DIRECTOR_WITH {director_name: "Antonio Reyes"}]->(con24)

CREATE (c54:Contract {reference_number: "DPWH-R4A-2024-003", title: "Road Rehabilitation - EDSA Extension", amount: 178000000, procurement_method: "public_bidding", award_date: date("2024-01-20"), status: "ongoing", bid_count: 3, category: "infrastructure"})
CREATE (ag2)-[:PROCURED {fiscal_year: 2024}]->(c54)
CREATE (c54)-[:AWARDED_TO {award_date: date("2024-01-20"), bid_amount: 178000000}]->(con24)

// --- Campaign donation pipeline (Golden Dragon -> Binay -> Makati contracts) ---
CREATE (cd1:CampaignDonation {name: "P5M Donation to Mayor Binay Campaign", amount: 5000000, election_year: 2022, election_type: "local", source_entity: "Golden Dragon Enterprises", recipient: "Abby Binay"})
CREATE (con5)-[:DONATED_TO {amount: 5000000, date: "2022-03-15"}]->(cd1)
CREATE (cd1)-[:DONATED_TO {election_year: 2022}]->(pol9)

// --- Cross-province political alliance (Dy-Binay, Cagayan Valley Builders in Makati) ---
CREATE (pol10)-[:ALLIED_WITH {alliance_type: "political", coalition: "UniTeam"}]->(pol9)
CREATE (c55:Contract {reference_number: "MAK-2023-005", title: "IT Infrastructure Upgrade - Makati City Hall", amount: 89000000, procurement_method: "negotiated", award_date: date("2023-06-15"), status: "completed", bid_count: 2, category: "infrastructure"})
CREATE (ag10)-[:PROCURED {fiscal_year: 2023}]->(c55)
CREATE (c55)-[:AWARDED_TO {award_date: date("2023-06-15"), bid_amount: 89000000}]->(con25)

// --- DPWH Tarlac total monopoly (Central Plains Development Corp, all single-bidder) ---
CREATE (c56:Contract {reference_number: "DPWH-TAR-2023-001", title: "Flood Control - Tarlac River", amount: 245000000, procurement_method: "public_bidding", award_date: date("2023-02-01"), status: "completed", bid_count: 1, category: "infrastructure"})
CREATE (c57:Contract {reference_number: "DPWH-TAR-2023-002", title: "Road Widening - MacArthur Hwy Segment 4", amount: 178000000, procurement_method: "public_bidding", award_date: date("2023-04-15"), status: "completed", bid_count: 1, category: "infrastructure"})
CREATE (c58:Contract {reference_number: "DPWH-TAR-2023-003", title: "Bridge Rehabilitation - O'Donnell River", amount: 134000000, procurement_method: "public_bidding", award_date: date("2023-07-01"), status: "ongoing", bid_count: 1, category: "infrastructure"})
CREATE (c59:Contract {reference_number: "DPWH-TAR-2023-004", title: "School Building Retrofit - Tarlac North", amount: 67000000, procurement_method: "public_bidding", award_date: date("2023-09-10"), status: "completed", bid_count: 1, category: "infrastructure"})
CREATE (ag16)-[:PROCURED {fiscal_year: 2023}]->(c56)
CREATE (ag16)-[:PROCURED {fiscal_year: 2023}]->(c57)
CREATE (ag16)-[:PROCURED {fiscal_year: 2023}]->(c58)
CREATE (ag16)-[:PROCURED {fiscal_year: 2023}]->(c59)
CREATE (c56)-[:AWARDED_TO {award_date: date("2023-02-01"), bid_amount: 245000000}]->(con26)
CREATE (c57)-[:AWARDED_TO {award_date: date("2023-04-15"), bid_amount: 178000000}]->(con26)
CREATE (c58)-[:AWARDED_TO {award_date: date("2023-07-01"), bid_amount: 134000000}]->(con26)
CREATE (c59)-[:AWARDED_TO {award_date: date("2023-09-10"), bid_amount: 67000000}]->(con26)

// --- SALN wealth declarations ---
CREATE (saln1:SALNRecord {name: "Binay SALN 2019", year: 2019, net_worth: 42000000, real_property: 25000000, personal_property: 8000000, liabilities: 5000000, annual_income: 1200000})
CREATE (saln2:SALNRecord {name: "Binay SALN 2023", year: 2023, net_worth: 90000000, real_property: 58000000, personal_property: 22000000, liabilities: 8000000, annual_income: 1400000})
CREATE (pol9)-[:DECLARED_WEALTH {year: 2019}]->(saln1)
CREATE (pol9)-[:DECLARED_WEALTH {year: 2023}]->(saln2)

// --- Additional audit findings ---
CREATE (af8:AuditFinding {type: "procurement_irregularity", severity: "critical", amount: 890000000, year: 2023, description: "P890M in emergency medical supplies awarded to company with P625K registered capital. Procurement justified under emergency provisions despite questionable eligibility.", recommendation: "Refer to Ombudsman; review eligibility screening", recommendation_status: "pending"})
CREATE (af9:AuditFinding {type: "competition_failure", severity: "high", amount: 624000000, year: 2023, description: "All four FY2023 contracts (P624M total) had only one bidder. No evidence of invitation to other qualified contractors.", recommendation: "Conduct post-procurement review; mandate re-bidding", recommendation_status: "noted"})
CREATE (ag4)-[:AUDITED {year: 2023}]->(af8)
CREATE (ag16)-[:AUDITED {year: 2023}]->(af9)
