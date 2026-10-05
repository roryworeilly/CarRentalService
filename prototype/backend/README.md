# Car Rental Service — Backend (Prototype)

CIS 453 Group 5. FastAPI + SQLAlchemy 2.x + PostgreSQL.

The database schema lives in `prototype/db/schema.sql` (source of truth). The
app binds to those tables via SQLAlchemy ORM. Payments are handled by an
in-process `MockGateway` (no Stripe). Emails are printed to stdout.

## Setup

```bash
cd prototype/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit DATABASE_URL and JWT_SECRET
```

Apply the schema to Postgres before running:

```bash
psql -d car_rental -f ../db/schema.sql
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

Interactive docs: <http://localhost:8000/docs>

## Environment variables

| Var | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | sqlite dev DB | SQLAlchemy URL |
| `JWT_SECRET` | insecure default | HS256 signing key |
| `JWT_ALGORITHM` | HS256 | JWT alg |
| `JWT_EXPIRE_MINUTES` | 120 | token lifetime |
| `HOLD_WINDOW_MINUTES` | 15 | FAILED_PAYMENT hold window (F.R 4.4) |

## Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | public | Create customer (enforces age >=21 and non-expired licence, F.R 1.1). |
| POST | `/auth/login` | public | Email + password; returns JWT. |
| GET | `/vehicles` | public | Filter by `category`, `location_id`, `period_start`, `period_end`. Only AVAILABLE, non-overlapping (F.R 2.4). |
| POST | `/bookings/quote` | customer | Returns `{daily_rate, days, flat_fee, discount_pct, subtotal, total}` (F.R 3.1/3.2). |
| POST | `/bookings` | customer | Creates INPROGRESS booking. Snapshots the price quote. |
| POST | `/bookings/{id}/pay` | customer | Charges mock gateway. 200+CONFIRMED on success; 402 and FAILED_PAYMENT with `hold_expires_at` on failure (F.R 4.3/4.4). |
| POST | `/bookings/{id}/cancel` | customer | Cancels INPROGRESS/CONFIRMED before pickup. Refund issued if CONFIRMED (F.R 4.5). |
| GET | `/bookings` | customer | Lists caller's bookings (F.R 3.4). Admin tokens are rejected (F.R 1.4). |
| GET | `/health` | public | Liveness. |

### Mock payment gateway

`app/payments/gateway.py` — any card number succeeds EXCEPT `4000000000000002`
(the standard test "declined" card). Only `last4` is stored (NFR 4).

### Hold timer (open issue #1 — resolved)

The 15-minute hold starts on **payment failure** (F.R 4.4 verbatim).
`hold_expires_at` is set only when a booking transitions to `FAILED_PAYMENT`.

### Scheduled expiry

`app.booking.service.expire_stale_holds(db)` transitions stale
`FAILED_PAYMENT` bookings to `EXPIRED`. Not wired to a scheduler in the
prototype — call it from a cron/APScheduler worker in production.

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
