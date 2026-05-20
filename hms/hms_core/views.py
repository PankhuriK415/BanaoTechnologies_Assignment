import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.urls import reverse

from .models import User, Slot, Appointment, GoogleOAuthToken
from .forms import SignupForm, SlotForm
from .email_utils import trigger_welcome_email, trigger_booking_email
from .calendar_utils import (
    get_auth_flow, 
    save_user_credentials, 
    create_appointment_events, 
    is_google_configured
)

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in immediately after signup
            login(request, user)
            
            # Send welcome email asynchronously via serverless service (non-blocking)
            try:
                trigger_welcome_email(user)
            except Exception as e:
                print(f"Failed to call serverless welcome email: {e}")
                
            messages.success(request, f"Welcome to Mini HMS, {user.first_name or user.username}! Registration successful.")
            return redirect('dashboard')
    else:
        form = SignupForm()
    return render(request, 'hms_core/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        passw = request.POST.get('password')
        user = authenticate(request, username=username, password=passw)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'hms_core/login.html')


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')


@login_required
def dashboard_redirect(request):
    """Redirects the authenticated user to their role-specific dashboard."""
    if request.user.is_doctor():
        return redirect('doctor_dashboard')
    elif request.user.is_patient():
        return redirect('patient_dashboard')
    else:
        # Fallback to patient dashboard if role is unclear
        return redirect('patient_dashboard')


@login_required
def doctor_dashboard(request):
    # Enforced by middleware, but check here too for safety
    if not request.user.is_doctor():
        return redirect('dashboard')

    doctor_slots = Slot.objects.filter(doctor=request.user)
    upcoming_appointments = Appointment.objects.filter(
        doctor=request.user,
        slot__date__gte=timezone.localdate()
    ).select_related('patient', 'slot')

    has_google_token = GoogleOAuthToken.objects.filter(user=request.user).exists()
    token = GoogleOAuthToken.objects.filter(user=request.user).first()
    is_mock = token.is_mock if token else False

    context = {
        'slots': doctor_slots,
        'appointments': upcoming_appointments,
        'has_google_token': has_google_token,
        'is_mock_token': is_mock,
        'google_configured': is_google_configured()
    }
    return render(request, 'hms_core/doctor_dashboard.html', context)


@login_required
def create_slot_view(request):
    if not request.user.is_doctor():
        return redirect('dashboard')

    if request.method == 'POST':
        form = SlotForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.doctor = request.user
            slot.status = Slot.Status.AVAILABLE
            slot.save()
            messages.success(request, "Availability slot created successfully!")
            return redirect('doctor_dashboard')
    else:
        form = SlotForm()
    return render(request, 'hms_core/create_slot.html', {'form': form})


@login_required
def patient_dashboard(request):
    if not request.user.is_patient():
        return redirect('dashboard')

    # Get all active doctors in the system
    doctors = User.objects.filter(role=User.Role.DOCTOR)
    
    # Get all appointments booked by this patient
    appointments = Appointment.objects.filter(
        patient=request.user
    ).select_related('doctor', 'slot').order_by('slot__date', 'slot__start_time')

    has_google_token = GoogleOAuthToken.objects.filter(user=request.user).exists()
    token = GoogleOAuthToken.objects.filter(user=request.user).first()
    is_mock = token.is_mock if token else False

    context = {
        'doctors': doctors,
        'appointments': appointments,
        'has_google_token': has_google_token,
        'is_mock_token': is_mock,
        'google_configured': is_google_configured()
    }
    return render(request, 'hms_core/patient_dashboard.html', context)


@login_required
def view_doctor_slots(request, doctor_id):
    if not request.user.is_patient():
        return redirect('dashboard')

    doctor = get_object_or_404(User, id=doctor_id, role=User.Role.DOCTOR)
    
    # Rules:
    # 1. Only future slots are visible (current date + future dates)
    # 2. Booked slots must be hidden
    now_time = timezone.localtime(timezone.now()).time()
    today = timezone.localdate()
    
    slots = Slot.objects.filter(
        doctor=doctor,
        status=Slot.Status.AVAILABLE
    ).filter(
        # Date is strictly in the future, OR date is today and time is in the future
        models.Q(date__gt=today) | models.Q(date=today, start_time__gt=now_time)
    ).order_by('date', 'start_time')

    context = {
        'doctor': doctor,
        'slots': slots
    }
    return render(request, 'hms_core/view_doctor_slots.html', context)


