# Open Issues (from 2026-10-02 review)
Resolve these (or document the decision) before/while building the prototype.

1. **15-min hold start:** SRS F.R 4.4 starts the 15-min window on *payment failure*; diagrams/class model start it at *reservation* (`holdExpiresAt`). Pick one.
2. **UC-13 / UC-17 direction:** Cancel «extend» Refund points the wrong way — Refund should extend Cancel.
3. **Phantom docs:** diagrams reference "D03" and "DD-1" — no such documents exist yet.
4. **F.R 5.2 wording:** "add cars for sale" conflicts with scope (not acquiring cars) — likely "for rent".
5. **NFR wording:** NFR 4 merges password hashing and card storage into one sentence; NFR 3 (subscription) is functional, not non-functional.
6. **Tech stack gaps:** justification omits Stripe, SES, ORM, auth/hashing libs, testing tools, scheduler.
7. **Class diagram redundancy:** Vehicle.homeLocation duplicates "based at"; Booking.pickupLocation duplicates "picked up at"; returnLocation has no association.
8. **Dynamic-flow diagrams** (sequence / object interaction) required for Phase 2 are not yet produced.
