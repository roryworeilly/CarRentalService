# Domain Design – Class Model (Week 2)
Diagram: `../diagrams/domain-class.png` (generated with Claude, PlantUML style)

## Classes
**User** (abstract) — id: UUID · email: string «unique» · passwordHash · role: Role · mfaEnabled: bool · createdAt
  ops: `authenticate(pw): bool`, `hasRole(r): bool`
- **Customer** extends User — firstName · lastName · dateOfBirth: date · phone — ops: `age(): int`, `isEligible(on: date): bool`
- **Administrator** extends User — staffId

**DriverLicence** — number · issuingState · expiresOn: date · verifiedAt — `isValid(on: date)`
**Subscription** — tier: SubTier · discountPct: decimal · startsOn · endsOn — `isActive(on: date)`
**AuditEntry** — actor: UUID · action · before: jsonb · after: jsonb · at

**Vehicle** — id · vin «unique» · make · model · year · seats · status: VehicleStatus · homeLocation: Location — `isBookable(): bool`
**VehicleCategory** — name · dailyRate: Money · flatFee: Money
**VehicleImage** — url · sortOrder
**Location** — code · name · address · opensAt: time · closesAt: time

**Booking** — id · reference «unique» · status: BookingStatus · period: TsTzRange · pickupLocation · returnLocation · holdExpiresAt · createdAt
  ops: `quote(): PriceQuote`, `transitionTo(s)`, `isHoldLive(now): bool`
**PriceQuote** (composed in Booking, snapshot) — dailyRate · days · flatFee · discountPct · subtotal · total — `recalc()`
  _Stored as a snapshot so that a later rate change (F.R 5.3) never alters the price of an existing booking._
**Payment** — id · gatewayIntentId · idempotencyKey «unique» · amount · status: PaymentStatus · cardLast4 · attemptedAt
**Refund** — amount · reason · issuedAt
**Notification** — channel: Channel · template · sentAt · deliveryStatus

## Associations / multiplicities
- Customer 1 — 0..* Booking (places)
- Customer 1 — 0..1 DriverLicence (holds)
- Customer 1 — 0..1 Subscription (has)
- User 1 — 0..* AuditEntry (generates)
- Vehicle * — 1 VehicleCategory (classified as)
- Vehicle 1 — 0..* VehicleImage (shown by)
- Vehicle * — 1 Location (based at)
- Vehicle 1 — 0..* Booking (reserved by)
- Booking * — 1 Location (picked up at)
- Booking 1 ◆— 1 PriceQuote (snapshot, composition)
- Booking 1 — 0..* Payment (paid by)
- Booking 1 — 0..* Notification (notifies)
- Payment 1 — 0..1 Refund (reversed by)

## Enums
- **Role:** CUSTOMER, ADMIN
- **VehicleStatus:** AVAILABLE, RENTED, IN_MAINTENANCE, RETIRED
- **BookingStatus:** INPROGRESS, CONFIRMED, FAILED_PAYMENT, EXPIRED, CANCELLED, COMPLETED
- **PaymentStatus:** PENDING, SUCCEEDED, FAILED, REFUNDED
- **SubTier:** NONE, STANDARD, PREMIUM
- **Channel:** EMAIL

## Key rules
- Customer must be **21+ with a valid licence** to book.
- **Cost = dailyRate × days + flatFee**, minus subscription discount (NFR 3). PriceQuote snapshotted at booking.
- **Booking lifecycle:** INPROGRESS → CONFIRMED → COMPLETED; INPROGRESS → FAILED_PAYMENT (15-min window) → EXPIRED; CANCELLED before pickup. Refund only for CONFIRMED.
- **No double booking:** `period` is a PostgreSQL `tstzrange`; an `EXCLUDE` constraint over `(vehicle_id WITH =, period WITH &&)` makes an overlapping live booking physically impossible.

## Booking state machine
```
            pay ok                return
INPROGRESS ────────► CONFIRMED ────────► COMPLETED
    │  pay fail          │ cancel (+refund)
    ▼                    ▼
FAILED_PAYMENT       CANCELLED
    │ 15 min, unpaid     ▲
    ▼                    │ cancel before pay
 EXPIRED          (INPROGRESS)
```
