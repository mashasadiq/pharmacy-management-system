from django.urls import path

from . import views


urlpatterns = [
    path("", views.inventory_list, name="inventory_list"),
    path("search/", views.search_drugs, name="search_drugs"),
    path("drug/<int:drug_id>/", views.drug_detail, name="drug_detail"),
    path("low-stock/", views.low_stock_drugs, name="low_stock"),
    path("expired/", views.expired_drugs, name="expired_drugs"),
    path("check-stock/<int:drug_id>/", views.check_stock_availability, name="check_stock"),
    path("create/", views.create_drug, name="create_drug"),
]