from django.urls import path

from .views import UserLoginView, user_logout


urlpatterns = [
    path(
        "login/",
        UserLoginView.as_view(),
        name="login",
    ),

    path(
        "logout/",
        user_logout,
        name="logout",
    ),
]