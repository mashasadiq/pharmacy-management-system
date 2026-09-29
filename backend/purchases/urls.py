from django.urls import path

from . import views


urlpatterns = [
    path("", views.purchase_list, name="purchase_list"),
    path("create/", views.create_purchase_page, name="create_purchase_page",),
    path("api/create/", views.create_purchase, name="create_purchase",),
    path("<int:purchase_id>/", views.purchase_detail, name="purchase_detail",),
]