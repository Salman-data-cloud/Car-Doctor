from django.contrib import admin

from .models import Mechanic, Client, Appointment

@admin.register(Mechanic)
class MechanicAdmin(admin.ModelAdmin):
    list_display = ("id", "name")

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone', 'car_license', 'engine_number')

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'mechanic', 'date')
    list_filter = ('date', 'mechanic')
    search_fields = ('client__name', "client_phone", 'car_license')  
