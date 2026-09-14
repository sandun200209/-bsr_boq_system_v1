-- ==============================================================================
-- BSR Rate Hub – Supabase PostgreSQL Schema & Migration Script
-- ==============================================================================
-- This script sets up all tables, indexes, Row Level Security (RLS) policies,
-- trigram extensions, and default roles for Supabase Cloud PostgreSQL.
-- ==============================================================================

-- 1. Enable Required Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 2. Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'USER' NOT NULL, -- ADMIN, MANAGER, USER, VIEWER
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_users_username ON users(username);
CREATE INDEX IF NOT EXISTS ix_users_role ON users(role);

-- 3. Source Files Table (Metadata & Cloud Storage References)
CREATE TABLE IF NOT EXISTS source_files (
    id SERIAL PRIMARY KEY,
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) UNIQUE NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(20) NOT NULL,
    file_size INTEGER NOT NULL,
    sha256_hash VARCHAR(64) NOT NULL,
    province VARCHAR(80) NOT NULL,
    district VARCHAR(80) NOT NULL,
    year INTEGER NOT NULL,
    revision VARCHAR(120) NOT NULL,
    dataset_type VARCHAR(80) DEFAULT 'BSR Rate Book' NOT NULL,
    vat_basis VARCHAR(80) DEFAULT 'Without VAT' NOT NULL,
    category_hint VARCHAR(120),
    sector VARCHAR(100) DEFAULT 'Building Works' NOT NULL,
    rate_system VARCHAR(100) DEFAULT 'BSR' NOT NULL,
    storage_provider VARCHAR(50) DEFAULT 'local' NOT NULL, -- local, supabase
    storage_key VARCHAR(500),
    public_url VARCHAR(1000),
    uploaded_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    uploaded_by_email VARCHAR(255),
    upload_status VARCHAR(40) DEFAULT 'UPLOADED' NOT NULL,
    import_status VARCHAR(40) DEFAULT 'READY_FOR_REVIEW' NOT NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE,
    total_rows_detected INTEGER DEFAULT 0 NOT NULL,
    valid_rows INTEGER DEFAULT 0 NOT NULL,
    review_rows INTEGER DEFAULT 0 NOT NULL,
    rejected_rows INTEGER DEFAULT 0 NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_source_files_sector_rate_system ON source_files(sector, rate_system);
CREATE INDEX IF NOT EXISTS ix_source_files_uploaded_at ON source_files(uploaded_at DESC);

