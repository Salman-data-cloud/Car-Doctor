from django.db import models
from django.contrib.auth.models import User 

class Mechanic(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class Client(models.Model):
    name = models.TextField()
    address = models.TextField()
    phone = models.TextField()
    car_license = models.TextField()
    engine_number = models.TextField()
    integrity_mac = models.CharField(max_length=64, blank=True, null=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name
    
class Appointment(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    mechanic = models.ForeignKey(Mechanic, on_delete=models.CASCADE)
    date = models.DateField()

    def __str__(self):
        return f"{self.client.name} - {self.date}"

