-- Optional sample data for live demos.
-- Run with:  psql "$DATABASE_URL" -f scripts/seed_data.sql

INSERT INTO customers (email, name) VALUES
  ('alice@contoso.com', 'Alice Borg'),
  ('bob@contoso.com',   'Bob Camilleri')
ON CONFLICT (email) DO NOTHING;

INSERT INTO tickets (customer_id, subject, status, priority, summary)
SELECT id, 'Cannot log in to portal', 'open', 'high',
       'User reports 401 errors after password reset.'
FROM customers WHERE email = 'alice@contoso.com'
ON CONFLICT DO NOTHING;
