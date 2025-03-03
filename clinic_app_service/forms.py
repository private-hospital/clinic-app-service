from django import forms
from .models import MedicalRecord
from django.forms import CheckboxSelectMultiple

class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ['patient', 'record_type', 'services', 'pdf_links', 'services', 'doctor_conclusion', 'created_at']
        widgets = {
            'services': CheckboxSelectMultiple(),
        }

