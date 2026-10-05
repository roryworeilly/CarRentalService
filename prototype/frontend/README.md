# DriveAway Frontend (prototype)

CIS 453 Group 5 — car rental booking prototype.
Vite + React (JavaScript), plain CSS, React Router. No TypeScript, no Tailwind, no UI library.

## Run

```bash
npm install
npm run dev
```

The dev server runs on `http://localhost:5173` and proxies `/api/*` to the
FastAPI backend at `http://localhost:8000`. Start the backend first (see
`prototype/backend/README.md`).

## Prototype scope

Covers registration/login, viewing cars, and booking (F.R 1.x, 2.x, 3.x).
Admin screens are intentionally out of scope.

## Test cards (mock payments)

- `4242 4242 4242 4242` — succeeds (CONFIRMED)
- `4000 0000 0000 0002` — declines (FAILED_PAYMENT, 15-min hold)
