# DriveAway Frontend (prototype)

CIS 453 Group 5 — car rental booking prototype.
Vite + React (JavaScript), plain CSS, React Router. No TypeScript, no Tailwind, no UI library.

## Run

Prerequisites: Postgres via `docker compose up -d` in `prototype/`, and the
backend running (`uvicorn app.main:app --reload --port 8000` in `prototype/backend`).

```bash
npm install
npm run dev
```

The dev server runs on `http://localhost:5173` and proxies `/api/*` to the
FastAPI backend at `http://localhost:8000`.

## Prototype scope

Customer: registration/login, search, vehicle detail + quote, reserve,
checkout (mock payment, 15-min retry countdown), My Bookings (cancel).
Admin (role ADMIN only): `/admin` dashboard, `/admin/fleet`,
`/admin/categories`, `/admin/bookings` (with status override).

## Demo credentials

Password for all: `password123`

- Admin: `admin@carrental.com`
- Customers: `alice@example.com`, `bob@example.com`

## Test cards (mock payments)

- `4242 4242 4242 4242` - succeeds (CONFIRMED)
- `4000 0000 0000 0002` - declines (HTTP 402, FAILED_PAYMENT, 15-min hold)
- Any other number also succeeds.