-- 4. Import Jobs Table
CREATE TABLE IF NOT EXISTS import_jobs (
    id SERIAL PRIMARY KEY,
    source_file_id INTEGER REFERENCES source_files(id) ON DELETE CASCADE,
    status VARCHAR(40) DEFAULT 'UPLOADED' NOT NULL,
    progress_percent INTEGER DEFAULT 0 NOT NULL,
    message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- 5. Master Items Table (Canonical Registry)
CREATE TABLE IF NOT EXISTS master_items (
    id SERIAL PRIMARY KEY,
    master_code VARCHAR(255) UNIQUE NOT NULL,
    canonical_description TEXT NOT NULL,
    canonical_unit VARCHAR(100) NOT NULL,
    category VARCHAR(500),
    sector VARCHAR(100) DEFAULT 'Building Works' NOT NULL,
    rate_system VARCHAR(100) DEFAULT 'BSR',
    notes TEXT,
    updated_by_email VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_master_items_sector_system ON master_items(sector, rate_system);

-- 6. Rate Items Table
CREATE TABLE IF NOT EXISTS rate_items (
    id SERIAL PRIMARY KEY,
    source_file_id INTEGER REFERENCES source_files(id) ON DELETE CASCADE,
    province VARCHAR(80) NOT NULL,
    district VARCHAR(80) NOT NULL,
    year INTEGER NOT NULL,
    revision VARCHAR(120) NOT NULL,
    dataset_type VARCHAR(80) DEFAULT 'BSR Rate Book' NOT NULL,
    vat_basis VARCHAR(80) DEFAULT 'Without VAT' NOT NULL,
    sector VARCHAR(100) DEFAULT 'Building Works' NOT NULL,
    rate_system VARCHAR(100) DEFAULT 'BSR' NOT NULL,
    category_code VARCHAR(255),
    category_name VARCHAR(500),
    item_code VARCHAR(255),
    description TEXT,
    unit VARCHAR(100),
    rate DOUBLE PRECISION,
    master_item_id INTEGER REFERENCES master_items(id) ON DELETE SET NULL,
    source_page INTEGER,
    source_sheet VARCHAR(255),
    source_row INTEGER,
    source_cell VARCHAR(255),
    raw_text TEXT,
    confidence_score DOUBLE PRECISION DEFAULT 1.0,
    validation_status VARCHAR(40) DEFAULT 'VALID' NOT NULL,
    validation_notes TEXT,
    updated_by_email VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    verified_at TIMESTAMP WITH TIME ZONE
);

-- GIN Trigram indexes for instant substring and fuzzy search
CREATE INDEX IF NOT EXISTS ix_rates_desc_trgm ON rate_items USING gin (description gin_trgm_ops);
CREATE INDEX IF NOT EXISTS ix_rates_code_trgm ON rate_items USING gin (item_code gin_trgm_ops);
CREATE INDEX IF NOT EXISTS ix_rate_items_sector_prov_dist_year ON rate_items(sector, province, district, year);
CREATE INDEX IF NOT EXISTS ix_rate_items_system_year_cat ON rate_items(rate_system, year, category_name);

-- 7. Rate Item to Master Item Mapping
CREATE TABLE IF NOT EXISTS rate_item_master_mapping (
    id SERIAL PRIMARY KEY,
    master_item_id INTEGER REFERENCES master_items(id) ON DELETE CASCADE,
    rate_item_id INTEGER UNIQUE REFERENCES rate_items(id) ON DELETE CASCADE,
    confidence DOUBLE PRECISION DEFAULT 1.0,
    mapped_by VARCHAR(80) DEFAULT 'user',
    mapped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- 8. Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    user_email VARCHAR(255),
    action VARCHAR(80) NOT NULL,
    entity_type VARCHAR(80) NOT NULL,
    entity_id VARCHAR(100),
    description TEXT,
    ip_address VARCHAR(80),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS ix_audit_logs_user_email ON audit_logs(user_email);
CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs(created_at DESC);

-- 9. Insert Default Seed Accounts (Bcrypt hashed)
INSERT INTO users (email, username, hashed_password, full_name, role, is_active)
VALUES 
('admin@bsrhub.lk', 'admin', '$2b$10$X55Hn1CvOMVlkh99P2Z/BOS8ZbTzNh48NF5wQHY3ElXhHaGK6m1Zy', 'System Administrator', 'ADMIN', true),
('manager@bsrhub.lk', 'manager', '$2b$10$2u..vMizRgwkrckhE8owYORCVXGMm7U1kb.EGqfSXhs27eB88Ww4C', 'Project Manager', 'MANAGER', true),
('qs@bsrhub.lk', 'qs_engineer', '$2b$10$MGyB1nQzESjgXRMBkrLFcOIZmkDoClrIkYG5P/H58iQMGwbFaT3Pe', 'Quantity Surveyor', 'USER', true),
('viewer@bsrhub.lk', 'viewer', '$2b$10$fgGdV5S87ASUKctheVeDHO2k6yz.h.oHamegU2TTOEdKKGGg6s1Y2', 'Executive Viewer', 'VIEWER', true)
ON CONFLICT (email) DO NOTHING;

-- 10. Enable Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE source_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE rate_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE master_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Allow authenticated and service_role access
CREATE POLICY "Allow public read on rate items" ON rate_items FOR SELECT USING (true);
CREATE POLICY "Allow public read on source files" ON source_files FOR SELECT USING (true);
CREATE POLICY "Allow public read on master items" ON master_items FOR SELECT USING (true);
CREATE POLICY "Allow full access for authenticated service role" ON rate_items USING (true) WITH CHECK (true);
CREATE POLICY "Allow full access for authenticated service role on files" ON source_files USING (true) WITH CHECK (true);
CREATE POLICY "Allow full access for authenticated service role on master" ON master_items USING (true) WITH CHECK (true);
CREATE POLICY "Allow full access for authenticated service role on users" ON users USING (true) WITH CHECK (true);
CREATE POLICY "Allow full access for authenticated service role on audit" ON audit_logs USING (true) WITH CHECK (true);
