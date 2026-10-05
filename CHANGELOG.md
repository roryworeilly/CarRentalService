# Changelog
All notable changes to the CIS 453 Group 5 Car Rental Service prototype are logged here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); dates in `YYYY-MM-DD`.
Reference F.R / NFR / UC ids where relevant.

## [Unreleased]

### Added
- **Backend (`prototype/backend/app/admin/`)** — admin API surface (F.R 5.1–5.5)
  - `GET /admin/dashboard` — fleet counts, bookings-by-status, upcoming pickups (7d), revenue (30d).
  - `GET|POST /admin/vehicles`, `PATCH /admin/vehicles/{id}` — fleet CRUD, status transitions.
  - `GET|POST /admin/categories`, `PATCH /admin/categories/{id}` — category + rate management; rate edits do NOT alter snapshotted PriceQuotes on existing bookings (F.R 3.2 / 5.3).
  - `GET /admin/bookings?status=&customer_email=&vehicle_id=&from=&to=` — admin booking search (UC-21).
  - `POST /admin/bookings/{id}/override-status` — force-transition booking status, writes `audit_entries` row.
  - All endpoints gated by `require_role('ADMIN')`; non-admin → 403.
  - `tests/test_admin.py` — 15 passing; verifies RBAC gate, dashboard math, rate-change snapshot immutability, audit row written on override.
  - Surgical additions to `app/main.py` (router include), `app/schemas.py` (admin schemas appended), `tests/conftest.py` (`make_admin()` helper + `AuditEntry` import).
  - `AuditEntry` ORM class lives in `admin/service.py` (not `models.py`) to honor the "don't touch existing models" scope rule.

- **Frontend (`prototype/frontend/src/pages/admin/`)** — admin UI (UC-19 to UC-23)
  - `Dashboard.jsx` — tiles for fleet counts, bookings-by-status table, revenue (30d), upcoming pickups (7d).
  - `Fleet.jsx` — vehicle table with inline status dropdown (PATCH on change); "Add vehicle" form (VIN, make, model, year, seats, category + location selects).
  - `Categories.jsx` — inline edit of `daily_rate` / `flat_fee`; persistent notice reminding admin that rate edits don't affect existing bookings.
  - `Bookings.jsx` — filter form + results table + "Override status" modal (requires reason).
  - `components/AdminRoute.jsx` — role gate; redirects non-admins to `/search?notice=...`, anonymous to `/login`.
  - Surgical additions to `App.jsx` (4 routes under `<AdminRoute>`), `NavBar.jsx` (admin-only dropdown; hides "My Bookings" for admins), `api.js` (adds `patch` helper), `styles.css` (appended `/* --- admin --- */` block).

- **Frontend (`src/components/VehicleCard.jsx`)** — vehicle imagery
  - Per-category Unsplash fallback (Economy / Sedan / SUV / Truck) when backend returns no image URL.
  - Hard-fallback to `placehold.co` labelled tile on image load error.
  - Reads `category_name`/`daily_rate` or `category`/`dailyRate` so cards render correctly from either backend endpoint shape.

### Fixed
- **Frontend (`src/auth.jsx`)** — token/user shape mismatch
  - `login()` and `register()` were reading `data.token` + `data.user` from the API response, but `TokenOut` returns `{access_token, token_type, role, user_id}`. Result: `user` was `undefined`, admin pages were unreachable because `AdminRoute` couldn't see `user.role`.
  - Now reads `data.access_token` and constructs `user = {id: data.user_id, role: data.role, email}` (email from the credentials/payload). Admin gating works end-to-end.


  - Per-category Unsplash fallback (`Economy` / `Sedan` / `SUV` / `Truck`) when the backend returns no `image_url` / `imageUrl`.
  - Hard-fallback to `placehold.co` on image load error, so a dead Unsplash link still renders a labelled tile.
  - Reads either `category_name` + `daily_rate` (current snake_case backend) or `category` + `dailyRate` (legacy), so the card renders correctly regardless of the search endpoint's casing.

