from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from .forms import AppointmentForm
from .models import Client, Appointment, Mechanic
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from django.contrib.auth import logout
from django.views import View


def book_appointment(request):
    mechanics = Mechanic.objects.all() 
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            address = form.cleaned_data['address']
            phone = form.cleaned_data['phone']
            car_license = form.cleaned_data['car_license']
            engine_number = form.cleaned_data['engine_number']
            appointment_date = form.cleaned_data['appointment_date']
            mechanic = form.cleaned_data['mechanic']

            existing = Appointment.objects.filter(
                client__phone=phone,
                date=appointment_date
            )
            if existing.exists():
                messages.error(request, "You already have an appointment on this date.")
            else:
                count = Appointment.objects.filter(mechanic=mechanic, date=appointment_date).count()
                if count >= 4:
                    messages.error(request, f"{mechanic.name} is fully booked on {appointment_date}.")
                else:
                    client = Client.objects.create(
                        name=name, address=address, phone=phone,
                        car_license=car_license, engine_number=engine_number
                    )
                    Appointment.objects.create(
                        client=client, mechanic=mechanic, date=appointment_date
                    )
                    messages.success(request, "Appointment booked successfully!")
                    return redirect('book_appointment')
    else:
        form = AppointmentForm()

    return render(request, 'appointments/book.html', {'form': form, 'mechanics': mechanics})

def check_mechanic_availability(request):
    mechanic_id = request.GET.get('mechanic_id')
    date_str = request.GET.get('date')
    
    if mechanic_id and date_str:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        count = Appointment.objects.filter(mechanic_id=mechanic_id, date=date_obj).count()
        available_slots = 4 - count
        return JsonResponse({'available_slots': available_slots})
    
    return JsonResponse({'error': 'Invalid data'}, status=400)

@staff_member_required
def admin_panel(request):
    appointments = Appointment.objects.select_related('client', 'mechanic').order_by('-date')
    mechanics = Mechanic.objects.all()
    return render(request, 'appointments/admin_panel.html', {
        'appointments': appointments,
        'mechanics': mechanics
    })

@staff_member_required
@csrf_exempt
def update_appointment(request, appt_id):
    if request.method == 'POST':
        new_date = request.POST.get('new_date')
        new_mechanic_id = request.POST.get('new_mechanic')
        appointment = get_object_or_404(Appointment, id=appt_id)

        if not new_date:
            return JsonResponse({'error': 'Appointment date is required.'}, status=400)

        try:
            
            new_date = datetime.strptime(new_date, "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

        exists = Appointment.objects.filter(
            client=appointment.client,
            date=new_date
        ).exclude(id=appt_id)
        if exists.exists():
            return JsonResponse({'error': 'Client already has appointment on this date.'}, status=400)
        count = Appointment.objects.filter(mechanic_id=new_mechanic_id, date=new_date).exclude(id=appt_id).count()
        if count >= 4:
            return JsonResponse({'error': 'Mechanic is fully booked on that date.'}, status=400)
        
        
        
        appointment.date = new_date
        appointment.mechanic_id = new_mechanic_id
        appointment.save()

        return redirect('admin_panel')
    
def home_view(request):
    return render(request, 'appointments/home.html')
    
class AdminLoginView(LoginView):
    template_name = 'appointments/login.html'

class AdminLogoutView(View):
    def get(self,request):
        logout(request)
        return redirect("login")