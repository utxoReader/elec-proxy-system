-- ========================================
-- 桐叶售电系统 - 初始化数据库 Schema
-- Database: PostgreSQL 16
-- ========================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ========== Agent tables ==========
CREATE TABLE IF NOT EXISTS elec_agent (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255),
    role VARCHAR(20) NOT NULL DEFAULT 'agent',
    type INTEGER,
    parent_id INTEGER REFERENCES elec_agent(id),
    status INTEGER DEFAULT 0,
    tax_type INTEGER,
    remark TEXT,
    region VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX idx_elec_agent_parent ON elec_agent(parent_id);
CREATE INDEX idx_elec_agent_region ON elec_agent(region);

CREATE TABLE IF NOT EXISTS elec_agent_fee (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES elec_agent(id),
    agent_name VARCHAR(100),
    customer_account_id INTEGER,
    customer_name VARCHAR(100),
    fee_month VARCHAR(7),
    config_month VARCHAR(7),
    fee_date DATE,
    customer_consumption NUMERIC(16,4),
    customer_payment NUMERIC(16,4),
    company_cost NUMERIC(16,4),
    gross_profit NUMERIC(16,4),
    commission_rate NUMERIC(8,4),
    commission_amount NUMERIC(16,4),
    fee_type INTEGER,
    tax_type INTEGER,
    tax_rate NUMERIC(8,4),
    tax_amount NUMERIC(16,4),
    net_amount NUMERIC(16,4),
    settlement_status INTEGER DEFAULT 1,
    settlement_date DATE,
    payment_date DATE,
    payment_method INTEGER,
    payment_voucher VARCHAR(200),
    approval_status INTEGER DEFAULT 1,
    approver_id INTEGER,
    approver_name VARCHAR(50),
    approval_time TIMESTAMPTZ,
    approval_comment TEXT,
    remark TEXT,
    region VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX idx_agent_fee_agent ON elec_agent_fee(agent_id);
CREATE INDEX idx_agent_fee_customer ON elec_agent_fee(customer_account_id);

-- ========== Customer account tables ==========
CREATE TABLE IF NOT EXISTS elec_customer_account (
    id SERIAL PRIMARY KEY,
    customer_status INTEGER,
    agent_id INTEGER REFERENCES elec_agent(id),
    agent_name VARCHAR(100),
    customer_name VARCHAR(100),
    inquiry_time TIMESTAMPTZ,
    voltage_level VARCHAR(20),
    account_number VARCHAR(500),
    service_password VARCHAR(100),
    verification_code VARCHAR(50),
    contact_phone VARCHAR(20),
    contact_person VARCHAR(50),
    trading_center_account VARCHAR(100),
    trading_center_password VARCHAR(100),
    package_type INTEGER,
    price_difference NUMERIC(10,6),
    contract_start_date DATE,
    contract_end_date DATE,
    industry_type VARCHAR(50),
    enterprise_feature VARCHAR(50),
    production_time VARCHAR(50),
    credit_code VARCHAR(50),
    legal_person VARCHAR(50),
    email VARCHAR(100),
    address VARCHAR(200),
    remark TEXT,
    region VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX idx_customer_account_agent ON elec_customer_account(agent_id);

CREATE TABLE IF NOT EXISTS elec_customer_account_price_history (
    id SERIAL PRIMARY KEY,
    customer_account_id INTEGER REFERENCES elec_customer_account(id),
    customer_name VARCHAR(100),
    old_price_difference NUMERIC(10,6),
    new_price_difference NUMERIC(10,6),
    effective_date DATE,
    change_reason TEXT,
    change_type INTEGER,
    status INTEGER DEFAULT 1,
    region VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX idx_price_history_account ON elec_customer_account_price_history(customer_account_id);

-- ========== Inquiry ==========
CREATE TABLE IF NOT EXISTS elec_inquiry (
    id SERIAL PRIMARY KEY,
    inquiry_no VARCHAR(50) UNIQUE,
    agent_id INTEGER REFERENCES elec_agent(id),
    agent_name VARCHAR(100),
    customer_name VARCHAR(100),
    contact_person VARCHAR(50),
    contact_phone VARCHAR(20),
    voltage_level VARCHAR(20),
    customer_type INTEGER,
    usage_month VARCHAR(7),
    estimated_monthly_consumption NUMERIC(16,4),
    usage_address VARCHAR(200),
    industry_type VARCHAR(50),
    enterprise_feature VARCHAR(50),
    production_time VARCHAR(50),
    data_submit_type INTEGER,
    peak_consumption NUMERIC(16,4),
    high_consumption NUMERIC(16,4),
    normal_consumption NUMERIC(16,4),
    valley_consumption NUMERIC(16,4),
    usage_curve_template_id INTEGER,
    usage_curve_template_name VARCHAR(100),
    inquiry_status INTEGER DEFAULT 1,
    is_second_inquiry INTEGER DEFAULT 0,
    reject_reason TEXT,
    customer_confirm_time TIMESTAMPTZ,
    admin_confirm_time TIMESTAMPTZ,
    cooperation_start_date DATE,
    cooperation_end_date DATE,
    terminate_date DATE,
    quoted_at TIMESTAMPTZ,
    quote_valid_until TIMESTAMPTZ,
    recommended_package_type INTEGER,
    price_difference NUMERIC(10,6),
    estimated_monthly_fee NUMERIC(16,4),
    estimated_savings NUMERIC(16,4),
    savings_rate NUMERIC(8,4),
    remark TEXT,
    consumption_data_json TEXT,
    consumption_summary TEXT,
    region VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX idx_inquiry_agent ON elec_inquiry(agent_id);

-- ========== Price tables ==========
CREATE TABLE IF NOT EXISTS elec_base_price (
    id SERIAL PRIMARY KEY,
    price_type INTEGER,
    price_date DATE,
    hour_index INTEGER,
    price NUMERIC(10,6),
    status INTEGER DEFAULT 0,
    remark TEXT,
    region VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS elec_grid_price (
    id SERIAL PRIMARY KEY,
    year_month VARCHAR(7),
    time_period INTEGER,
    start_time TIME,
    end_time TIME,
    base_price NUMERIC(10,6),
    price NUMERIC(10,6),
    price_coefficient NUMERIC(6,4),
    applicable_months VARCHAR(50),
    status INTEGER DEFAULT 0,
    remark TEXT,
    region VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS elec_wholesale_price (
    id SERIAL PRIMARY KEY,
    price_date DATE,
    price_month VARCHAR(7),
    hour_index INTEGER,
    time_period VARCHAR(10),
    wholesale_price NUMERIC(10,6),
    price_type INTEGER,
    data_source INTEGER,
    status INTEGER,
    remark TEXT,
    region VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS elec_market_allocation_price (
    id SERIAL PRIMARY KEY,
    year_month VARCHAR(7),
    allocation_price NUMERIC(10,6),
    price_date DATE,
    status INTEGER DEFAULT 0,
    remark TEXT,
    region VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS elec_other_fee (
    id SERIAL PRIMARY KEY,
    month_config VARCHAR(7),
    distribution_price NUMERIC(10,6),
    government_fund NUMERIC(10,6),
    cross_subsidy NUMERIC(10,6),
    line_loss_fee NUMERIC(10,6),
    status INTEGER DEFAULT 0,
    remark TEXT,
    region VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- ========== Commission config ==========
CREATE TABLE IF NOT EXISTS elec_commission_config (
    id SERIAL PRIMARY KEY,
    config_month VARCHAR(7),
    effective_month VARCHAR(7),
    agent_commission_rate NUMERIC(8,4) DEFAULT 50.0000,
    parent_commission_rate NUMERIC(8,4) DEFAULT 5.0000,
    company_commission_rate NUMERIC(8,4) DEFAULT 45.0000,
    status INTEGER DEFAULT 1,
    remark TEXT,
    region VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- ========== Consumption tables ==========
CREATE TABLE IF NOT EXISTS elec_customer_daily_consumption (
    id SERIAL PRIMARY KEY,
    customer_account_id INTEGER REFERENCES elec_customer_account(id),
    inquiry_id INTEGER,
    customer_name VARCHAR(100),
    account_number VARCHAR(50),
    data_date DATE,
    data_month VARCHAR(7)
);
-- Add 24 hour columns
DO $$
DECLARE
    i INT;
BEGIN
    FOR i IN 0..23 LOOP
        EXECUTE format('ALTER TABLE elec_customer_daily_consumption ADD COLUMN hour_%s NUMERIC(12,4)', LPAD(i::text, 2, '0'));
    END LOOP;
END $$;
ALTER TABLE elec_customer_daily_consumption ADD COLUMN total_consumption NUMERIC(16,4);
ALTER TABLE elec_customer_daily_consumption ADD COLUMN peak_consumption NUMERIC(16,4);
ALTER TABLE elec_customer_daily_consumption ADD COLUMN high_consumption NUMERIC(16,4);
ALTER TABLE elec_customer_daily_consumption ADD COLUMN normal_consumption NUMERIC(16,4);
ALTER TABLE elec_customer_daily_consumption ADD COLUMN valley_consumption NUMERIC(16,4);
ALTER TABLE elec_customer_daily_consumption ADD COLUMN data_type INTEGER DEFAULT 1;
ALTER TABLE elec_customer_daily_consumption ADD COLUMN data_source INTEGER DEFAULT 1;
ALTER TABLE elec_customer_daily_consumption ADD COLUMN package_type INTEGER;
ALTER TABLE elec_customer_daily_consumption ADD COLUMN price_difference NUMERIC(10,6);
ALTER TABLE elec_customer_daily_consumption ADD COLUMN import_file_name VARCHAR(200);
ALTER TABLE elec_customer_daily_consumption ADD COLUMN import_batch_id VARCHAR(50);
ALTER TABLE elec_customer_daily_consumption ADD COLUMN raw_data_count INTEGER;
ALTER TABLE elec_customer_daily_consumption ADD COLUMN remarks TEXT;
ALTER TABLE elec_customer_daily_consumption ADD COLUMN commission_status INTEGER DEFAULT 1;
ALTER TABLE elec_customer_daily_consumption ADD COLUMN data_locked BOOLEAN DEFAULT FALSE;
ALTER TABLE elec_customer_daily_consumption ADD COLUMN commission_calculated_time DATE;
ALTER TABLE elec_customer_daily_consumption ADD COLUMN region VARCHAR(20);
ALTER TABLE elec_customer_daily_consumption ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE elec_customer_daily_consumption ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE elec_customer_daily_consumption ADD COLUMN deleted_at TIMESTAMPTZ;
CREATE INDEX idx_daily_consumption_customer ON elec_customer_daily_consumption(customer_account_id);
CREATE INDEX idx_daily_consumption_date ON elec_customer_daily_consumption(data_date);

CREATE TABLE IF NOT EXISTS elec_customer_hourly_consumption (
    id SERIAL PRIMARY KEY,
    customer_account_id INTEGER REFERENCES elec_customer_account(id),
    inquiry_id INTEGER,
    customer_name VARCHAR(100),
    data_date DATE,
    data_month VARCHAR(7),
    hour_index INTEGER,
    consumption NUMERIC(12,4),
    time_period INTEGER,
    data_type INTEGER DEFAULT 1,
    data_source INTEGER DEFAULT 1,
    package_type INTEGER,
    retail_unit_price NUMERIC(10,6),
    delivered_unit_price NUMERIC(10,6),
    wholesale_unit_price NUMERIC(10,6),
    remarks TEXT,
    region VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX idx_hourly_consumption_customer ON elec_customer_hourly_consumption(customer_account_id);

-- ========== 96-point data ==========
CREATE TABLE IF NOT EXISTS elec_point96_data (
    id SERIAL PRIMARY KEY,
    customer_account_id INTEGER REFERENCES elec_customer_account(id),
    market_member_name VARCHAR(100),
    account_number VARCHAR(50),
    measure_point VARCHAR(50),
    data_date DATE,
    is_contracted BOOLEAN,
    trading_unit_name VARCHAR(100),
    total_consumption NUMERIC(16,4),
    batch_no VARCHAR(50),
    processed INTEGER DEFAULT 0,
    convert_time DATE,
    region VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- Add 96 point columns
DO $$
DECLARE
    h INT;
    m INT;
BEGIN
    FOR h IN 0..23 LOOP
        FOR m IN 0, 15, 30, 45 LOOP
            EXECUTE format('ALTER TABLE elec_point96_data ADD COLUMN p%s%s NUMERIC(10,4)', LPAD(h::text, 2, '0'), LPAD(m::text, 2, '0'));
        END LOOP;
    END LOOP;
END $$;

-- ========== Profit tables ==========
CREATE TABLE IF NOT EXISTS elec_customer_daily_profit (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER,
    customer_name VARCHAR(100),
    profit_date DATE,
    profit_month VARCHAR(7),
    agent_id INTEGER,
    agent_name VARCHAR(100),
    parent_agent_id INTEGER,
    parent_agent_name VARCHAR(100),
    total_consumption NUMERIC(16,4),
    adjustment_consumption NUMERIC(16,4),
    retail_fee NUMERIC(16,4),
    wholesale_fee NUMERIC(16,4),
    market_allocation_fee NUMERIC(16,4),
    total_profit NUMERIC(16,4),
    agent_commission_rate NUMERIC(8,4),
    agent_commission_amount NUMERIC(16,4),
    agent_tax_type INTEGER,
    agent_net_amount NUMERIC(16,4),
    parent_commission_rate NUMERIC(8,4),
    parent_commission_amount NUMERIC(16,4),
    parent_tax_type INTEGER,
    parent_net_amount NUMERIC(16,4),
    company_commission_amount NUMERIC(16,4),
    status INTEGER DEFAULT 1,
    adjustment_status INTEGER DEFAULT 0,
    remark TEXT,
    price_difference NUMERIC(10,6),
    region VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX idx_daily_profit_customer ON elec_customer_daily_profit(customer_id);

CREATE TABLE IF NOT EXISTS elec_customer_hourly_profit (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER,
    customer_name VARCHAR(100),
    profit_date DATE,
    profit_month VARCHAR(7),
    hour INTEGER,
    time_start VARCHAR(10),
    time_end VARCHAR(10),
    agent_id INTEGER,
    agent_name VARCHAR(100),
    time_period INTEGER,
    time_period_name VARCHAR(10),
    package_type INTEGER,
    package_type_name VARCHAR(20),
    consumption NUMERIC(12,4),
    retail_unit_price NUMERIC(10,6),
    wholesale_unit_price NUMERIC(10,6),
    customer_unit_price NUMERIC(10,6),
    market_allocation_unit_price NUMERIC(10,6),
    retail_fee NUMERIC(16,4),
    wholesale_fee NUMERIC(16,4),
    market_allocation_fee NUMERIC(16,4),
    profit NUMERIC(16,4),
    price_difference NUMERIC(10,6),
    base_price NUMERIC(10,6),
    remark TEXT,
    region VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS elec_customer_monthly_profit (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER,
    customer_name VARCHAR(100),
    profit_month VARCHAR(7),
    agent_id INTEGER,
    agent_name VARCHAR(100),
    parent_agent_id INTEGER,
    parent_agent_name VARCHAR(100),
    total_consumption NUMERIC(16,4),
    adjustment_consumption NUMERIC(16,4),
    final_consumption NUMERIC(16,4),
    retail_fee NUMERIC(16,4),
    wholesale_fee NUMERIC(16,4),
    market_allocation_fee NUMERIC(16,4),
    adjustment_fee NUMERIC(16,4),
    total_profit NUMERIC(16,4),
    adjusted_total_profit NUMERIC(16,4),
    agent_commission_rate NUMERIC(8,4),
    agent_commission_amount NUMERIC(16,4),
    agent_tax_type INTEGER,
    agent_net_amount NUMERIC(16,4),
    parent_commission_rate NUMERIC(8,4),
    parent_commission_amount NUMERIC(16,4),
    parent_tax_type INTEGER,
    parent_net_amount NUMERIC(16,4),
    company_commission_amount NUMERIC(16,4),
    status INTEGER DEFAULT 1,
    adjustment_status INTEGER DEFAULT 0,
    settlement_status INTEGER DEFAULT 0,
    data_days_count INTEGER,
    expected_days_count INTEGER,
    data_completeness_rate NUMERIC(6,4),
    region VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX idx_monthly_profit_customer ON elec_customer_monthly_profit(customer_id);
CREATE INDEX idx_monthly_profit_month ON elec_customer_monthly_profit(profit_month);

-- ========== Usage curve template ==========
CREATE TABLE IF NOT EXISTS elec_usage_curve_template (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(100),
    description TEXT,
    template_type INTEGER,
    industry VARCHAR(50),
    image_url VARCHAR(200),
    status INTEGER DEFAULT 1,
    is_default INTEGER DEFAULT 0,
    sort INTEGER,
    region VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);
-- Add 48 ratio columns
DO $$
DECLARE
    i INT;
BEGIN
    FOR i IN 0..23 LOOP
        EXECUTE format('ALTER TABLE elec_usage_curve_template ADD COLUMN hour_%s_ratio NUMERIC(8,4)', LPAD(i::text, 2, '0'));
        EXECUTE format('ALTER TABLE elec_usage_curve_template ADD COLUMN hour_%s_peak_ratio NUMERIC(8,4)', LPAD(i::text, 2, '0'));
    END LOOP;
END $$;

-- ========== Import task ==========
CREATE TABLE IF NOT EXISTS elec_import_task (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(50),
    original_filename VARCHAR(200),
    file_path VARCHAR(500),
    file_size BIGINT,
    task_status INTEGER DEFAULT 0,
    progress INTEGER DEFAULT 0,
    total_rows INTEGER,
    success_rows INTEGER,
    failed_rows INTEGER,
    skipped_rows INTEGER,
    error_message TEXT,
    progress_message TEXT,
    result_summary TEXT,
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    region VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX idx_import_task_id ON elec_import_task(task_id);
