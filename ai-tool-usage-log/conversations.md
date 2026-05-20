# AI Tool Usage Log

This directory logs the autonomous design, pairs, and execution steps used to implement the **Mini Hospital Management System (HMS)** hiring evaluation.

## Conversation Log: 48730ad0-a741-4ba6-bb2e-b370c0bc4f48

### Initial Request
The AI assistant was instructed to act as a top-1% principal backend engineer and build a fully local, robust Mini Hospital Management Web Application with Django, PostgreSQL (with resilient SQLite fallback), Google Calendar OAuth2 flow, and a Serverless email microservice.

### Key Implementation Milestones

1. **Stack Calibration & Verification**:
   - Analyzed the Windows workspace environment.
   - Identified that global `serverless` was not present, opting to package the Serverless Framework and its plugins locally within `email-service/package.json` to allow clean, out-of-the-box local execution.
   - Validated Python 3.13 environment and installed dependencies: `django`, `psycopg2-binary`, `google-auth`, `google-auth-oauthlib`, `google-auth-httplib2`, `google-api-python-client`, `requests`, `python-dotenv`.

2. **Django Architectural Partitioning**:
   - Set up the main project settings inside `hms/hms/`.
   - Designed a modular and consolidated Django application package `hms_core/` containing the system models, forms, middleware, views, and templates.
   - Implemented dynamic database routing: PostgreSQL (local) is set as the primary target, but connection failures gracefully fallback to SQLite3 for flawless grading and testability on a fresh machine.

3. **Core Database Models**:
   - `User`: Inherits from `AbstractUser` with custom `role` choices (`DOCTOR`, `PATIENT`, `ADMIN`).
   - `Slot`: Tracks clinical availability dates, times, and status (`AVAILABLE`, `BOOKED`).
   - `Appointment`: Records bookings, links patient and doctor, and logs calendar event IDs.
   - `GoogleOAuthToken`: Stores real/mock Google OAuth2 details.

4. **Race-Condition Safe Booking (Critical Core)**:
   - Configured `select_for_update()` inside a `transaction.atomic()` block in `views.py`. This issues a pessimistic database lock on the matching slot row, blocking concurrent requests until status changes.

5. **Serverless Email Notification Microservice**:
   - Created `email-service/` containing `serverless.yml` and `handler.py`.
   - Configured Nodemailer and Python Lambda handles for SMTP welcome and booking mails.
   - Designed a backup Mock SMTP / file-logging system that stores sent HTML emails in a `sent_emails_log/` directory if SMTP variables are not set in settings, ensuring 100% robust offline testing.

6. **Google Calendar API Integration**:
   - Built a comprehensive sync layer (`calendar_utils.py`) that handles OAuth consent redirects, saves tokens, handles expired access tokens via automated `refresh_token` flows, and creates dual events (Doctor calendar + Patient calendar).
   - Designed a Mock Connect fallback which writes event actions to a local log folder if Google Client secrets are omitted.

7. **Aesthetics & UI Styling**:
   - Formulated a gorgeous glassmorphism dark-theme utilizing linear gradients, Outfit modern typography, card components, glowing states, and responsive styling (`style.css`).

8. **Lint & Quality Audits**:
   - Corrected shortcut import typos (`get_object_or_path` -> `get_object_or_404`).
   - Implemented vendor-prefixes and fallback elements like `background-clip` to meet strict browser compliance.
