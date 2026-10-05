# 03 · Cancel & Refund
Covers UC-13 Cancel Booking, UC-17 Issue Refund (refund `extend`s cancel, correcting the arrow direction noted in open issue #2).

A Customer cancels a booking. The service branches on current status: cancelling a CONFIRMED booking issues a refund via the mock gateway (F.R 4.5); cancelling an INPROGRESS hold just releases the vehicle with no money movement. Both paths send a notification. Cancels are forbidden once status is COMPLETED or after pickup time (business rule from F.R 3.5).

```mermaid
sequenceDiagram
    actor C as Customer
    participant UI as React UI
    participant API as Booking API
    participant B as Booking (DB)
    participant P as Payment (DB)
    participant R as Refund (DB)
    participant G as MockGateway
    participant N as Notification

    C->>UI: click "Cancel" on booking
    UI->>API: POST /bookings/{id}/cancel
    API->>B: load booking

    alt status == CONFIRMED
        API->>P: find SUCCEEDED payment
        API->>G: refund(intentId, amount)
        G-->>API: REFUNDED, refundId
        API->>R: INSERT refund row
        API->>P: transitionTo(REFUNDED)
        API->>B: transitionTo(CANCELLED)
        API->>N: send(BOOKING_CANCELLED_REFUNDED)
        API-->>UI: 200 {status:CANCELLED, refundIssued:true}
    else status == INPROGRESS
        API->>B: transitionTo(CANCELLED)
        Note over B: hold released,<br/>no payment to reverse
        API->>N: send(BOOKING_CANCELLED)
        API-->>UI: 200 {status:CANCELLED, refundIssued:false}
    else status in {COMPLETED, EXPIRED, CANCELLED}
        API-->>UI: 409 {detail:"cannot cancel in this state"}
    end
```
