from rest_framework import serializers
from .models import Patient, SEX_CHOICES, BENEFIT_GROUP_CHOICES, PriceList


class PatientSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()
    dob = serializers.DateField(
        source='birth_date',
        format='%Y-%m-%d',
        input_formats=['%Y-%m-%d']
    )
    sex = serializers.CharField(source='gender')
    benefit = serializers.CharField(source='benefit_group', allow_blank=True)
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
        data['sex'] = instance.gender
        data['benefit'] = instance.benefit_group
        return data


class PriceListSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='name')
    state = serializers.CharField(source='status')
    isArchived = serializers.BooleanField(source='is_archived')
    archivationReason = serializers.CharField(
        source='archive_reason',
        required=False,
        allow_blank=True
    )
    archivationDate = serializers.SerializerMethodField()

    class Meta:
        model = PriceList
        fields = [
            'id',
            'title',
            'state',
            'isArchived',
            'archivationReason',
            'archivationDate',
        ]

    def get_archivationDate(self, obj):
        if obj.archivation_date:
            return int(obj.archivation_date.timestamp() * 1000)
        return None

from rest_framework import serializers
from .models import PriceListEntry

class CurrentPriceListEntrySerializer(serializers.ModelSerializer):
    label = serializers.CharField(source='service.service_name')
    serviceId = serializers.IntegerField(source='service.id')
    price = serializers.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        model = PriceListEntry
        fields = ['label', 'serviceId', 'price']