from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status
from ..models import Service

class CheckServiceExistsView(APIView):
    def get(self, request):
        name = request.query_params.get('name')
        if not name:
            return JsonResponse({
                'payloadType': 'ErrorResponseDto',
                'payload': {
                    "detail": "Missing name query param."
                }
            }, status=status.HTTP_404_BAD_REQUEST)

        service_exists = Service.objects.filter(service_name=name).exists()

        return JsonResponse({
            'payloadType': 'StatusResponseDto',
            'payload': {
                'exists': service_exists
            }
        }, status=status.HTTP_200_OK)
