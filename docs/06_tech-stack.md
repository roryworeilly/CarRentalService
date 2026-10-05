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

## Gaps flagged in review (open issue #6)
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
