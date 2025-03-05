from rest_framework import serializers
from .models import Patient, SEX_CHOICES, BENEFIT_GROUP_CHOICES


class PatientSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()
    dob = serializers.DateField(
        source='birth_date',
        format='%Y-%m-%d',
        input_formats=['%Y-%m-%d']
    )
    sex = serializers.CharField(source='gender')
    benefit = serializers.CharField(source='benefit_group')
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

    def to_representation(self, instance):

        data = super().to_representation(instance)
        data['sex'] = dict(SEX_CHOICES).get(instance.gender, instance.gender)
        data['benefit'] = dict(BENEFIT_GROUP_CHOICES).get(instance.benefit_group, instance.benefit_group)
        return data
