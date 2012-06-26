from django.contrib import admin
from djdev.modelwork.models import Vehicle
from guardian.admin import GuardedModelAdmin


class VehicleAdmin(GuardedModelAdmin):
    pass

admin.site.register(Vehicle, VehicleAdmin)