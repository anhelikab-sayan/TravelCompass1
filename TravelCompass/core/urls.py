from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.search_view, name="index"),
    path("search/", views.search_view, name="search"),
    path('api/plan-route/', views.plan_route_api, name='plan_route_api'),
    path('api/save-route/', views.save_route_api, name='save_route_api'),
    path('api/delete-route/<int:route_id>/', views.delete_route_api, name='delete_route_api'),
]
