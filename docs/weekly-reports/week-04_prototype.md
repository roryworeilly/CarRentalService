# Week 4 - Prototype
**Goal:** working prototype covering registration/login, viewing cars, booking.

Status legend: [x] done and exercised, [~] implemented but not verified end-to-end this week, [ ] not done.

## Done this week
- [x] Repo + project skeleton (backend, frontend, db)
- [x] DB schema + seed data (Postgres 16 via `prototype/docker-compose.yml`)
- [x] Register / login (age 21+, licence) - F.R 1.1; backend tests pass
- [x] Vehicle list + availability search (`GET /vehicles`, `GET /vehicles/{id}`, `GET /locations`)
- [~] Quote + reserve (hold) + mock payment -> CONFIRMED (backend tested; frontend flow being fixed for demo: search->detail params, checkout 402 handling, My Bookings fields)
- [x] Failed payment -> FAILED_PAYMENT with 15-min hold; APScheduler expiry every 60s (backend)
- [x] Cancel / refund (backend)
- [x] Dynamic-flow (sequence) diagrams (`diagrams/dynamic-flows/`)
- [x] Admin API + UI (dashboard, fleet, categories, bookings, status override with audit entry)
- [~] Double-booking 409: backed by Postgres EXCLUDE constraint; the test only runs against Postgres and has not been re-confirmed against the Compose DB this week
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
- Confirm full demo path end-to-end in a browser against Postgres (see `docs/demo-script.md`); not all steps verified yet.
- Open issues #2-#5, #7 still open; #6 partly closed (Stripe/SES undecided).
- Expiry can lag up to 60s; single-process scheduler only.
- Capture screenshots / demo video.

## Evidence for final report
- Screenshots / demo video saved to `prototype/screenshots/` (to do)
- Demo walkthrough: `docs/demo-script.md`
- Backend tests: `cd prototype/backend && pytest -q`
