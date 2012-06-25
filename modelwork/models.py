from django.db import models
from django.contrib.auth.models import User # Mostly just to put this into our namespace if we import *
from guardian import shortcuts

class Vehicle(models.Model):
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.IntegerField()
    
    class Meta:
        permissions = (
                ('can_operate','Can operate this vehicle.'),
            )
    
    def __repr__(self):
        return "Vehicle(make=\"%s\",model=\"%s\",year=%s)" % (self.make,self.model,self.year)
        
class Motorcycle(Vehicle):
    has_sidecart = models.BooleanField(default=False)
    
class Bicycle(Vehicle):
    pass
    
# Model inheritance seems to work well. A new db table is created for each sub class, and the records are joined
# when selecting them. But they don't appear to inherit Meta info, such as permissions.