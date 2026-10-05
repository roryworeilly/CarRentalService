# Database – PostgreSQL 15+

Single-node PostgreSQL schema for the Car Rental Service prototype (CIS 453, Group 5).

## Required extensions

Both extensions must be available in your PostgreSQL installation:

| Extension | Purpose |
|---|---|
| `btree_gist` | Enables the `EXCLUDE USING gist (vehicle_id WITH =, period WITH &&)` constraint that physically prevents double-booking (F.R 3.3) |
| `pgcrypto` | Provides `gen_random_uuid()` for UUID primary keys |

On most systems these ship with PostgreSQL core. If missing, install `postgresql-contrib`.

## How to run

```bash
# 1. Create the database (run once)
createdb car_rental

# 2. Apply schema and seed data
psql -d car_rental -f schema.sql -f seed.sql
```

To reset to a clean demo state without recreating the database, re-run seed.sql alone (it `TRUNCATE … RESTART IDENTITY CASCADE`s all tables at the top):

```bash
psql -d car_rental -f seed.sql
```

## Demo credentials

All demo accounts use the password **`password123`** (bcrypt hash, cost 12).

| Role | Email | Notes |
|---|---|---|
| Admin | `admin@carrental.com` | staff_id `STAFF-001`; no customer fields (F.R 1.4) |
| Customer | `alice@example.com` | DOB 1990-05-14, NY licence, expires 2029-05-31 |
| Customer | `bob@example.com` | DOB 1988-11-22, NJ licence, expires 2029-11-30 |

Before any real deployment, regenerate all password hashes with the application's auth library (e.g. `passlib.hash.bcrypt`) — the seed hash is a known demo value.

## Schema overview

| Table | Key design decisions |
|---|---|
| `users` | Single-table inheritance for CUSTOMER / ADMIN (F.R 1.4). `CHECK customer_fields_required` enforces `first_name`, `last_name`, `date_of_birth` NOT NULL when `role = 'CUSTOMER'`. Age ≥ 21 check is enforced at the application layer (depends on booking date, F.R 1.1). |
| `bookings` | `period tstzrange` + `EXCLUDE USING gist` on live statuses blocks overlapping bookings at the DB level (F.R 3.3). The GiST index created by the EXCLUDE also serves range queries — no separate GiST index is created. `hold_expires_at` is populated **only** when status transitions to `FAILED_PAYMENT`, set to `now() + 15 minutes` by the app layer (F.R 4.4; open issue #1 locked). |
| `bookings` (quote) | `quote_*` columns snapshot the `PriceQuote` at booking time so admin rate changes (F.R 5.3) never alter existing bookings. Cost formula: `daily_rate × days + flat_fee − discount` (F.R 3.2, NFR 3). |
| `vehicles` | `updated_at` maintained by trigger. `idx_vehicles_status_category` composite index covers the primary search filter (F.R 2.4). |
| `payments` | Only `card_last4` and gateway IDs stored — never card numbers (NFR 4). |

## Files

```
prototype/db/
  schema.sql   -- DDL: types, tables, indexes, triggers, constraints
  seed.sql     -- Demo data: 3 locations, 4 categories, 8 vehicles, 3 users
  README.md    -- This file
```
