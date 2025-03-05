from rest_framework import serializers
from .models import Patient, SEX_CHOICES, BENEFIT_GROUP_CHOICES
from datetime import datetime


class PatientSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()
    dob = serializers.DateField(
        source='birth_date',
        format='%Y-%m-%d',
        input_formats=['%Y-%m-%d']
    )
    sex = serializers.SerializerMethodField(source="gender")
    benefit = serializers.SerializerMethodField(source="benefit_group")
    phone = serializers.CharField(source='phone_number')
    lastName = serializers.CharField(source='last_name')
    firstName = serializers.CharField(source='first_name')
    middleName = serializers.CharField(
        source='middle_name',
        required=False,
        allow_blank=True,
        allow_null=True
    )
    class Meta:
        model = Patient
        fields = ['id', 'fullname', 'phone', 'email', 'dob', 'sex', 'benefit', 'lastName', 'firstName', 'middleName']

    def get_fullname(self, obj):
        return f"{obj.last_name} {obj.first_name} {obj.middle_name}"

    def get_sex(self, obj):
        return dict(SEX_CHOICES).get(obj.gender, obj.gender)

    def get_benefit(self, obj):
        return dict(BENEFIT_GROUP_CHOICES).get(obj.benefit_group, obj.benefit_group)
