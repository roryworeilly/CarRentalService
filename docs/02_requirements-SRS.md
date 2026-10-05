# Software Requirements Specification – Group 5
_Source: SRSDocument-Group5.pdf (Week 1). Requirement text copied verbatim._

## Project scope
This software will facilitate online bookings for rental cars. It will handle payment, client information, authorization, car database, check-in/checkout transactions, transaction information, and client notifications. It will not handle acquiring new cars.

Initial plan: 1 Account Managing · 2 Search Features · 3 Booking/Booking Information · 4 Payment/Notifications · 5 Admin Features.
Stack: PostgreSQL, Python + React.js, Amazon EC2, Git.

## Functional requirements

### 1. Account
- **F.R 1.1:** Account Creation. (Provide valid driver's license to continue any bookings, must be over 21)
- **F.R 1.2:** Login / Logout Page.
- **F.R 1.3:** Account Manager Page.
- **F.R 1.4:** Role-Based Access separating Customer from Admin; customers cannot reach admin functions
- **F.R 1.5:** Password Reset functionality through email.
- **F.R 1.6:** Two-Factor Authentication through email to add a layer of protection for the user

### 2. Car Search Features
- **F.R 2.1:** Browse Vehicle by Make, Model, Year, Seats, Images
- **F.R 2.2:** Browse by category (e.g. Sedan, SUV, Truck, etc.)
- **F.R 2.3:** Search for pickup and return date based off of location.
- **F.R 2.4:** Allow for only vehicles that are not currently reserved to be available.

### 3. Booking / Booking Information
- **F.R 3.1:** Vehicle Selection and quoting prior to booking.
- **F.R 3.2:** Calculate Total Cost as daily rate x days rented, with an additional flat rate on top.
- **F.R 3.3:** Once a booking is selected, send to the INPROGRESS stage so that it can be removed from the site. This will help with duplicate bookings on the same vehicle.
- **F.R 3.4:** Page to view all current and past bookings.
- **F.R 3.5:** Booking Cancellation prior to pick up. Set booking to CANCELLED and release hold on vehicle.

### 4. Payment and Notifications
- **F.R 4.1:** Payment Submission to gateway for INPROGRESS bookings.
- **F.R 4.2:** Email Confirmations for booking as well as follow-ups near booking timeframe.
- **F.R 4.3:** Move booking status from INPROGRESS -> CONFIRMED once payment has been processed.
- **F.R 4.4:** On a failed payment hold status to FAILED_PAYMENT and give a 15min window for payment completion. If payment is not completed by 15min mark set as EXPIRED and release the hold on the car. If the vehicle has since been taken, the customer is returned to search
- **F.R 4.5:** Refund policy for after successful transaction and the customer wants to cancel their booking only for CONFIRMED bookings.
- **F.R 4.6:** Once the car has returned Set booking status to COMPLETED and release hold on car.

### 5. Admin Privileges
- **F.R 5.1:** Allow Admin to Create, read and update bookings according to the status of the fleet. (Available, Rented, In Maintenance, and Retired)
- **F.R 5.2:** Add new cars onto the lot for sale. _(see open issue #4 – likely "for rent")_
- **F.R 5.3:** Manage Cars by Category and adjust rates as needed.
- **F.R 5.4:** The ability to search over all bookings and override status/booking process if needed.
- **F.R 5.5:** Dashboard showing the entire fleet including Available, Rented, In Maintenance, and Retired Cars.

## Non-functional requirements
- **NFR 1 – Availability:** online all hours; pickup only when the physical location is open.
- **NFR 2 – Portability:** bookings on any device (phone, computer, tablet), web or app.
- **NFR 3 – Customer Subscription:** customers receive discounts while booking.
- **NFR 4 – Security:** secure user info, payment info, passwords and software. Passwords stored as crypt hashes; no card numbers persisted in the application database.
- **NFR 5 – Ease of Use:** clean UI, straightforward UX; transaction completable within 10 minutes (excluding search).
- **NFR 6 – Scalability:** handle a large number of concurrent users.
- **NFR 7 – Maintainability:** developers can update software as needed; daily refreshes to car database based on inventory updates.
