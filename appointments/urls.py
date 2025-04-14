from django.urls import path
from . import views
from .views import AdminLoginView, AdminLogoutView, LogoutView

urlpatterns = [
    path('', views.home_view, name='home'),
    path('book/', views.book_appointment, name='book_appointment'),
    path('availability/', views.check_mechanic_availability, name='check_availability'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('update/<int:appt_id>/', views.update_appointment, name='update_appointment'),
    path('login/', AdminLoginView.as_view(), name='login'),
    path('logout/', AdminLogoutView.as_view(), name='logout'),


]
