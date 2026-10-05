# Use Cases (Week 2)
Diagrams: `../diagrams/use-case-customer.png`, `../diagrams/use-case-admin.png`

**Actors:** Customer, Administrator, Scheduler, Payment Gateway, Email Service.

| UC | Name | Package | Primary actor | Relationships | Prototype? |
|---|---|---|---|---|---|
| UC-1 | Create Account | 1 Account Mgmt | Customer | «include» UC-6 | ✅ required |
| UC-2 | Log In / Log Out | 1 | Customer | «include» UC-5 | ✅ required |
| UC-3 | Manage Profile | 1 | Customer | | |
| UC-4 | Reset Password | 1 | Customer | | |
| UC-5 | Verify Second Factor | 1 | — | | optional |
| UC-6 | Validate Age & Licence | 1 | — | | ✅ required |
| UC-7 | Browse Vehicles | 2 Search | Customer | | ✅ required |
| UC-8 | Filter by Category | 2 | Customer | | nice-to-have |
| UC-9 | Search Availability by Date & Location | 2 | Customer | «extend» UC-7 (as drawn) | ✅ needed for booking |
| UC-10 | Quote Rental Cost | 3 Booking | — | | ✅ required |
| UC-11 | Reserve Vehicle (place hold) | 3 | Customer | «include» UC-10, UC-6 | ✅ required |
| UC-12 | View My Bookings | 3 | Customer | | nice-to-have |
| UC-13 | Cancel Booking | 3 | Customer | drawn «extend» → UC-17 (should be UC-17 extends UC-13) | |
| UC-14 | Submit Payment | 4 Payment & Notif. | Customer | «include» UC-15; ↔ Payment Gateway | stub/mock |
| UC-15 | Confirm Booking | 4 | — | «include» UC-18 | ✅ |
| UC-16 | Expire Unpaid Hold | Automated | Scheduler | «include» UC-18 | |
| UC-17 | Issue Refund | 4 / Automated | — | ↔ Payment Gateway | |
| UC-18 | Send Notification | 4 / Automated | — | ↔ Email Service | stub (log to console) |
| UC-19 | Manage Fleet & Vehicle Status | 5 Admin | Administrator | | |
| UC-20 | Manage Categories & Rates | 5 | Administrator | | |
| UC-21 | Search / Override Bookings | 5 | Administrator | «extend» UC-17 (as drawn) | |
| UC-22 | View Fleet Dashboard | 5 | Administrator | | |
| UC-23 | Complete Return | 5 | Administrator | «include» UC-18 | |
| UC-24 | Send Pickup Reminder | Automated | Scheduler | «include» UC-18 | |
| UC-25 | Refresh Inventory (daily) | Automated | Scheduler | | |

UC numbers are unique (UC-16–18 appear on both diagrams; they are shared, not duplicated).
The "Prototype?" column is a suggestion mapped to the assignment's prototype minimum (registration/login, viewing cars, booking).
