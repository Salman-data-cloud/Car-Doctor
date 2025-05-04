from django.urls import path
from . import views
from .views import AdminLoginView, AdminLogoutView, UserLogoutView, UserLoginView
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('', views.home_view, name='home'),
    path('book/', views.book_appointment, name='book_appointment'),
    path('availability/', views.check_mechanic_availability, name='check_availability'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('update/<int:appt_id>/', views.update_appointment, name='update_appointment'),
    path('admin-login/', AdminLoginView.as_view(), name='admin_login'),
    path('admin-logout/', AdminLogoutView.as_view(), name='admin_logout'),
    path('register/', views.register_view, name='register'),
    path('login/', views.UserLoginView.as_view(), name='user_login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),



]
