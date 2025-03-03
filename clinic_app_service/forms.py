from django import forms
from .models import Patient, Service, MedicalRecord, Invoice, User, PriceList, PriceListEntry, Appointment
from django.forms import CheckboxSelectMultiple


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['last_name', 'first_name', 'middle_name', 'phone_number', 'email', 'birth_date',
                  'gender', 'benefit_group']


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['service_name', 'is_service_archived']


class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ['patient', 'record_type', 'pdf_links', 'services', 'doctor_conclusion', 'created_at']
        widgets = {
            'services': CheckboxSelectMultiple(),
        }


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['discount_percent', 'subtotal', 'total', 'paid_date']


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['last_name', 'first_name', 'middle_name', 'email', 'user_type', 'services',
                  'password_hash', 'qualification']
        widgets = {
            'services': CheckboxSelectMultiple(),
        }


class PriceListForm(forms.ModelForm):
    class Meta:
        model = PriceList
        fields = ['name', 'status', 'is_archived', 'archive_reason']


class PriceListEntryForm(forms.ModelForm):
    class Meta:
        model = PriceListEntry
        fields = ['price_list', 'service', 'price']


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['invoice', 'patient', 'doctor', 'price_list_entry', 'execution_status',
                  'appointment_date', 'completion_date']