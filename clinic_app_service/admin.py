from django.contrib import admin
from .models import Patient, MedicalRecord, Service, User, PriceList, PriceListEntry, Invoice, Appointment
from .forms import MedicalRecordForm

admin.site.register(Patient)
admin.site.register(MedicalRecord)
admin.site.register(Service)
admin.site.register(User)
admin.site.register(PriceList)
admin.site.register(PriceListEntry)
admin.site.register(Invoice)
admin.site.register(Appointment)

