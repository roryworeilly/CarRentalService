# Architecture (Week 1)
Diagram: `../diagrams/architecture.pdf`

Three-tier web application deployed on **Amazon EC2** (online 24/7 – NFR 1; scales horizontally behind a load balancer – NFR 6).

## Actors
- **Customer** – 21+, valid driver's licence
- **Admin** – role-based access (F.R 1.4)

## Client tier – React.js single-page app
Any device (NFR 2); booking completes in under 10 minutes (NFR 5).
| Area | Covers |
|---|---|
| Account pages | sign up · login · 2FA |
| Search & browse | make · category · dates |
| Booking & checkout | quote · pay · history |
| Admin dashboard | fleet · rates |

Talks to the API over **HTTPS · REST / JSON**; the session token carries the role (customer | admin).

## Application tier – Python REST API
Stateless services, one module per requirement group:
| Module | Requirements | Responsibilities |
|---|---|---|
| Auth & Accounts | F.R 1.1–1.6 | RBAC · 2FA · hashed passwords |
| Vehicle Catalog | F.R 2.1–2.4 | availability filter |
| Booking Engine | F.R 3.1–3.5 | quote · hold · status machine |
| Payments | F.R 4.1, 4.3–4.6 | charge · refund · no card stored |
| Notifications | F.R 4.2, 1.5, 1.6 | confirmations · codes · links |
| Fleet Admin | F.R 5.1–5.5 | cars · rates · overrides |

## Data tier – PostgreSQL
- users: role, licence, password hash
- vehicles: make, model, year, seats, images, category, daily rate, fleet status
- bookings: dates, location, cost, status
- transactions: gateway reference only — no card number (NFR 4)
- subscriptions: discount tier (NFR 3)

## Background worker – scheduled jobs
- Expire FAILED_PAYMENT holds at 15 min → EXPIRED, release vehicle (F.R 4.4)
- Send follow-ups near pickup window (F.R 4.2)
- Daily inventory refresh of car database (NFR 7)

## External services
- **Payment gateway** (e.g. Stripe): tokenized card · charge · refund. API sends charge/refund requests; result → status change.
- **Email service** (SMTP / Amazon SES): 2FA codes, reset links, confirmations, reminders.
- **Git repository**: version control (NFR 7); build → deploy to EC2.
