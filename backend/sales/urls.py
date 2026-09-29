from django.urls import path

from . import views


urlpatterns = [
    path("", views.sales_list, name="sales_list"),
    path("create/", views.create_sale_page, name="create_sale_page"),
    path("api/create/", views.create_sale, name="create_sale"),
    path("<int:sale_id>/", views.sale_detail, name="sale_detail"),
    path("<int:sale_id>/complete/", views.complete_sale_view,  name="complete_sale",),
    path("<int:sale_id>/cancel/", views.cancel_sale_view, name="cancel_sale",),
    path("<int:sale_id>/edit/", views.edit_pending_sale, name="edit_pending_sale",),
    path("<int:sale_id>/delete/", views.delete_pending_sale, name="delete_pending_sale",
),
    
]