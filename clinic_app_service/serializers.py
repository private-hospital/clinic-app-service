from rest_framework import serializers
from .models import Patient, SEX_CHOICES, BENEFIT_GROUP_CHOICES
from datetime import datetime


class PatientSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()
    dob = serializers.SerializerMethodField()
    sex = serializers.SerializerMethodField()
    benefit = serializers.SerializerMethodField()
    phone = serializers.CharField(source='phone_number')

    class Meta:
        model = Patient
        fields = ['id', 'fullname', 'phone', 'email', 'dob', 'sex', 'benefit']

    def get_fullname(self, obj):
        return f"{obj.last_name} {obj.first_name} {obj.middle_name}"

    def get_dob(self, obj):
        if obj.birth_date:
            return obj.birth_date.strftime('%d.%m.%Y')  # Форматування дати
        return None

    def get_sex(self, obj):
        return dict(SEX_CHOICES).get(obj.gender, obj.gender)

    def get_benefit(self, obj):
        return dict(BENEFIT_GROUP_CHOICES).get(obj.benefit_group, obj.benefit_group)
