-- FinRoot database schema
-- Auto-created by DigitalTwinStore on first use.

CREATE TABLE IF NOT EXISTS digital_twins (
    user_id           TEXT PRIMARY KEY,
    name              TEXT NOT NULL,
    age               INTEGER NOT NULL,
    risk_tolerance    TEXT NOT NULL DEFAULT 'moderate',
    investment_horizon TEXT NOT NULL DEFAULT 'medium',
    monthly_income    REAL NOT NULL DEFAULT 0,
    monthly_expenses  REAL NOT NULL DEFAULT 0,
    tax_bracket_pct   REAL NOT NULL DEFAULT 0,
    goals             TEXT NOT NULL DEFAULT '[]',
    constraints       TEXT NOT NULL DEFAULT '[]',
    holdings          TEXT NOT NULL DEFAULT '[]',
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL
);
