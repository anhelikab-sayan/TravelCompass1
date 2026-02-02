from django.urls import path
from .views import (
    login_view,
    register_view,
    profile_view,
    logout_view,
    confirm_email_view
)

urlpatterns = [
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('profile/', profile_view, name='profile'),
    path('logout/', logout_view, name='logout'),
    path('confirm/<str:token>/', confirm_email_view, name='confirm_email'),
]