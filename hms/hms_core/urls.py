from django.urls import path
from . import views

urlpatterns = [
    # Auth routing
    path('', views.login_view, name='root'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard routing
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/slots/create/', views.create_slot_view, name='create_slot_view'),
    path('patient/dashboard/', views.patient_dashboard, name='patient_dashboard'),
    
    # Patient actions
    path('patient/doctors/<int:doctor_id>/slots/', views.view_doctor_slots, name='view_doctor_slots'),
    path('patient/slots/<int:slot_id>/book/', views.book_slot, name='book_slot'),
    
    # Google Calendar integrations
    path('google-calendar/connect/', views.google_connect_init, name='google_connect_init'),
    path('google-calendar/connect/mock/', views.google_connect_mock, name='google_connect_mock'),
    path('google-calendar/callback/', views.google_callback, name='google_callback'),
]
