from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.http import JsonResponse
from django.shortcuts import render


def admin_required(view_func):
    """Allow only administrators and explain denied access to other users."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())

        if request.user.role != "ADMIN":
            if request.path.startswith("/purchases/api/"):
                return JsonResponse(
                    {
                        "error": (
                            "Access denied. Only administrators "
                            "can manage purchases."
                        )
                    },
                    status=403,
                )

            return render(
                request,
                "403.html",
                status=403,
            )

        return view_func(request, *args, **kwargs)

    return wrapper