-- PostgreSQL 15+ schema for Car Rental Service – Group 5 (CIS 453)
-- Derived from docs/05_domain-design.md and docs/02_requirements-SRS.md
-- Run: psql -d car_rental -f schema.sql

-- ------------------------------------------------------------
-- Extensions
-- ------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS btree_gist;   -- required for EXCLUDE with uuid "=" (no double booking)
CREATE EXTENSION IF NOT EXISTS pgcrypto;     -- gen_random_uuid(), crypt()

-- ------------------------------------------------------------
-- Enum types
-- ------------------------------------------------------------
CREATE TYPE role           AS ENUM ('CUSTOMER', 'ADMIN');
CREATE TYPE vehicle_status AS ENUM ('AVAILABLE', 'RENTED', 'IN_MAINTENANCE', 'RETIRED');
-- BookingStatus lifecycle: INPROGRESS → CONFIRMED → COMPLETED
--                          INPROGRESS → FAILED_PAYMENT → EXPIRED
--                          INPROGRESS | CONFIRMED → CANCELLED  (F.R 3.5, F.R 4.4)
CREATE TYPE booking_status AS ENUM ('INPROGRESS', 'CONFIRMED', 'FAILED_PAYMENT', 'EXPIRED', 'CANCELLED', 'COMPLETED');
CREATE TYPE payment_status AS ENUM ('PENDING', 'SUCCEEDED', 'FAILED', 'REFUNDED');
CREATE TYPE sub_tier       AS ENUM ('NONE', 'STANDARD', 'PREMIUM');

-- ------------------------------------------------------------
-- Users (single-table inheritance: CUSTOMER + ADMIN)  F.R 1.4
-- ------------------------------------------------------------
CREATE TABLE users (
  id             uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  email          text        NOT NULL UNIQUE,
  password_hash  text        NOT NULL,                       -- NFR 4: bcrypt/argon2 hash only, never plaintext
  role           role        NOT NULL DEFAULT 'CUSTOMER',
  mfa_enabled    boolean     NOT NULL DEFAULT false,         -- F.R 1.6
  created_at     timestamptz NOT NULL DEFAULT now(),

  -- Customer fields (NULL for ADMIN rows)
  first_name     text,
  last_name      text,
  date_of_birth  date,
  phone          text,

  -- Administrator field (NULL for CUSTOMER rows)
  staff_id       text,

  -- Enforce NOT NULL on customer-specific fields when role = CUSTOMER (F.R 1.1)
  -- Age ≥21 check depends on booking date, so it is enforced in the application layer (F.R 1.1)
  CONSTRAINT customer_fields_required CHECK (
    role <> 'CUSTOMER'
    OR (first_name IS NOT NULL AND last_name IS NOT NULL AND date_of_birth IS NOT NULL)
  )
);

-- ------------------------------------------------------------
-- Driver licences  (F.R 1.1: must hold a valid, unexpired licence to book)
-- ------------------------------------------------------------
CREATE TABLE driver_licences (
  user_id        uuid  PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  number         text  NOT NULL,
  issuing_state  text  NOT NULL,
  expires_on     date  NOT NULL,
  verified_at    timestamptz
);

-- Index to speed licence validity checks during booking eligibility (F.R 1.1)
CREATE INDEX idx_driver_licences_expires ON driver_licences (expires_on);

-- ------------------------------------------------------------
-- Subscriptions  (NFR 3: discount applied at quote time)
-- ------------------------------------------------------------
CREATE TABLE subscriptions (
  user_id      uuid           PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  tier         sub_tier       NOT NULL DEFAULT 'NONE',
  discount_pct numeric(5,2)   NOT NULL DEFAULT 0,
  starts_on    date           NOT NULL,
  ends_on      date
);

-- ------------------------------------------------------------
-- Locations  (NFR 1: pickup only when location is open)
-- ------------------------------------------------------------
CREATE TABLE locations (
  id         serial PRIMARY KEY,
  code       text   NOT NULL UNIQUE,
  name       text   NOT NULL,
  address    text   NOT NULL,
  opens_at   time   NOT NULL,
  closes_at  time   NOT NULL
);

-- ------------------------------------------------------------
-- Vehicle categories  (F.R 2.2, F.R 3.2)
-- ------------------------------------------------------------
CREATE TABLE vehicle_categories (
  id          serial         PRIMARY KEY,
  name        text           NOT NULL UNIQUE,        -- Economy, Sedan, SUV, Truck
  daily_rate  numeric(10,2)  NOT NULL,
  flat_fee    numeric(10,2)  NOT NULL
);

-- ------------------------------------------------------------
-- Vehicles  (F.R 2.1, F.R 2.4, F.R 5.1)
-- ------------------------------------------------------------
CREATE TABLE vehicles (
  id               uuid           PRIMARY KEY DEFAULT gen_random_uuid(),
  vin              text           NOT NULL UNIQUE,   -- 17-char VIN
  make             text           NOT NULL,
  model            text           NOT NULL,
  year             int            NOT NULL,
  seats            int            NOT NULL,
  status           vehicle_status NOT NULL DEFAULT 'AVAILABLE',
  category_id      int            NOT NULL REFERENCES vehicle_categories(id),
  home_location_id int            NOT NULL REFERENCES locations(id),
  updated_at       timestamptz    NOT NULL DEFAULT now()
);

-- F.R 2.4: search filters on status + category; composite covers both equality predicates
CREATE INDEX idx_vehicles_status_category ON vehicles (status, category_id);

-- FK index (always index foreign keys)
CREATE INDEX idx_vehicles_category    ON vehicles (category_id);
CREATE INDEX idx_vehicles_location    ON vehicles (home_location_id);

