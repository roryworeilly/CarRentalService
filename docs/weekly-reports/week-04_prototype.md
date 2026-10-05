# Week 4 - Prototype
**Goal:** working prototype covering registration/login, viewing cars, booking.

Status legend: [x] done and exercised, [~] implemented but not verified end-to-end this week, [ ] not done.

## Done this week
- [x] Repo + project skeleton (backend, frontend, db)
- [x] DB schema + seed data (Postgres 16 via `prototype/docker-compose.yml`)
- [x] Register / login (age 21+, licence) - F.R 1.1; backend tests pass
- [x] Vehicle list + availability search (`GET /vehicles`, `GET /vehicles/{id}`, `GET /locations`)
- [x] Quote + reserve (hold) + mock payment -> CONFIRMED: exercised over the API through the Vite proxy against Postgres (quote 120.00 for 3 days, reserve 201, pay CONFIRMED). Frontend fixes (search->detail params, checkout 402 handling, My Bookings fields) are build-tested; screens not yet clicked through in a browser
- [x] Failed payment -> FAILED_PAYMENT with 15-min hold (402 + hold_expires_at), retry with a good card -> CONFIRMED, verified over the API; APScheduler expiry every 60s
- [x] Cancel / refund (verified over the API on Postgres: CANCELLED, refund row, payment REFUNDED)
- [x] Dynamic-flow (sequence) diagrams (`diagrams/dynamic-flows/`)
- [x] Admin API + UI (dashboard, fleet, categories, bookings, status override with audit entry)
- [x] Double-booking 409: confirmed on Postgres 16 (overlapping reserve returns 409; dedicated test hits the EXCLUDE constraint alone, 17 passed). Not yet run against the docker-compose DB (Docker not installed on the dev machine; same schema.sql/seed.sql used)
- [ ] Frontend automated tests
- [ ] Stripe test mode, SES email, EC2 deployment (deferred)

## Decisions made
- 15-min hold starts at **payment failure** (F.R 4.4 verbatim); open issue #1 resolved.
- Mock payment gateway in-process (card `4000000000000002` declines); Stripe deferred.
- Email is a console stub.
- Schema.sql is source of truth; no Alembic.
- Expiry via in-process APScheduler (60s interval).
- Return location = pickup location in the UI (simplification).

## Blockers / next week
- Click through the full demo path in a browser (see `docs/demo-script.md`); API path is verified, UI screens are not.
- Open issues #2-#5, #7 still open; #6 partly closed (Stripe/SES undecided).
- Expiry can lag up to 60s; single-process scheduler only.
- Capture screenshots / demo video.

## Evidence for final report
- Screenshots / demo video saved to `prototype/screenshots/` (to do)
- Demo walkthrough: `docs/demo-script.md`
- Backend tests: `cd prototype/backend && pytest -q`
