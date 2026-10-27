-- Cartera sintética de ACME en SQLite. src/agents/servers/credits.py crea data/acme_credits.db con este archivo.
CREATE TABLE credits (
    customer TEXT NOT NULL,
    code TEXT NOT NULL,
    product TEXT NOT NULL,
    balance INTEGER NOT NULL CHECK (balance >= 0),
    installment INTEGER NOT NULL CHECK (installment >= 0),
    overdue_installments INTEGER NOT NULL CHECK (overdue_installments >= 0),
    days_past_due INTEGER NOT NULL CHECK (days_past_due >= 0),
    PRIMARY KEY (customer, code)
);
INSERT INTO credits (customer, code, product, balance, installment, overdue_installments, days_past_due) VALUES
 ('C-1042', 'CLI', 'Crédito Libre Inversión', 8450000, 412000, 2, 45),
 ('C-1042', 'CEX', 'Crédito Express', 600000, 150000, 0, 0),
 ('C-2210', 'CEX', 'Crédito Express', 1200000, 215000, 0, 0),
 ('C-3307', 'CLI', 'Crédito Libre Inversión', 15300000, 690000, 3, 75),
 ('C-4415', 'CLI', 'Crédito Libre Inversión', 22000000, 980000, 1, 12);
