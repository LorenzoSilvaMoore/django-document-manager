from django.contrib import admin
from .models.city import City
from .models.country import Country
from .models.region import Region
from .models.subregion import Subregion
from .models.state import State

admin.site.register(City)
admin.site.register(Country)
admin.site.register(Region)
admin.site.register(Subregion)
admin.site.register(State)