- **Database (`prototype/db/`)**
  - `seed.sql`: 3 locations (JFK/LGA/EWR), 4 vehicle categories (Economy/Sedan/SUV/Truck), 8 vehicles, 1 admin + 2 customer users with bcrypt-hashed `password123`, 2 driver licence rows (expire 2029). Idempotent via `TRUNCATE ... RESTART IDENTITY CASCADE`.
  - `schema.sql`: `updated_at` columns + shared `set_updated_at()` trigger on `vehicles` and `bookings`; `customer_fields_required` CHECK constraint on `users`; FK indexes across all FK columns; partial index on `hold_expires_at WHERE status = 'FAILED_PAYMENT'`; column comment locking the hold-timer semantics (open issue #1).
  - `README.md`: run instructions, demo credentials, extension requirements (`btree_gist`, `pgcrypto`).

- **Backend (`prototype/backend/`)** — FastAPI scaffold (F.R 1.x–4.x)
  - App layout: `app/{main,config,db,models,schemas,security,deps}.py` plus `auth/`, `catalog/`, `booking/`, `payments/` modules.
  - Auth: `POST /auth/register` (enforces ≥21 and unexpired licence — F.R 1.1) and `POST /auth/login`; bcrypt via passlib, JWT via python-jose.
  - Catalog: `GET /vehicles?category=&location_id=&period_start=&period_end=` filters AVAILABLE + non-overlapping (F.R 2.3, 2.4).
  - Booking: `/bookings/quote`, `POST /bookings` (INPROGRESS hold, snapshots PriceQuote per F.R 3.2 / 5.3), `/bookings/{id}/pay`, `/bookings/{id}/cancel`, `GET /bookings`; plus `expire_stale_holds` helper for F.R 4.4.
  - Payments: in-process `MockGateway` — card `4000000000000002` declines; everything else succeeds. Only `last4` is retained (NFR 4).
  - Global `IntegrityError` handler translates Postgres SQLSTATE `23P01` (EXCLUDE violation) → HTTP 409.
  - Payment failure returns **HTTP 402** with `{message, booking_status:"FAILED_PAYMENT", hold_expires_at}`; hold timer starts here (F.R 4.4).
  - `/bookings` endpoints require role CUSTOMER (F.R 1.4).
  - Tests: `tests/{conftest,test_auth,test_booking}.py` — 9 passing, 1 Postgres-only EXCLUDE test skipped on sqlite by design.
  - `requirements.txt`, `.env.example`, `pytest.ini`, overwritten `README.md`.

- **Frontend (`prototype/frontend/`)** — Vite + React (JS, no TypeScript, no Tailwind)
  - Pages: `Login`, `Register` (live age-21 + licence-expiry warnings; server is source of truth), `Search` (date/location/category filters), `VehicleDetail` (calls `/bookings/quote`), `Checkout` (prefills `4242…`, hint for decline card, live mm:ss countdown on `FAILED_PAYMENT`, retry disabled at zero), `MyBookings`, `NotFound`.
  - Components: `NavBar`, `VehicleCard`, `ProtectedRoute`.
  - `api.js` wrapper attaches Bearer token and exposes `ApiError.status` for 409 handling; 409 on reservation routes back to Search with a yellow notice banner and preserves query params.
  - `vite.config.js` proxies `/api` → `localhost:8000`.
  - `AuthContext` + `useAuth` hook; token in `localStorage`.
  - Return location = pickup location in the prototype UI (simplification).

- **Diagrams (`diagrams/dynamic-flows/`)** — Phase 2 dynamic-flow requirement
  - `01_reserve-and-pay.md` — UC-10/11/14/15, includes 409 alt branch.
  - `02_failed-payment-and-expire.md` — UC-14/16, retry-before-deadline alt + Scheduler loop.
  - `03_cancel-and-refund.md` — UC-13/17, branches on CONFIRMED (refund via MockGateway) vs INPROGRESS vs forbidden states.
  - `04_search-availability.md` — UC-7/9, availability query showing EXCLUDE-consistent overlap check.
  - `README.md` — index table and note that `seq-reserve-and-pay.mmd` is superseded by `01_reserve-and-pay.md`.

- **Project-level**
  - `CHANGELOG.md` (this file).

### Decided (locked)
- **Hold timer** (open issue #1 in `docs/07_open-issues.md`): starts on **payment failure**, per F.R 4.4 verbatim. `hold_expires_at` is populated only at the FAILED_PAYMENT transition, cleared on recovery.
- **Payment path**: in-process `MockGateway` for the prototype — no Stripe, no real card handling, no API keys.
- **Email path**: console-stubbed `Notification` service — no SMTP/SES in prototype.
- **Scope**: no admin UI, no scheduler process wiring, no Alembic migrations (schema.sql is source of truth).

### Known limitations
- `expire_stale_holds` exists as a function but is not run on a schedule in the prototype.
- Backend ORM uses `period_start` / `period_end` columns for sqlite test portability; the real `period tstzrange` + EXCLUDE constraint remains the production guarantee against double bookings.
- Frontend has no `GET /vehicles/{id}` call (uses the list endpoint + client-side filter); no `/locations` endpoint (hardcoded list).
- Admin endpoints (F.R 5.x) and 2FA (F.R 1.6) are out of prototype scope.

---

## Change-log conventions

- Each merged change goes under a new dated `## [YYYY-MM-DD]` section (promote from `[Unreleased]` on release).
- Group entries by `Added` / `Changed` / `Fixed` / `Removed` / `Decided` / `Known limitations`.
- Prefix bullets with the touched area in bold (e.g. **Backend (booking)**).
- Reference F.R / NFR / UC ids where applicable so entries map back to `docs/02_requirements-SRS.md` and `docs/03_use-cases.md`.
- When this repo moves under `git`, record the commit SHA in parentheses at the end of each entry, e.g. `(a1b2c3d)`.
