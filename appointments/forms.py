from django import forms
from .models import Client, Appointment, Mechanic
import datetime

class AppointmentForm(forms.Form):
    name = forms.CharField(max_length=100)
    address = forms.CharField(widget=forms.Textarea)
    phone = forms.CharField(max_length=20)
    car_license = forms.CharField(max_length=20)
    engine_number = forms.CharField(max_length=50)
    appointment_date = forms.DateField(widget=forms.SelectDateWidget(), initial=datetime.date.today)
    mechanic = forms.ModelChoiceField(queryset=Mechanic.objects.all())

    def clean_engine_number(self):
        engine_number = self.cleaned_data['engine_number']
        if not engine_number.isdigit():
            raise forms.ValidationError("Engine number must contain only digits.")
        return engine_number