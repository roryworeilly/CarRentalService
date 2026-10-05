# Car Rental Service — Backend (Prototype)

CIS 453 Group 5. FastAPI + SQLAlchemy 2.x + PostgreSQL.

The database schema lives in `prototype/db/schema.sql` (source of truth). The
app binds to those tables via SQLAlchemy ORM. Payments are handled by an
in-process `MockGateway` (no Stripe). Emails are printed to stdout.

## Setup

Start Postgres 16 (schema.sql and seed.sql are auto-applied on first boot):

```bash
cd prototype
docker compose up -d
```

Then the backend:

```bash
cd prototype/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# .env already points DATABASE_URL at the docker-compose Postgres; see .env.example
```

To reset demo data: `docker compose down -v && docker compose up -d` (or re-run `db/seed.sql`). See `prototype/db/README.md`.

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

Interactive docs: <http://localhost:8000/docs>. Then start the frontend (`npm run dev` in `prototype/frontend`).

## Demo credentials

All seeded accounts use password `password123`:

| Role | Email |
|---|---|
| Admin | `admin@carrental.com` |
| Customer | `alice@example.com` |
| Customer | `bob@example.com` |

## Environment variables

| Var | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | sqlite dev DB (fallback only; `.env` sets Postgres) | SQLAlchemy URL |
| `JWT_SECRET` | insecure default | HS256 signing key |
| `JWT_ALGORITHM` | HS256 | JWT alg |
| `JWT_EXPIRE_MINUTES` | 120 | token lifetime |
| `HOLD_WINDOW_MINUTES` | 15 | FAILED_PAYMENT hold window (F.R 4.4) |

## Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | public | Create customer (enforces age >=21 and non-expired licence, F.R 1.1). |
| POST | `/auth/login` | public | Email + password; returns `{access_token, token_type, role, user_id}`. |
| GET | `/vehicles` | public | Filter by `category`, `location_id`, `period_start`, `period_end`. Only AVAILABLE, non-overlapping (F.R 2.4). |
| GET | `/vehicles/{id}` | public | Single vehicle (same shape as search result). 404 if unknown. |
| GET | `/locations` | public | List pickup/return locations. |
| POST | `/bookings/quote` | customer | Returns `{daily_rate, days, flat_fee, discount_pct, subtotal, total}` (F.R 3.1/3.2). |
| POST | `/bookings` | customer | Creates INPROGRESS booking. Snapshots the price quote. Overlap -> 409. |
| POST | `/bookings/{id}/pay` | customer | Charges mock gateway. 200+CONFIRMED on success; 402 and FAILED_PAYMENT with `hold_expires_at` on failure (F.R 4.3/4.4). |
| POST | `/bookings/{id}/cancel` | customer | Cancels INPROGRESS/CONFIRMED before pickup. Refund issued if CONFIRMED (F.R 4.5). |
| GET | `/bookings` | customer | Lists caller's bookings (F.R 3.4). Admin tokens are rejected (F.R 1.4). |
| GET | `/admin/dashboard` | admin | Fleet counts, bookings by status, upcoming pickups (7d), revenue (30d). |
| GET | `/admin/vehicles` | admin | List fleet. |
| POST | `/admin/vehicles` | admin | Add vehicle. |
| PATCH | `/admin/vehicles/{id}` | admin | Edit vehicle / change status. |
| GET | `/admin/categories` | admin | List categories and rates. |
| POST | `/admin/categories` | admin | Create category. |
| PATCH | `/admin/categories/{id}` | admin | Edit rate/fee (does not alter existing quote snapshots, F.R 3.2/5.3). |
| GET | `/admin/bookings` | admin | Search by `status`, `customer_email`, `vehicle_id`, `from`, `to`. |
| POST | `/admin/bookings/{id}/override-status` | admin | Force a status change; requires reason; writes an `audit_entries` row. |
| GET | `/health` | public | Liveness. |

All `/admin/*` routes require role ADMIN; customers get 403 (F.R 1.4).

### Mock payment gateway

`app/payments/gateway.py` — any card number succeeds EXCEPT `4000000000000002`
(the standard test "declined" card). Only `last4` is stored (NFR 4).

### Hold timer (open issue #1 — resolved)

The 15-minute hold starts on **payment failure** (F.R 4.4 verbatim).
`hold_expires_at` is set only when a booking transitions to `FAILED_PAYMENT`.

### Scheduled expiry

An APScheduler `BackgroundScheduler` started in the FastAPI lifespan
(`app/main.py`) runs `expire_stale_holds` every 60 seconds, moving stale
`FAILED_PAYMENT` bookings to `EXPIRED` (F.R 4.4). Expiry can therefore lag the
15-minute deadline by up to 60s.

## Testing

```bash
pytest -q
```

Tests run against sqlite in-memory by default. The Postgres `EXCLUDE USING
gist` double-booking constraint cannot be exercised on sqlite, so that specific
test is `skipif`-gated. To exercise it, apply `schema.sql` to a Postgres DB and
run:

```bash
TEST_DATABASE_URL=postgresql+psycopg2://user:pw@localhost/car_rental_test pytest -q
```
