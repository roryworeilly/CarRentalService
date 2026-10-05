# 01 · Reserve and Pay (happy path)
Covers UC-10 Quote Rental Cost, UC-11 Reserve Vehicle, UC-14 Submit Payment, UC-15 Confirm Booking.

A logged-in Customer picks a vehicle and dates. The Booking service composes a `PriceQuote` snapshot (so later rate changes under F.R 5.3 can't retro-affect this booking), creates an INPROGRESS hold protected by the Postgres `EXCLUDE USING gist` constraint on `(vehicle_id, period)`, charges via the mock payment gateway, and on success transitions to CONFIRMED and emits a notification. The `alt` block shows what happens when another customer books the same window first (DB raises SQLSTATE `23P01` → HTTP 409).

```mermaid
sequenceDiagram
    actor C as Customer
    participant UI as React UI
    participant API as Booking API
    participant V as Vehicle (DB)
    participant B as Booking (DB)
    participant PQ as PriceQuote
    participant G as MockGateway
    participant N as Notification

    C->>UI: pick vehicle + dates
    UI->>API: POST /bookings/quote
    API->>V: load vehicle + category
    API->>PQ: quote(dailyRate, days, flatFee, discountPct)
    PQ-->>API: {subtotal, total}
    API-->>UI: 200 quote JSON

    C->>UI: confirm "Reserve"
    UI->>API: POST /bookings
    alt vehicle still free for period
        API->>B: INSERT booking status=INPROGRESS, snapshot PriceQuote
        B-->>API: id, reference
        API-->>UI: 201 {id, status:INPROGRESS}
    else overlapping live booking exists
        B-->>API: IntegrityError SQLSTATE 23P01
        API-->>UI: 409 {detail:"vehicle already booked"}
        UI-->>C: back to Search with notice
    end

    C->>UI: submit card (test number 4242…)
    UI->>API: POST /bookings/{id}/pay
    API->>G: charge(amount, last4, idempotencyKey)
    G-->>API: SUCCEEDED, intentId
    API->>B: transitionTo(CONFIRMED)
    API->>N: send(BOOKING_CONFIRMED)
    N-->>C: email (console-stubbed)
    API-->>UI: 200 {status:CONFIRMED}
```
