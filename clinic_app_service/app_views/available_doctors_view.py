from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status
from ..models import User

class AvailableDoctorsView(APIView):
    def get(self, request):
        service_name = request.query_params.get('service')
        if not service_name:
            return JsonResponse({
                "payloadType": "ErrorResponseDto",
                "payload": {"detail": "Missing 'service' query parameter."}
            }, status=status.HTTP_400_BAD_REQUEST)

        doctors_qs = User.objects.filter(
            user_type='DOCTOR',
            services__service_name=service_name
        ).order_by('last_name', 'first_name', 'middle_name')

        doctors_list = [
            {
                "id": doc.id,
                "displayName": f"{doc.last_name} {doc.first_name} {doc.middle_name} ({doc.qualification})".strip()
            }
            for doc in doctors_qs
        ]

        return JsonResponse({
            "payloadType": "AvailableDoctors",
            "payload": {"entries": doctors_list}
        }, status=status.HTTP_200_OK)
