"""Initial schema — all 19 tables for 桐叶售电系统

Revision ID: 001
Revises:
Create Date: 2026-06-24

This migration creates the complete database schema matching the
SQLAlchemy models. It mirrors migrations/001_init.sql and includes
the password_hash and role columns on elec_agent for authentication.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # ========== Agent tables ==========
    op.execute("""
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
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_elec_agent_parent ON elec_agent(parent_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_elec_agent_region ON elec_agent(region)")

    op.execute("""
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
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_agent_fee_agent ON elec_agent_fee(agent_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_agent_fee_customer ON elec_agent_fee(customer_account_id)")

    # ========== Customer tables ==========
    op.execute("""
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
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_customer_account_agent ON elec_customer_account(agent_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_customer_account_status ON elec_customer_account(customer_status)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS elec_customer_account_price_history (
            id SERIAL PRIMARY KEY,
            customer_account_id INTEGER REFERENCES elec_customer_account(id),
            customer_name VARCHAR(100),
            old_price_difference NUMERIC(10,6),
            new_price_difference NUMERIC(10,6),
            old_contract_start_date DATE,
            old_contract_end_date DATE,
            new_contract_start_date DATE,
            new_contract_end_date DATE,
            effective_date DATE,
            change_reason VARCHAR(500),
            change_type INTEGER,
            status INTEGER DEFAULT 1,
            applied_at TIMESTAMPTZ,
            region VARCHAR(20),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)

    # ========== Inquiry ==========
    op.execute("""
        CREATE TABLE IF NOT EXISTS elec_inquiry (
            id SERIAL PRIMARY KEY,
            inquiry_no VARCHAR(50),
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
            is_second_inquiry BOOLEAN DEFAULT FALSE,
            reject_reason TEXT,
            customer_confirm_time TIMESTAMPTZ,
            admin_confirm_time TIMESTAMPTZ,
            cooperation_start_date DATE,
            cooperation_end_date DATE,
            terminate_date DATE,
            quoted_at TIMESTAMPTZ,
            quote_valid_until DATE,
            recommended_package_type INTEGER,
            price_difference NUMERIC(10,6),
            estimated_monthly_fee NUMERIC(16,4),
            estimated_savings NUMERIC(16,4),
            savings_rate NUMERIC(8,4),
            remark TEXT,
            consumption_data_json JSONB,
            consumption_summary TEXT,
            region VARCHAR(20),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_inquiry_agent ON elec_inquiry(agent_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_inquiry_status ON elec_inquiry(inquiry_status)")

    # ========== Consumption tables ==========
    op.execute("""
        CREATE TABLE IF NOT EXISTS elec_customer_daily_consumption (
            id SERIAL PRIMARY KEY,
            customer_account_id INTEGER,
            inquiry_id INTEGER,
            customer_name VARCHAR(100),
            account_number VARCHAR(200),
            data_date DATE NOT NULL,
            data_month VARCHAR(7),
            hour_00 NUMERIC(16,4), hour_01 NUMERIC(16,4), hour_02 NUMERIC(16,4),
            hour_03 NUMERIC(16,4), hour_04 NUMERIC(16,4), hour_05 NUMERIC(16,4),
            hour_06 NUMERIC(16,4), hour_07 NUMERIC(16,4), hour_08 NUMERIC(16,4),
            hour_09 NUMERIC(16,4), hour_10 NUMERIC(16,4), hour_11 NUMERIC(16,4),
            hour_12 NUMERIC(16,4), hour_13 NUMERIC(16,4), hour_14 NUMERIC(16,4),
            hour_15 NUMERIC(16,4), hour_16 NUMERIC(16,4), hour_17 NUMERIC(16,4),
            hour_18 NUMERIC(16,4), hour_19 NUMERIC(16,4), hour_20 NUMERIC(16,4),
            hour_21 NUMERIC(16,4), hour_22 NUMERIC(16,4), hour_23 NUMERIC(16,4),
            total_consumption NUMERIC(16,4),
            peak_consumption NUMERIC(16,4),
            high_consumption NUMERIC(16,4),
            normal_consumption NUMERIC(16,4),
            valley_consumption NUMERIC(16,4),
            data_type INTEGER,
            data_source INTEGER,
            package_type INTEGER,
            price_difference NUMERIC(10,6),
            import_file_name VARCHAR(200),
            import_batch_id VARCHAR(50),
            raw_data_count INTEGER,
            remarks TEXT,
            commission_status INTEGER DEFAULT 1,
            data_locked BOOLEAN DEFAULT FALSE,
            commission_calculated_time TIMESTAMPTZ,
            region VARCHAR(20),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_daily_consumption_customer ON elec_customer_daily_consumption(customer_account_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_daily_consumption_date ON elec_customer_daily_consumption(data_date)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS elec_customer_hourly_consumption (
            id SERIAL PRIMARY KEY,
            customer_account_id INTEGER,
            inquiry_id INTEGER,
            customer_name VARCHAR(100),
            data_date DATE NOT NULL,
            data_month VARCHAR(7),
            hour_index INTEGER NOT NULL,
            consumption NUMERIC(16,4),
            time_period INTEGER,
            data_type INTEGER,
            data_source INTEGER,
            package_type INTEGER,
            retail_unit_price NUMERIC(10,6),
            delivered_unit_price NUMERIC(10,6),
            wholesale_unit_price NUMERIC(10,6),
            remarks TEXT,
            region VARCHAR(20),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_hourly_consumption_customer ON elec_customer_hourly_consumption(customer_account_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_hourly_consumption_date ON elec_customer_hourly_consumption(data_date)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS elec_point96_data (
            id SERIAL PRIMARY KEY,
            customer_account_id INTEGER,
            market_member_name VARCHAR(100),
            account_number VARCHAR(100),
            measure_point VARCHAR(50),
            data_date DATE NOT NULL,
            is_contracted BOOLEAN,
            trading_unit_name VARCHAR(100),
            total_consumption NUMERIC(16,4),
            p0015 NUMERIC(16,4), p0030 NUMERIC(16,4), p0045 NUMERIC(16,4),
            p0100 NUMERIC(16,4), p0115 NUMERIC(16,4), p0130 NUMERIC(16,4),
            p0145 NUMERIC(16,4), p0200 NUMERIC(16,4), p0215 NUMERIC(16,4),
            p0230 NUMERIC(16,4), p0245 NUMERIC(16,4), p0300 NUMERIC(16,4),
            p0315 NUMERIC(16,4), p0330 NUMERIC(16,4), p0345 NUMERIC(16,4),
            p0400 NUMERIC(16,4), p0415 NUMERIC(16,4), p0430 NUMERIC(16,4),
            p0445 NUMERIC(16,4), p0500 NUMERIC(16,4), p0515 NUMERIC(16,4),
            p0530 NUMERIC(16,4), p0545 NUMERIC(16,4), p0600 NUMERIC(16,4),
            p0615 NUMERIC(16,4), p0630 NUMERIC(16,4), p0645 NUMERIC(16,4),
            p0700 NUMERIC(16,4), p0715 NUMERIC(16,4), p0730 NUMERIC(16,4),
            p0745 NUMERIC(16,4), p0800 NUMERIC(16,4), p0815 NUMERIC(16,4),
            p0830 NUMERIC(16,4), p0845 NUMERIC(16,4), p0900 NUMERIC(16,4),
            p0915 NUMERIC(16,4), p0930 NUMERIC(16,4), p0945 NUMERIC(16,4),
            p1000 NUMERIC(16,4), p1015 NUMERIC(16,4), p1030 NUMERIC(16,4),
            p1045 NUMERIC(16,4), p1100 NUMERIC(16,4), p1115 NUMERIC(16,4),
            p1130 NUMERIC(16,4), p1145 NUMERIC(16,4), p1200 NUMERIC(16,4),
            p1215 NUMERIC(16,4), p1230 NUMERIC(16,4), p1245 NUMERIC(16,4),
            p1300 NUMERIC(16,4), p1315 NUMERIC(16,4), p1330 NUMERIC(16,4),
            p1345 NUMERIC(16,4), p1400 NUMERIC(16,4), p1415 NUMERIC(16,4),
            p1430 NUMERIC(16,4), p1445 NUMERIC(16,4), p1500 NUMERIC(16,4),
            p1515 NUMERIC(16,4), p1530 NUMERIC(16,4), p1545 NUMERIC(16,4),
            p1600 NUMERIC(16,4), p1615 NUMERIC(16,4), p1630 NUMERIC(16,4),
            p1645 NUMERIC(16,4), p1700 NUMERIC(16,4), p1715 NUMERIC(16,4),
            p1730 NUMERIC(16,4), p1745 NUMERIC(16,4), p1800 NUMERIC(16,4),
            p1815 NUMERIC(16,4), p1830 NUMERIC(16,4), p1845 NUMERIC(16,4),
            p1900 NUMERIC(16,4), p1915 NUMERIC(16,4), p1930 NUMERIC(16,4),
            p1945 NUMERIC(16,4), p2000 NUMERIC(16,4), p2015 NUMERIC(16,4),
            p2030 NUMERIC(16,4), p2045 NUMERIC(16,4), p2100 NUMERIC(16,4),
            p2115 NUMERIC(16,4), p2130 NUMERIC(16,4), p2145 NUMERIC(16,4),
            p2200 NUMERIC(16,4), p2215 NUMERIC(16,4), p2230 NUMERIC(16,4),
            p2245 NUMERIC(16,4), p2300 NUMERIC(16,4), p2315 NUMERIC(16,4),
            p2330 NUMERIC(16,4), p2345 NUMERIC(16,4),
            batch_no VARCHAR(50),
            processed BOOLEAN DEFAULT FALSE,
            convert_time TIMESTAMPTZ,
            region VARCHAR(20),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_point96_customer ON elec_point96_data(customer_account_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_point96_date ON elec_point96_data(data_date)")

    # ========== Price tables ==========
    op.execute("""
        CREATE TABLE IF NOT EXISTS elec_base_price (
            id SERIAL PRIMARY KEY,
            price_type INTEGER DEFAULT 1,
            price_date DATE NOT NULL,
            hour_index INTEGER NOT NULL,
            price NUMERIC(10,6),
            status INTEGER DEFAULT 0,
            remark TEXT,
            region VARCHAR(20),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_base_price_date ON elec_base_price(price_date)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_base_price_type ON elec_base_price(price_type)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS elec_grid_price (
            id SERIAL PRIMARY KEY,
            year_month VARCHAR(7) NOT NULL,
            time_period INTEGER NOT NULL,
            start_time TIME,
            end_time TIME,
            base_price NUMERIC(10,6),
            price NUMERIC(10,6),
            price_coefficient NUMERIC(8,4),
            applicable_months VARCHAR(50),
            status INTEGER DEFAULT 0,
            remark TEXT,
            region VARCHAR(20),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_grid_price_month ON elec_grid_price(year_month)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS elec_wholesale_price (
            id SERIAL PRIMARY KEY,
            price_date DATE NOT NULL,
            price_month VARCHAR(7),
            hour_index INTEGER NOT NULL,
            time_period VARCHAR(10),
            wholesale_price NUMERIC(10,6),
            price_type INTEGER,
            data_source INTEGER,
            status INTEGER DEFAULT 0,
            remark TEXT,
            region VARCHAR(20),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_wholesale_price_date ON elec_wholesale_price(price_date)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_wholesale_price_month ON elec_wholesale_price(price_month)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS elec_market_allocation_price (
            id SERIAL PRIMARY KEY,
            year_month VARCHAR(7) NOT NULL,
            allocation_price NUMERIC(10,6),
            price_date DATE,
            status INTEGER DEFAULT 0,
            remark TEXT,
            region VARCHAR(20),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_market_allocation_month ON elec_market_allocation_price(year_month)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS elec_other_fee (
            id SERIAL PRIMARY KEY,
            month_config VARCHAR(7) NOT NULL,
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
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_other_fee_month ON elec_other_fee(month_config)")

    # ========== Profit tables ==========
    op.execute("""
        CREATE TABLE IF NOT EXISTS elec_customer_daily_profit (
            id SERIAL PRIMARY KEY,
            customer_id INTEGER,
            customer_name VARCHAR(100),
            profit_date DATE NOT NULL,
            profit_month VARCHAR(7),
            agent_id INTEGER,
            total_consumption NUMERIC(16,4),
            retail_fee NUMERIC(16,4),
            wholesale_fee NUMERIC(16,4),
            market_allocation_fee NUMERIC(16,4),
            total_profit NUMERIC(16,4),
            price_difference NUMERIC(10,6),
            agent_commission_amount NUMERIC(16,4),
            company_commission_amount NUMERIC(16,4),
            status INTEGER DEFAULT 1,
            remark TEXT,
            region VARCHAR(20),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_daily_profit_customer ON elec_customer_daily_profit(customer_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_daily_profit_date ON elec_customer_daily_profit(profit_date)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS elec_customer_hourly_profit (
            id SERIAL PRIMARY KEY,
            customer_id INTEGER,
            customer_name VARCHAR(100),
            profit_date DATE NOT NULL,
            profit_month VARCHAR(7),
            hour INTEGER NOT NULL,
            time_start TIME,
            time_end TIME,
            time_period INTEGER,
            time_period_name VARCHAR(10),
            consumption NUMERIC(16,4),
            retail_unit_price NUMERIC(10,6),
            wholesale_unit_price NUMERIC(10,6),
            retail_fee NUMERIC(16,4),
            wholesale_fee NUMERIC(16,4),
            market_allocation_fee NUMERIC(16,4),
            profit NUMERIC(16,4),
            region VARCHAR(20),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_hourly_profit_customer ON elec_customer_hourly_profit(customer_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS elec_customer_monthly_profit (
            id SERIAL PRIMARY KEY,
            customer_id INTEGER,
            customer_name VARCHAR(100),
            profit_month VARCHAR(7) NOT NULL,
            agent_id INTEGER,
            agent_name VARCHAR(100),
            total_consumption NUMERIC(16,4),
            retail_fee NUMERIC(16,4),
            wholesale_fee NUMERIC(16,4),
            market_allocation_fee NUMERIC(16,4),
            total_profit NUMERIC(16,4),
            adjusted_total_profit NUMERIC(16,4),
            status INTEGER DEFAULT 1,
            adjustment_status INTEGER DEFAULT 0,
            adjustment_consumption NUMERIC(16,4),
            adjustment_remark TEXT,
            settlement_status INTEGER DEFAULT 0,
            data_days_count INTEGER,
            expected_days_count INTEGER,
            data_completeness_rate NUMERIC(8,4),
            remark TEXT,
            region VARCHAR(20),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_monthly_profit_customer ON elec_customer_monthly_profit(customer_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_monthly_profit_month ON elec_customer_monthly_profit(profit_month)")

    # ========== Commission ==========
    op.execute("""
        CREATE TABLE IF NOT EXISTS elec_commission_config (
            id SERIAL PRIMARY KEY,
            effective_month VARCHAR(7) NOT NULL,
            agent_commission_rate NUMERIC(8,4) DEFAULT 0.50,
            parent_commission_rate NUMERIC(8,4) DEFAULT 0.05,
            company_commission_rate NUMERIC(8,4) DEFAULT 0.45,
            status INTEGER DEFAULT 0,
            remark TEXT,
            region VARCHAR(20),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)

    # ========== Usage curve template ==========
    op.execute("""
        CREATE TABLE IF NOT EXISTS elec_usage_curve_template (
            id SERIAL PRIMARY KEY,
            template_name VARCHAR(100) NOT NULL,
            description TEXT,
            template_type VARCHAR(50),
            industry VARCHAR(50),
            image_url VARCHAR(200),
            hour_00_ratio NUMERIC(8,6), hour_01_ratio NUMERIC(8,6), hour_02_ratio NUMERIC(8,6),
            hour_03_ratio NUMERIC(8,6), hour_04_ratio NUMERIC(8,6), hour_05_ratio NUMERIC(8,6),
            hour_06_ratio NUMERIC(8,6), hour_07_ratio NUMERIC(8,6), hour_08_ratio NUMERIC(8,6),
            hour_09_ratio NUMERIC(8,6), hour_10_ratio NUMERIC(8,6), hour_11_ratio NUMERIC(8,6),
            hour_12_ratio NUMERIC(8,6), hour_13_ratio NUMERIC(8,6), hour_14_ratio NUMERIC(8,6),
            hour_15_ratio NUMERIC(8,6), hour_16_ratio NUMERIC(8,6), hour_17_ratio NUMERIC(8,6),
            hour_18_ratio NUMERIC(8,6), hour_19_ratio NUMERIC(8,6), hour_20_ratio NUMERIC(8,6),
            hour_21_ratio NUMERIC(8,6), hour_22_ratio NUMERIC(8,6), hour_23_ratio NUMERIC(8,6),
            hour_00_peak_ratio NUMERIC(8,6), hour_01_peak_ratio NUMERIC(8,6), hour_02_peak_ratio NUMERIC(8,6),
            hour_03_peak_ratio NUMERIC(8,6), hour_04_peak_ratio NUMERIC(8,6), hour_05_peak_ratio NUMERIC(8,6),
            hour_06_peak_ratio NUMERIC(8,6), hour_07_peak_ratio NUMERIC(8,6), hour_08_peak_ratio NUMERIC(8,6),
            hour_09_peak_ratio NUMERIC(8,6), hour_10_peak_ratio NUMERIC(8,6), hour_11_peak_ratio NUMERIC(8,6),
            hour_12_peak_ratio NUMERIC(8,6), hour_13_peak_ratio NUMERIC(8,6), hour_14_peak_ratio NUMERIC(8,6),
            hour_15_peak_ratio NUMERIC(8,6), hour_16_peak_ratio NUMERIC(8,6), hour_17_peak_ratio NUMERIC(8,6),
            hour_18_peak_ratio NUMERIC(8,6), hour_19_peak_ratio NUMERIC(8,6), hour_20_peak_ratio NUMERIC(8,6),
            hour_21_peak_ratio NUMERIC(8,6), hour_22_peak_ratio NUMERIC(8,6), hour_23_peak_ratio NUMERIC(8,6),
            status INTEGER DEFAULT 1,
            is_default BOOLEAN DEFAULT FALSE,
            sort INTEGER DEFAULT 0,
            region VARCHAR(20),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)

    # ========== Import task ==========
    op.execute("""
        CREATE TABLE IF NOT EXISTS elec_import_task (
            id SERIAL PRIMARY KEY,
            task_id VARCHAR(50) NOT NULL,
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
            progress_message VARCHAR(500),
            result_summary TEXT,
            start_time TIMESTAMPTZ,
            end_time TIMESTAMPTZ,
            region VARCHAR(20),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)

    # ========== Seed: default admin user ==========
    op.execute("""
        INSERT INTO elec_agent (name, password_hash, role, type, status)
        SELECT 'admin', '$2b$12$LJ3m4ys3Lg2F3eOqX8mYrOEPJjZjZRPiFqGzVQO5mVYvZL5xL3WmK', 'admin', 1, 0
        WHERE NOT EXISTS (SELECT 1 FROM elec_agent WHERE name = 'admin')
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS elec_import_task")
    op.execute("DROP TABLE IF EXISTS elec_usage_curve_template")
    op.execute("DROP TABLE IF EXISTS elec_commission_config")
    op.execute("DROP TABLE IF EXISTS elec_customer_monthly_profit")
    op.execute("DROP TABLE IF EXISTS elec_customer_hourly_profit")
    op.execute("DROP TABLE IF EXISTS elec_customer_daily_profit")
    op.execute("DROP TABLE IF EXISTS elec_other_fee")
    op.execute("DROP TABLE IF EXISTS elec_market_allocation_price")
    op.execute("DROP TABLE IF EXISTS elec_wholesale_price")
    op.execute("DROP TABLE IF EXISTS elec_grid_price")
    op.execute("DROP TABLE IF EXISTS elec_base_price")
    op.execute("DROP TABLE IF EXISTS elec_point96_data")
    op.execute("DROP TABLE IF EXISTS elec_customer_hourly_consumption")
    op.execute("DROP TABLE IF EXISTS elec_customer_daily_consumption")
    op.execute("DROP TABLE IF EXISTS elec_inquiry")
    op.execute("DROP TABLE IF EXISTS elec_customer_account_price_history")
    op.execute("DROP TABLE IF EXISTS elec_customer_account")
    op.execute("DROP TABLE IF EXISTS elec_agent_fee")
    op.execute("DROP TABLE IF EXISTS elec_agent")