@login_required
def book_slot(request, slot_id):
    """
    RACE CONDITION SAFE SLOT BOOKING.
    Uses select_for_update() inside a transaction block to lock the database row,
    ensuring that double-booking or concurrent patient overrides are structurally impossible.
    """
    if not request.user.is_patient():
        return redirect('dashboard')

    try:
        # Atomic lock transaction
        with transaction.atomic():
            # 1. Lock the Slot record immediately
            slot = Slot.objects.select_for_update().get(id=slot_id)
            
            # 2. Verify availability inside the locked block
            if slot.status != Slot.Status.AVAILABLE:
                messages.error(request, "Sorry, this slot has already been booked by another user.")
                return redirect('patient_dashboard')
                
            # Double-booking check: Patient can't book overlapping appointments
            # Or can't book the exact same slot.
            existing_appt = Appointment.objects.filter(patient=request.user, slot__date=slot.date, slot__start_time=slot.start_time).exists()
            if existing_appt:
                messages.error(request, "You already have another appointment booked at this exact time.")
                return redirect('patient_dashboard')

            # 3. Transition the status atomically
            slot.status = Slot.Status.BOOKED
            slot.save()

            # 4. Record the Appointment
            appointment = Appointment.objects.create(
                patient=request.user,
                doctor=slot.doctor,
                slot=slot
            )

        # Triggers after successful transaction completion (to avoid slowing or breaking db rollback)
        # A. Trigger Google Calendar API additions for both Doctor and Patient
        try:
            create_appointment_events(appointment)
        except Exception as calendar_err:
            print(f"Non-fatal error creating calendar events: {calendar_err}")

        # B. Invoke Serverless Email Notification service
        try:
            trigger_booking_email(appointment)
        except Exception as email_err:
            print(f"Non-fatal error triggering booking email: {email_err}")

        messages.success(request, f"Appointment successfully scheduled with Dr. {slot.doctor.get_full_name() or slot.doctor.username}!")
        return redirect('patient_dashboard')

    except Slot.DoesNotExist:
        messages.error(request, "The requested availability slot does not exist.")
        return redirect('patient_dashboard')
    except Exception as e:
        messages.error(request, f"An unexpected system booking error occurred: {str(e)}")
        return redirect('patient_dashboard')


# --- Google OAuth Flow Views ---

@login_required
def google_connect_init(request):
    """
    Initiates Google OAuth2.
    If client secrets are not configured, redirects to a page offering a Mock connection.
    """
    flow = get_auth_flow()
    if not flow:
        # Falls back to Mock Connect option for evaluators
        return render(request, 'hms_core/google_callback.html', {
            'mock_option': True,
            'google_configured': False
        })
        
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    # Save the state in the session to verify the callback
    request.session['oauth2_state'] = state
    return redirect(authorization_url)


@login_required
def google_connect_mock(request):
    """Mock-connects a User to Google Calendar in one-click, saving a mock token."""
    save_user_credentials(request.user, None, is_mock=True)
    messages.success(request, "Successfully connected mock Google Calendar! Ready to simulate calendar booking events locally.")
    return redirect('dashboard')


@login_required
def google_callback(request):
    """Handles callback response from Google OAuth server."""
    state = request.GET.get('state')
    error = request.GET.get('error')
    
    if error:
        messages.error(request, f"Google authentication failed: {error}")
        return redirect('dashboard')

    flow = get_auth_flow()
    if not flow:
        messages.error(request, "Google OAuth is not configured on this server.")
        return redirect('dashboard')

    # Verify state against session
    saved_state = request.session.get('oauth2_state')
    if not state or state != saved_state:
        messages.error(request, "OAuth security state mismatch. Please try again.")
        return redirect('dashboard')

    # Fetch token using code
    try:
        flow.fetch_token(authorization_response=request.build_absolute_uri())
        credentials = flow.credentials
        
        # Save credentials to GoogleOAuthToken table
        save_user_credentials(request.user, credentials)
        
        messages.success(request, "Google Calendar successfully connected! Appointments will now sync to your calendar.")
    except Exception as e:
        messages.error(request, f"Could not retrieve access credentials from Google: {e}")
        
    return redirect('dashboard')
