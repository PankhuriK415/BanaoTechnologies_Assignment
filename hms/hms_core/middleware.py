from django.shortcuts import redirect
from django.contrib import messages

class RoleRequiredMiddleware:
    """
    Middleware to enforce role-based access control at the request level.
    Redirects unauthorized users away from role-specific paths.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            path = request.path_info
            
            # Enforce Doctor-only pages
            if path.startswith('/doctor/') and not request.user.is_doctor():
                messages.error(request, "Access denied: This section is restricted to Doctors.")
                return redirect('dashboard')
            
            # Enforce Patient-only pages
            if path.startswith('/patient/') and not request.user.is_patient():
                messages.error(request, "Access denied: This section is restricted to Patients.")
                return redirect('dashboard')
                
        return self.get_response(request)
