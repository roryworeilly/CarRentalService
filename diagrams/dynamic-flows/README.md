# Dynamic-Flow Diagrams (Phase 2)
Object-interaction / sequence diagrams, one per core flow. Mermaid renders on GitHub and in VS Code (Markdown Preview Mermaid extension).

| File | Flow | Use cases |
|---|---|---|
| [01_reserve-and-pay.md](01_reserve-and-pay.md) | Quote → reserve (INPROGRESS hold) → pay → CONFIRMED | UC-10, UC-11, UC-14, UC-15 |
| [02_failed-payment-and-expire.md](02_failed-payment-and-expire.md) | Payment declined → FAILED_PAYMENT → 15-min scheduler expiry (with retry alt) | UC-14, UC-16 |
| [03_cancel-and-refund.md](03_cancel-and-refund.md) | Cancel booking; refund only from CONFIRMED | UC-13, UC-17 |
| [04_search-availability.md](04_search-availability.md) | Availability search by date + location (status + non-overlapping check) | UC-7, UC-9 |

Starter file `seq-reserve-and-pay.mmd` from Week 2 is superseded by `01_reserve-and-pay.md`.

**Locked decision (open issue #1):** the 15-min hold timer starts at **payment failure**, not at reservation — per F.R 4.4 verbatim.
