from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status

from ..models import Verification


class RemoveVerificationCodeView(APIView):
    def delete(self, request):
        email = request.query_params.get('email')
        if not email:
            return JsonResponse({
                'payloadType': 'ErrorResponseDto',
                'payload': {
                    "detail": "Missing email query param."
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            Verification.objects.filter(email=email).delete()
            return JsonResponse({
                'payloadType': 'StatusResponseDto',
                'payload': {
                    "detail": "OK"
                }
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse({
                'payloadType': 'ErrorResponseDto',
                'payload': {
                    "detail": str(e)
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
