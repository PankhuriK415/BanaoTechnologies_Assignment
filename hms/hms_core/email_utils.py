import requests
import json
from django.conf import settings

def send_notification_email(trigger, recipient_email, data):
    """
    Invokes the local serverless email microservice via an HTTP POST request.
    Handles service unavailability gracefully to prevent main system crashes.
    """
    payload = {
        "trigger": trigger,
        "email": recipient_email,
        "data": data
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    url = settings.EMAIL_SERVICE_URL
    print(f"[Email Client] Invoking Email Service at {url} for trigger '{trigger}'...")
    
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=3)
        if response.status_code == 200:
            print(f"[Email Client] Success: Notification email triggered successfully via Serverless offline!")
            return True
        else:
            print(f"[Email Client] Failed with status code {response.status_code}: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[Email Client] WARNING: Could not connect to Serverless Email Service ({e}).")
        print("[Email Client] Note: Make sure 'serverless offline' is running inside the 'email-service' folder.")
        print("[Email Client] HMS Django app will continue running smoothly (graceful microservice fallback).")
        return False

def trigger_welcome_email(user):
    """Triggers the SIGNUP_WELCOME email upon successful user registration."""
    if not user.email:
        print(f"[Email Client] User {user.username} has no email address. Skipping welcome notification.")
        return False
        
    data = {
        "name": user.get_full_name() or user.username,
        "role": user.role
    }
    return send_notification_email("SIGNUP_WELCOME", user.email, data)

def trigger_booking_email(appointment):
    """Triggers the BOOKING_CONFIRMATION email upon booking an appointment."""
    patient = appointment.patient
    doctor = appointment.doctor
    slot = appointment.slot

    if not patient.email:
        print(f"[Email Client] Patient {patient.username} has no email address. Skipping booking notification.")
        return False

    data = {
        "patient_name": patient.get_full_name() or patient.username,
        "doctor_name": doctor.get_full_name() or doctor.username,
        "date": str(slot.date),
        "start_time": slot.start_time.strftime("%I:%M %p"),
        "end_time": slot.end_time.strftime("%I:%M %p")
    }
    return send_notification_email("BOOKING_CONFIRMATION", patient.email, data)
