from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class User(AbstractUser):
    class Role(models.TextChoices):
        DOCTOR = 'DOCTOR', 'Doctor'
        PATIENT = 'PATIENT', 'Patient'
        ADMIN = 'ADMIN', 'Admin'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.PATIENT
    )

    def is_doctor(self):
        return self.role == self.Role.DOCTOR

    def is_patient(self):
        return self.role == self.Role.PATIENT


class GoogleOAuthToken(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='google_token')
    token = models.TextField(null=True, blank=True)
    refresh_token = models.TextField(null=True, blank=True)
    token_uri = models.CharField(max_length=255, null=True, blank=True)
    client_id = models.CharField(max_length=255, null=True, blank=True)
    client_secret = models.CharField(max_length=255, null=True, blank=True)
    scopes = models.JSONField(null=True, blank=True)
    expiry = models.DateTimeField(null=True, blank=True)
    
    # Track mock connected status for local development fallback if user clicks mock connect!
    is_mock = models.BooleanField(default=False)

    def __str__(self):
        return f"GoogleOAuthToken for {self.user.username} ({'Mock' if self.is_mock else 'Real'})"


class Slot(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = 'AVAILABLE', 'Available'
        BOOKED = 'BOOKED', 'Booked'

    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='slots',
        limit_choices_to={'role': User.Role.DOCTOR}
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE
    )

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"Slot: Dr. {self.doctor.get_full_name() or self.doctor.username} on {self.date} ({self.start_time} - {self.end_time}) - {self.status}"


class Appointment(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointments_as_patient',
        limit_choices_to={'role': User.Role.PATIENT}
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointments_as_doctor',
        limit_choices_to={'role': User.Role.DOCTOR}
    )
    slot = models.OneToOneField(
        Slot,
        on_delete=models.CASCADE,
        related_name='appointment'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Store calendar event IDs in case we want to fetch, edit, or delete them
    doctor_calendar_event_id = models.CharField(max_length=255, blank=True, null=True)
    patient_calendar_event_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        patient_name = self.patient.get_full_name() or self.patient.username
        doctor_name = self.doctor.get_full_name() or self.doctor.username
        return f"Appointment: {patient_name} with Dr. {doctor_name} on {self.slot.date}"
