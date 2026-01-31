from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.search_view, name="index"),
    path("search/", views.search_view, name="search"),
]
