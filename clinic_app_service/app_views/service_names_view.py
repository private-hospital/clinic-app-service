from django.http.response import JsonResponse
from rest_framework.views import APIView
from rest_framework import status
from ..models import Service

class ServiceNamesView(APIView):
    def get(self, request):
        services = Service.objects.all().order_by('service_name')
        names = [s.service_name for s in services]
        return JsonResponse({
            'payloadType': 'AvailableServicesDto',
            'payload': {
                'services': names
            }
        }, status=status.HTTP_200_OK)
