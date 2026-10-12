from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.views.decorators.http import require_POST


class UserLoginView(LoginView):
    """Display the login page."""
    template_name = "accounts/login.html"


@require_POST
def user_logout(request):
    """Log out the current user and redirect to login."""
    logout(request)
    return redirect("login")