# 04 · Search Availability by Date & Location
Covers UC-7 Browse Vehicles, UC-9 Search Availability by Date & Location, F.R 2.3 / F.R 2.4.

Customer submits a pickup/return window plus optional location and category filters. The Catalog service returns only vehicles whose fleet status is AVAILABLE **and** which have no overlapping live booking for the requested period. The overlap check uses the Postgres `tstzrange` operator `&&` against the same column protected by the no-double-booking EXCLUDE constraint, so searches and bookings see a consistent definition of "available."

```mermaid
sequenceDiagram
    actor C as Customer
    participant UI as React UI
    participant API as Catalog API
    participant V as Vehicle (DB)
    participant B as Booking (DB)

    C->>UI: enter dates + location + category
    UI->>API: GET /vehicles?period_start=&period_end=&location_id=&category=

    API->>V: SELECT * FROM vehicles<br/>WHERE status='AVAILABLE'<br/>AND (location_id = ? OR ? IS NULL)<br/>AND (category_id = ? OR ? IS NULL)
    V-->>API: candidate vehicles

    loop for each candidate
        API->>B: EXISTS SELECT 1 FROM bookings<br/>WHERE vehicle_id = v.id<br/>AND status IN ('INPROGRESS','CONFIRMED','FAILED_PAYMENT')<br/>AND period && tstzrange(?, ?)
        B-->>API: overlap? true/false
    end

    API-->>UI: 200 [filtered vehicles with daily_rate, flat_fee, images]
    UI-->>C: render results grid
```
