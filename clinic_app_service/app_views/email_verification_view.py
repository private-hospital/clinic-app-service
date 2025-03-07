import random
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status

from ..mail_service import send_email_verification_notification
from ..models import User, Verification


class SendVerificationCodeView(APIView):
    def get(self, request):
        email = request.query_params.get('email')
        if not email:
            return JsonResponse({
                'payloadType': 'ErrorResponseDto',
                'payload': {
                    "detail": "Missing email query param."
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            Verification.objects.get(email=email)
            return JsonResponse({
                'payloadType': 'ErrorResponseDto',
                'payload': {
                    "detail": "Email already exists"
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        except Verification.DoesNotExist:
            code = random.randint(100000, 999999)
            Verification.objects.create(email=email, code=code)
            send_email_verification_notification(email, code)

            return JsonResponse({
                'payloadType': 'StatusResponseDto',
                'payload': {
                    'status': 'OK'
                }
            }, status=status.HTTP_200_OK)


class VerifyEmailView(APIView):
    def get(self, request):
        email = request.query_params.get('email')
        code_str = request.query_params.get('code')

        if not email or not code_str:
            return JsonResponse({
                'payloadType': 'ErrorResponseDto',
                'payload': {
                    "detail": "Missing email query param."
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            code = int(code_str)
        except ValueError:
            return JsonResponse({
                'payloadType': 'ErrorResponseDto',
                'payload': {
                    "detail": "Invalid code format."
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            verification = Verification.objects.get(email=email)
        except Verification.DoesNotExist:
            return JsonResponse({
                'payloadType': 'ErrorResponseDto',
                'payload': {
                    "detail": f"Verification with email {email} not found"
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        if verification.code == code:
            return JsonResponse({
                'payloadType': 'StatusResponseDto',
                'payload': {
                    'status': 'OK'
                }
            }, status=status.HTTP_200_OK)
        else:
            return JsonResponse({
                'payloadType': 'ErrorResponseDto',
                'payload': {
                    "detail": "Invalid verification code"
                }
            }, status=status.HTTP_400_BAD_REQUEST)
