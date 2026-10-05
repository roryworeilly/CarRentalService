# 5-Minute Demo Script

Status: the booking, payment, retry, cancel, 409 and admin steps were verified over the API against Postgres; the browser screens have not been clicked through, so rehearse once before presenting. Steps marked (unverified) were not run in a browser.

## Setup (before the demo)
```bash
cd prototype && docker compose up -d                         # Postgres + schema + seed
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
cd ../frontend && npm run dev                                # http://localhost:5173
```
Reset state if needed: `docker compose down -v && docker compose up -d`.

Credentials (password `password123` for all): customer `alice@example.com`, customer `bob@example.com`, admin `admin@carrental.com`.
Test cards: `4242 4242 4242 4242` succeeds; `4000 0000 0000 0002` declines.

## Script
1. **Register (0:00)** - Go to /register, create a new customer. Show the live warnings: DOB under 21 or expired licence is rejected (F.R 1.1). Then register validly (or just log in as alice).
2. **Search (0:45)** - /search: pick dates, location (JFK/LGA/EWR), category. Only AVAILABLE, non-overlapping cars appear (F.R 2.4).
3. **Quote (1:15)** - Open a car. Show quote: dailyRate x days + flat fee - discount (F.R 3.2).
4. **Reserve + pay success (1:45)** - Reserve (booking INPROGRESS), checkout with `4242...` -> CONFIRMED. Open My Bookings.
5. **Failed payment + countdown (2:30)** - Reserve another car (different dates), pay with `4000 0000 0000 0002`. Backend returns 402, booking FAILED_PAYMENT, mm:ss countdown starts (hold starts at failure, F.R 4.4). Retry with `4242...` to recover (unverified). Optionally let it lapse: scheduler expires it within ~60s after the deadline (EXPIRED).
6. **Cancel / refund (3:15)** - In My Bookings cancel the CONFIRMED booking; refund is issued via the mock gateway (F.R 4.5). Cancelling a non-CONFIRMED booking issues no refund.
7. **Double booking 409 (3:45)** - Log in as bob, try to reserve the same car for overlapping dates already CONFIRMED by alice (use the URL with the same params). Expect a 409 and redirect to Search with a notice. Enforced by the Postgres EXCLUDE constraint (unverified in browser against Compose DB).
8. **Admin (4:15)** - Log out, log in as admin. /admin dashboard (fleet counts, revenue, upcoming pickups). /admin/bookings: find alice's booking and use Override status with a reason (writes an audit entry). /admin/categories: change a rate and note existing bookings keep their snapshotted quote. Show that admin can't use customer pages and customers get 403 on /admin (F.R 1.4).

## Fallbacks
- If the UI misbehaves, use the interactive API docs at http://localhost:8000/docs.
- Run `pytest -q` in `prototype/backend` to show automated coverage.
