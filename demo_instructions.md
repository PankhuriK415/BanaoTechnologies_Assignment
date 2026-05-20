# Video Demo Recording Instructions

Use this guide to record and prepare your hiring evaluation submission video. This walkthrough is structured to demonstrate every technical requirement of the Mini Hospital Management System (HMS).

---

## ⏱️ Video Structure & Script (Total: 6–8 minutes)

### Part 1: Environment & Architecture Walkthrough (1.5 Mins)
1. **Show Workspace Structure**:
   - Open your IDE and present the root folder. Point out the standard repository structure: `hms/` (Django engine), `email-service/` (Serverless handler), and `requirements.txt`.
2. **Present Active Running Terminals**:
   - **Terminal 1 (Django)**: Show the server running via `python manage.py runserver`. Point out the startup warning in the log showing the database fallback connecting smoothly:
   - **Terminal 2 (Serverless/Simulator)**: Show either `python local_server.py` or `npx serverless offline` running inside the `email-service` directory on `http://localhost:3000`.

---

### Part 2: Doctor Onboarding & Slot Creation (1.5 Mins)
1. **Doctor Registration**:
   - Open your browser to [http://localhost:8000/signup/](http://localhost:8000/signup/).
   - Sign up a new user (e.g., `doctor_smith`). Complete all fields, select the role **Doctor**, and click **Create Account**.
2. **Google Calendar Connection**:
   - Point out the **Mock Integration mode** on the dashboard. Click **Mock Connect Google Calendar**.
   - Show the state update: the indicator turns to a vibrant green dot displaying `CONNECTED (MOCK MODE)`.
3. **Availability Publishing**:
   - Click **Add Availability** or navigate to `/doctor/slots/create/`.
   - Set a future date (e.g., tomorrow) and hours (e.g., `10:00 AM` to `11:00 AM`).
   - Click **Publish Slot**.
   - Show the slot instantly populating on the Doctor Dashboard as `AVAILABLE`.

---

### Part 3: Patient Onboarding & Atomic Booking (2 Mins)
1. **Patient Registration**:
   - Log out, click Sign Up again, and register a patient (e.g., `patient_doe`). Select role **Patient** and submit.
   - Show the Patient Dashboard displaying the available Specialist (Dr. Smith).
2. **Google Calendar Connect**:
   - Click **Mock Connect Google Calendar** on the patient's dashboard to link their account as well.
3. **Slot Reservation**:
   - Click **Book Appointment** next to Dr. Smith.
   - Show the available slots grid. Point out that the slot we created is visible because it is in the future.
   - Click **Confirm Booking**.
   - Show the success alert: *"Appointment successfully scheduled with Dr. Smith!"*.
   - Point out that the slot is now hidden from the availability grid.

---

### Part 4: Verification of Integrations (2 Mins)
1. **Verify Email Triggers**:
   - Open the IDE. Show the directory `email-service/sent_emails_log/`.
   - Open and render the generated `.html` log files:
     - `SIGNUP_WELCOME` file: Verify the greeting and user role.
     - `BOOKING_CONFIRMATION` file: Verify the booking details (Patient Name, Doctor Name, Date, and Time).
2. **Verify Google Calendar Synchronization**:
   - Show the directory `google_calendar_log/`.
   - Open `DOCTOR_doctor_smith_calendar.txt` and `PATIENT_patient_doe_calendar.txt`.
   - Point out the logged JSON events showing that the events were created on both calendars with correct summaries, descriptions, and time bounds.
3. **Show Console HTTP Outputs**:
   - Present the terminal stdout history showing Django triggering HTTP POST calls to `http://localhost:3000/dev/email/send` returning status `200 OK`.

---

### Part 5: Code & Design Walkthrough (1.5 Mins)
1. **Explain the Concurrency Trade-Off**:
   - Explain how **Pessimistic Locking** using `.select_for_update()` inside `views.py` completely blocks double-booking.
   - Open `hms/hms_core/views.py` around line `182` showing the `book_slot` implementation.
   - Highlight the `transaction.atomic()` context and explain that this row lock guarantees strict consistency under high-contention patient loads.
2. **Show Serverless decoupling**:
   - Briefly present `email-service/handler.py` to highlight how the serverless service parses triggers separately from Django.
