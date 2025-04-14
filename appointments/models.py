from django.db import models

class Mechanic(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class Client(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    car_license = models.CharField(max_length=20)
    engine_number = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    
class Appointment(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    mechanic = models.ForeignKey(Mechanic, on_delete=models.CASCADE)
    date = models.DateField()

    def __str__(self):
        return f"{self.client.name} - {self.date}"

