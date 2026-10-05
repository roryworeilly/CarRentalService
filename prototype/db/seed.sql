-- Seed data for Car Rental Service prototype – Group 5 (CIS 453)
-- Run AFTER schema.sql: psql -d car_rental -f schema.sql -f seed.sql
--
-- WARNING: The TRUNCATE below destroys all existing data and resets sequences.
-- Safe for the dev/demo environment only – NEVER run against production.
--
-- Demo plaintext passwords (for demo use only – never store plaintext in production):
--   admin@carrental.com  → password123
--   alice@example.com    → password123
--   bob@example.com      → password123
--
-- The bcrypt hashes below were generated for "password123" with cost factor 12.
-- In production the application layer (e.g. passlib/bcrypt) generates these.

TRUNCATE
  audit_entries,
  notifications,
  refunds,
  payments,
  bookings,
  vehicle_images,
  vehicles,
  subscriptions,
  driver_licences,
  users,
  vehicle_categories,
  locations
RESTART IDENTITY CASCADE;

-- ------------------------------------------------------------
-- Locations  (NFR 1)
-- Opens 07:00, closes 22:00 daily
-- ------------------------------------------------------------
INSERT INTO locations (code, name, address, opens_at, closes_at) VALUES
  ('JFK', 'John F. Kennedy International Airport',
   'Terminal 4, JFK Access Road, Jamaica, NY 11430',
   '07:00', '22:00'),
  ('LGA', 'LaGuardia Airport',
   'Hangar Rd, East Elmhurst, NY 11369',
   '07:00', '22:00'),
  ('EWR', 'Newark Liberty International Airport',
   '3 Brewster Rd, Newark, NJ 07114',
   '07:00', '22:00');

-- ------------------------------------------------------------
-- Vehicle categories  (F.R 2.2, F.R 3.2)
-- Cost = daily_rate × days + flat_fee, minus subscription discount (NFR 3)
-- ------------------------------------------------------------
INSERT INTO vehicle_categories (name, daily_rate, flat_fee) VALUES
  ('Economy',  35.00, 15.00),
  ('Sedan',    55.00, 20.00),
  ('SUV',      85.00, 25.00),
  ('Truck',    95.00, 30.00);

-- ------------------------------------------------------------
-- Vehicles  (F.R 2.1, F.R 5.2)
-- VINs are fictional but follow the 17-char format
-- All AVAILABLE at seed time (F.R 2.4)
-- ------------------------------------------------------------
INSERT INTO vehicles (vin, make, model, year, seats, status, category_id, home_location_id) VALUES
  -- Economy (category 1) – JFK
  ('1HGBH41JXMN109186', 'Honda',      'Fit',        2023, 5, 'AVAILABLE', 1, 1),
  ('3FADP4AJ5FM123456', 'Ford',       'Fiesta',     2022, 5, 'AVAILABLE', 1, 2),
  -- Sedan (category 2) – LGA + EWR
  ('1FAHP2E89DG234567', 'Ford',       'Fusion',     2023, 5, 'AVAILABLE', 2, 2),
  ('1G1ZD5ST4JF345678', 'Chevrolet',  'Malibu',     2024, 5, 'AVAILABLE', 2, 3),
  -- SUV (category 3) – JFK + LGA
  ('5XYKT3A10CG456789', 'Kia',        'Sorento',    2023, 7, 'AVAILABLE', 3, 1),
  ('1GNSCCKC2FR567890', 'Chevrolet',  'Suburban',   2022, 8, 'AVAILABLE', 3, 2),
  -- Truck (category 4) – EWR + JFK
  ('1FTFW1ET5DFC678901', 'Ford',      'F-150',      2024, 5, 'AVAILABLE', 4, 3),
  ('3TMMU4FN0CM789012', 'Toyota',     'Tacoma',     2023, 5, 'AVAILABLE', 4, 1);

-- ------------------------------------------------------------
-- Users  (F.R 1.1, F.R 1.4, NFR 4)
--
-- Bcrypt hash for "password123" (cost=12); generated externally with passlib:
--   from passlib.hash import bcrypt
--   bcrypt.hash("password123", rounds=12)
-- Replace with fresh hashes before any real deployment.
-- ------------------------------------------------------------
INSERT INTO users
  (id, email, password_hash, role, first_name, last_name, date_of_birth, phone, staff_id)
VALUES
  -- Admin user (F.R 1.4 – staff_id set, customer fields NULL)
  (
    'a0000000-0000-0000-0000-000000000001',
    'admin@carrental.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQyCMRd/A2gFJuBZOSMfX6cWG',
    'ADMIN',
    NULL, NULL, NULL, NULL,
    'STAFF-001'
  ),
  -- Customer: Alice  (DOB 1990-05-14 → 36 years old; eligible F.R 1.1)
  (
    'b0000000-0000-0000-0000-000000000002',
    'alice@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQyCMRd/A2gFJuBZOSMfX6cWG',
    'CUSTOMER',
    'Alice', 'Johnson', '1990-05-14', '555-0101',
    NULL
  ),
  -- Customer: Bob  (DOB 1988-11-22 → 37 years old; eligible F.R 1.1)
  (
    'c0000000-0000-0000-0000-000000000003',
    'bob@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQyCMRd/A2gFJuBZOSMfX6cWG',
    'CUSTOMER',
    'Bob', 'Martinez', '1988-11-22', '555-0202',
    NULL
  );

-- ------------------------------------------------------------
-- Driver licences  (F.R 1.1: must be valid/unexpired to book)
-- ------------------------------------------------------------
INSERT INTO driver_licences (user_id, number, issuing_state, expires_on, verified_at) VALUES
  (
    'b0000000-0000-0000-0000-000000000002',
    'AJ-4821-990514', 'NY', '2029-05-31',
    now()
  ),
  (
    'c0000000-0000-0000-0000-000000000003',
    'BM-7733-881122', 'NJ', '2029-11-30',
    now()
  );
