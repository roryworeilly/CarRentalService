# Tech Stack Justification (Week 3) – summary
_The full Week 3 write-up was not found on the Desktop; this is the summary kept in the CIS 453 project._

| Layer | Choice |
|---|---|
| Backend | Python + **FastAPI** |
| Frontend | **React.js**, JavaScript, HTML, CSS |
| Database | **PostgreSQL** |
| Version control | Git / GitHub (team repo, used both semesters) |
| Hosting | Amazon EC2 |
| Payments (from architecture) | Stripe |
| Email (from architecture) | SMTP / Amazon SES |
| Background jobs | scheduler / worker process |

## As built in the prototype
| Concern | Used | Notes |
|---|---|---|
| ORM | SQLAlchemy 2.x (psycopg2) | No Alembic; `db/schema.sql` is source of truth |
| Validation | Pydantic v2 (+ pydantic-settings) | Built into FastAPI |
| Password hashing | passlib + bcrypt (`bcrypt<4.1`) | NFR 4 |
| Auth tokens | JWT HS256 via python-jose | Role claim drives CUSTOMER/ADMIN gating (F.R 1.4) |
| Scheduler | APScheduler `BackgroundScheduler` | Runs hold expiry every 60s (F.R 4.4) |
| Backend tests | pytest + httpx | sqlite in-memory by default; Postgres for EXCLUDE test |
| Frontend tooling | Vite + React + React Router, plain CSS | JavaScript, no TypeScript |
| Payments | In-process mock gateway | Stripe test mode deferred; only last4 stored |
| Email | Console stub | SES/SMTP deferred |
| Dev DB | PostgreSQL 16 in Docker Compose | `prototype/docker-compose.yml` |
| Not adopted | Alembic, Vitest/RTL | Not used in prototype |

## Gaps flagged in review (open issue #6, partly closed by the table above)
The justification does not yet cover: Stripe, SES, the ORM, auth/hashing libraries, testing tools, or the scheduler.
Suggested picks for the prototype (to add to the justification if adopted):
- ORM / migrations: SQLAlchemy 2.x + Alembic
- Validation: Pydantic (built into FastAPI)
- Password hashing: passlib/bcrypt or argon2-cffi
- Auth tokens: JWT (python-jose / PyJWT)
- Scheduler: APScheduler
- Testing: pytest + httpx (backend), Vitest + React Testing Library (frontend)
- Frontend tooling: Vite, React Router
- Payments in prototype: Stripe test mode, or a mock gateway
