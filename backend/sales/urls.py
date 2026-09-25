from django.urls import path

from . import views


urlpatterns = [
    path("", views.sales_list, name="sales_list"),
    path("create/", views.create_sale_page, name="create_sale_page"),
    path("api/create/", views.create_sale, name="create_sale"),
    path("<int:sale_id>/", views.sale_detail, name="sale_detail"),
]