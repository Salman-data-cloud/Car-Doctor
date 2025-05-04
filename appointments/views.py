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
from django.contrib.auth import logout, authenticate, login
from django.views import View
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.urls import reverse
import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
import hmac
import hashlib
from django.urls import reverse_lazy

@login_required
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
                    encryptor = Encryptor()
                    encrypted_name = encryptor.encrypt(name)
                    encrypted_address = encryptor.encrypt(address)
                    encrypted_phone = encryptor.encrypt(phone)
                    encrypted_car_license = encryptor.encrypt(car_license)
                    encrypted_engine_number = encryptor.encrypt(engine_number)

                    mac = encryptor.create_mac(f'{name}{address}{phone}{car_license}{engine_number}', encryptor.key)


                    client = Client.objects.create(
                        name=encrypted_name.decode(), address=encrypted_address.decode(), phone=encrypted_phone.decode(),
                        car_license=encrypted_car_license.decode(), engine_number=encrypted_engine_number.decode(), integrity_mac=mac, user = request.user
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

    encryptor = Encryptor()
    decrypted_appointments = []
    for appointment in appointments:
        try:
            decrypted_name = encryptor.decrypt(appointment.client.name.encode())
            decrypted_address = encryptor.decrypt(appointment.client.address.encode())
            decrypted_phone = encryptor.decrypt(appointment.client.phone.encode())
            decrypted_car_license = encryptor.decrypt(appointment.client.car_license.encode())
            decrypted_engine_number = encryptor.decrypt(appointment.client.engine_number.encode())

            appointment.client.decrypted_name = decrypted_name
            appointment.client.decrypted_address = decrypted_address
            appointment.client.decrypted_phone = decrypted_phone
            appointment.client.decrypted_car_license = decrypted_car_license
            appointment.client.decrypted_engine_number = decrypted_engine_number

            if hasattr(appointment.client, 'integrity_mac') and appointment.client.integrity_mac:
                mac = encryptor.create_mac(f'{decrypted_name}{decrypted_address}{decrypted_phone}{decrypted_car_license}{decrypted_engine_number}', encryptor.key)
                if not encryptor.verify_mac(f'{decrypted_name}{decrypted_address}{decrypted_phone}{decrypted_car_license}{decrypted_engine_number}', appointment.client.integrity_mac, encryptor.key):
                    messages.warning(request, "Data integrity check failed for client: {appointment.id}")
                    
            appointment.client.decrypted_name = decrypted_name
            appointment.client.decrypted_address = decrypted_address
            appointment.client.decrypted_phone = decrypted_phone
            appointment.client.decrypted_car_license = decrypted_car_license
            appointment.client.decrypted_engine_number = decrypted_engine_number
            decrypted_appointments.append(appointment)
        except Exception as e:
            appointment.client.decrypted_name = 'Encrypted data'
            appointment.client.decrypted_address = 'Encrypted data'
            appointment.client.decrypted_phone = 'Encrypted data'
            appointment.client.decrypted_car_license = 'Encrypted data'
            appointment.client.decrypted_engine_number = 'Encrypted data'
            appointment.decryption_failed = True
            decrypted_appointments.append(appointment)
            messages.error(request, f"Error decrypting data for appointment {appointment.id}: {str(e)}")
            
    
    return render(request, 'appointments/admin_panel.html', {
        'appointments': decrypted_appointments,
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
        
        mechanic = get_object_or_404(Mechanic, id=new_mechanic_id)
        count = Appointment.objects.filter(mechanic_id=new_mechanic_id, date=new_date).exclude(id=appt_id).count()
        if count >= 4:
            return JsonResponse({'error': 'Mechanic is fully booked on that date.'}, status=400)
        
    
        
        appointment.date = new_date
        appointment.mechanic_id = new_mechanic_id
        appointment.save()

        return redirect('admin_panel')
    return JsonResponse({'error': 'POST method required'}, status=405)

    
def home_view(request):
    return render(request, 'appointments/home.html')
    
class AdminLoginView(LoginView):
    template_name = 'appointments/login.html'
    def get_success_url(self):
        return reverse ('admin_panel')

class AdminLogoutView(View):
    def get(self,request):
        logout(request)
        messages.info(request, "You have been logged out.")
        return redirect('home')
    
class KeyManager:
    @staticmethod
    def generate_key():
        "Generate a new encryption key."
        return Fernet.generate_key()
    
    @staticmethod

    def get_key():
        "Get the encryption key from the settings or generate a new one."
        key_path = os.path.join(settings.BASE_DIR, 'key.key')
        if os.path.exists(key_path):
            with open(key_path, 'rb') as key_file:
                return key_file.read()
        else:
            key = KeyManager.generate_key()
            with open(key_path, 'wb') as key_file:
                key_file.write(key)
            return key
    
    @staticmethod

    def derive_key_from_password(password, salt = None):
        "Derive a key from a password using PBKDF2."
        if salt is None:
            salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
class Encryptor:
    def __init__(self):
        self.key = KeyManager.get_key()
        self.fernet = Fernet(self.key)

    def encrypt(self, data):
        "Encrypt the data."
        if isinstance(data, str):
            data = data.encode()
        encrypted_data = self.fernet.encrypt(data)
        return encrypted_data
    
    def decrypt(self, encrypted_data):
        "Decrypt the data."
        decrypted_data = self.fernet.decrypt(encrypted_data)
        return decrypted_data.decode()
    
    @staticmethod
    def create_mac(data, key):
        "Create a MAC for data integrity."

        h = hmac.new(key, data.encode() if isinstance(data, str) else data, hashlib.sha256)

        return h.hexdigest()
    
    @staticmethod
    def verify_mac(data, mac, key):
        "Verify the MAC."
        h = hmac.new(key, data.encode() if isinstance(data, str) else data, hashlib.sha256)
        calculated_mac = h.hexdigest()
        return hmac.compare_digest(calculated_mac, mac)
    
def check_credentials(username, password):

    user = authenticate(username= username, password=password)
    return user

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            encryptor = Encryptor()
            user = form.save(commit=False)
            user.username = encryptor.encrypt(form.cleaned_data['username']).decode()
            
            user.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('home')
        else:
            messages.error(request, "Registration failed. Please correct the errors below.")

    else:
            form = UserCreationForm()
    return render(request, 'appointments/register.html', {'form': form})
        


class UserLoginView(LoginView):
    template_name = 'appointments/user_login.html'
    authentication_form = AuthenticationForm

    def form_valid(self, form):
        login(self.request, form.get_user())
        return super().form_valid(form)
    
    def get_success_url(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_staff:
                return reverse('admin_panel')
            else:
                return reverse('book_appointment')
        else:
            messages.error(self.request, "Authentication failed.")
            return reverse('user_login')
    
    
        
class UserLogoutView(View):
    def get(self, request):
        logout(request)
        messages.info(request, "You have been logged out.")
        return redirect('home')
    
