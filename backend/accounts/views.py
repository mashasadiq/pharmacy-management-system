from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect


class UserLoginView(LoginView):
    """Display the pharmacist/admin login page."""
    template_name = "accounts/login.html"


def user_logout(request):
    """Log out the current user and redirect to the login page."""
    logout(request)

    return redirect("login")