# 02 · Failed Payment & 15-min Expiry
Covers UC-14 Submit Payment (failure branch), UC-16 Expire Unpaid Hold.

When the mock gateway declines (test card `4000 0000 0000 0002`), the booking transitions INPROGRESS → FAILED_PAYMENT and `holdExpiresAt` is set to `now() + 15 min` — this is the moment the clock starts (locked per F.R 4.4). The Scheduler sweeps periodically; any FAILED_PAYMENT booking past its deadline flips to EXPIRED, releasing the vehicle (the EXCLUDE constraint only applies to live statuses, so EXPIRED frees the slot). The `alt` block shows the Customer retrying with a valid card before the deadline and recovering to CONFIRMED.

```mermaid
sequenceDiagram
    actor C as Customer
    participant UI as React UI
    participant API as Booking API
    participant B as Booking (DB)
    participant G as MockGateway
    participant S as Scheduler
    participant N as Notification

    C->>UI: submit card 4000…0002
    UI->>API: POST /bookings/{id}/pay
    API->>G: charge(...)
    G-->>API: FAILED (card declined)
    API->>B: transitionTo(FAILED_PAYMENT), holdExpiresAt = now()+15min
    API->>N: send(PAYMENT_FAILED)
    API-->>UI: 402 {booking_status:FAILED_PAYMENT, hold_expires_at}
    UI-->>C: show countdown + retry

    alt Customer retries before deadline with valid card
        C->>UI: resubmit card 4242…
        UI->>API: POST /bookings/{id}/pay
        API->>G: charge(...)
        G-->>API: SUCCEEDED
        API->>B: transitionTo(CONFIRMED), clear holdExpiresAt
        API->>N: send(BOOKING_CONFIRMED)
        API-->>UI: 200 {status:CONFIRMED}
    else deadline passes with no successful payment
        loop every minute
            S->>B: SELECT WHERE status=FAILED_PAYMENT AND hold_expires_at < now()
            B-->>S: expired holds
            S->>B: transitionTo(EXPIRED) for each
            S->>N: send(HOLD_EXPIRED)
        end
        Note over B: vehicle period now free<br/>(EXCLUDE ignores EXPIRED)
    end
```