-- ------------------------------------------------------------
-- Trigger: keep vehicles.updated_at current
-- ------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_vehicles_updated_at
  BEFORE UPDATE ON vehicles
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ------------------------------------------------------------
-- Vehicle images  (F.R 2.1)
-- ------------------------------------------------------------
CREATE TABLE vehicle_images (
  id          serial PRIMARY KEY,
  vehicle_id  uuid   NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
  url         text   NOT NULL,
  sort_order  int    NOT NULL DEFAULT 0
);

CREATE INDEX idx_vehicle_images_vehicle ON vehicle_images (vehicle_id);

-- ------------------------------------------------------------
-- Bookings  (F.R 3.1 – F.R 4.6)
-- ------------------------------------------------------------
CREATE TABLE bookings (
  id                  uuid           PRIMARY KEY DEFAULT gen_random_uuid(),
  reference           text           NOT NULL UNIQUE,
  customer_id         uuid           NOT NULL REFERENCES users(id),
  vehicle_id          uuid           NOT NULL REFERENCES vehicles(id),
  status              booking_status NOT NULL DEFAULT 'INPROGRESS',
  period              tstzrange      NOT NULL,
  pickup_location_id  int            NOT NULL REFERENCES locations(id),
  return_location_id  int            NOT NULL REFERENCES locations(id),

  -- Open issue #1 LOCKED: hold_expires_at is set ONLY when status transitions to
  -- FAILED_PAYMENT; the app layer sets it to now() + INTERVAL '15 minutes'.
  -- It is NULL for all other statuses.  (F.R 4.4)
  hold_expires_at     timestamptz,

  created_at          timestamptz    NOT NULL DEFAULT now(),
  updated_at          timestamptz    NOT NULL DEFAULT now(),

  -- PriceQuote snapshot – composition; rate changes (F.R 5.3) never alter existing bookings
  -- Cost = daily_rate × days + flat_fee, minus discount  (F.R 3.2, NFR 3)
  quote_daily_rate    numeric(10,2)  NOT NULL,
  quote_days          int            NOT NULL,
  quote_flat_fee      numeric(10,2)  NOT NULL,
  quote_discount_pct  numeric(5,2)   NOT NULL DEFAULT 0,
  quote_subtotal      numeric(10,2)  NOT NULL,
  quote_total         numeric(10,2)  NOT NULL,

  -- No double booking: overlapping live bookings on the same vehicle are physically impossible.
  -- EXPIRED/CANCELLED/COMPLETED are excluded from the constraint so they don't block future bookings.
  -- The GiST index created by this EXCLUDE also serves range queries – no separate gist index needed.
  -- (F.R 3.3, F.R 2.4)
  CONSTRAINT no_overlap EXCLUDE USING gist (vehicle_id WITH =, period WITH &&)
    WHERE (status IN ('INPROGRESS', 'CONFIRMED', 'FAILED_PAYMENT'))
);

-- Composite index for customer booking history queries (F.R 3.4)
CREATE INDEX idx_bookings_customer_status ON bookings (customer_id, status);

-- FK indexes
CREATE INDEX idx_bookings_vehicle         ON bookings (vehicle_id);
CREATE INDEX idx_bookings_pickup_location ON bookings (pickup_location_id);
CREATE INDEX idx_bookings_return_location ON bookings (return_location_id);

-- Index to support background job querying for expired FAILED_PAYMENT holds (F.R 4.4)
CREATE INDEX idx_bookings_hold_expires ON bookings (hold_expires_at)
  WHERE status = 'FAILED_PAYMENT';

-- Trigger: keep bookings.updated_at current
CREATE TRIGGER trg_bookings_updated_at
  BEFORE UPDATE ON bookings
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ------------------------------------------------------------
-- Payments  (F.R 4.1 – F.R 4.3; NFR 4: no card numbers stored)
-- ------------------------------------------------------------
CREATE TABLE payments (
  id                 uuid           PRIMARY KEY DEFAULT gen_random_uuid(),
  booking_id         uuid           NOT NULL REFERENCES bookings(id),
  gateway_intent_id  text,                                   -- Stripe PaymentIntent id
  idempotency_key    text           NOT NULL UNIQUE,
  amount             numeric(10,2)  NOT NULL,
  status             payment_status NOT NULL DEFAULT 'PENDING',
  card_last4         char(4),                                -- NFR 4: last 4 digits only
  attempted_at       timestamptz    NOT NULL DEFAULT now()
);

CREATE INDEX idx_payments_booking ON payments (booking_id);

-- ------------------------------------------------------------
-- Refunds  (F.R 4.5: only for CONFIRMED bookings)
-- ------------------------------------------------------------
CREATE TABLE refunds (
  payment_id  uuid           PRIMARY KEY REFERENCES payments(id),
  amount      numeric(10,2)  NOT NULL,
  reason      text,
  issued_at   timestamptz    NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------
-- Notifications  (F.R 4.2)
-- ------------------------------------------------------------
CREATE TABLE notifications (
  id               serial      PRIMARY KEY,
  booking_id       uuid        REFERENCES bookings(id),
  channel          text        NOT NULL DEFAULT 'EMAIL',
  template         text        NOT NULL,
  sent_at          timestamptz,
  delivery_status  text
);

CREATE INDEX idx_notifications_booking ON notifications (booking_id);

-- ------------------------------------------------------------
-- Audit log
-- ------------------------------------------------------------
CREATE TABLE audit_entries (
  id      serial      PRIMARY KEY,
  actor   uuid        REFERENCES users(id),
  action  text        NOT NULL,
  before  jsonb,
  after   jsonb,
  at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_entries_actor ON audit_entries (actor);
CREATE INDEX idx_audit_entries_at    ON audit_entries (at);
