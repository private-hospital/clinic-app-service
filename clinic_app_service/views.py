# views.py
from math import ceil
import bcrypt
from django.db.models.query import QuerySet
from django.shortcuts import render, redirect
from .models import MedicalRecord, Patient
from .forms import MedicalRecordForm
from django.http import JsonResponse
from django.db import connection
from django.db.utils import OperationalError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import User, Service, Appointment
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status, generics
from .serializers import PatientSerializer,  MedicalRecordSerializer
from rest_framework.decorators import api_view
from datetime import datetime
from rest_framework.generics import ListAPIView

def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except OperationalError:
        return JsonResponse(
            {
                "payloadType": "HealthResponseDto",
                "payload": {
                    "status": "UNHEALTHY"
                }
            },
            status=500
        )

    return JsonResponse({
        "payloadType": "HealthResponseDto",
        "payload": {
            "status": "HEALTHY"
        }
    })

class MyRefreshToken(RefreshToken):
    @classmethod
    def for_user(cls, user):
        # Створюємо стандартний токен
        token = super().for_user(user)

        middle_name = f"{user.middle_name[0]}." if user.middle_name.strip() else ' '

        # Додаємо додаткові дані в payload
        token['sub'] = {
            'id': user.id,
            'role': user.user_type,
            'fullname': f"{user.last_name} {user.first_name[0]}. {middle_name}"
        }
        print(token)
        return token

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Неправильний email або пароль"}, status=status.HTTP_401_UNAUTHORIZED)

        # Перевірка пароля
        if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            return Response({"error": "Неправильний email або пароль"}, status=status.HTTP_401_UNAUTHORIZED)

        # Генеруємо токен
        refresh = MyRefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({
            "payloadType": "LoginResponseDto",
            "payload": {
                "accessToken": access_token
            }
        })


class PatientListView(APIView):
    def get(self, request):
        page = int(request.query_params.get('p', 1))
        per_page = int(request.query_params.get('q', 10))

        start_index = (page - 1) * per_page
        end_index = start_index + per_page

        queryset: QuerySet[Patient] = Patient.objects.all()
        total_count = queryset.count()

        page_qs = queryset[start_index:end_index]

        serializer = PatientSerializer(page_qs, many=True)

        return JsonResponse({
           'payloadType': 'PatientsRegistryDto',
           'payload': {
               'page': page,
               'perPage': per_page,
               'totalPages': ceil(total_count / per_page),
               'entries': serializer.data
           }
        }, status=status.HTTP_200_OK)

class PatientDetailView(APIView):
    def get(self, request, id):
        try:
            patient = Patient.objects.get(id=id)
            serializer = PatientSerializer(patient)
            return Response(serializer.data)
        except Patient.DoesNotExist:
            return Response({"detail": "Пацієнт не знайдений"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, id):
        try:
            patient = Patient.objects.get(id=id)
            serializer = PatientSerializer(patient, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Patient.DoesNotExist:
            return Response({"detail": "Пацієнт не знайдений"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, id):
        try:
            patient = Patient.objects.get(id=id)
            patient.delete()
            return Response({"detail": "Пацієнт видалений"}, status=status.HTTP_204_NO_CONTENT)
        except Patient.DoesNotExist:
            return Response({"detail": "Пацієнт не знайдений"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def create_patient(request):
    if request.method == 'POST':
        serializer = PatientSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'Пацієнт успішно доданий'})
        return Response(serializer.errors, status=400)

def get_services(request):
    services = Service.objects.filter(is_service_archived=False).values('id', 'service_name')
    return JsonResponse(list(services), safe=False)

def get_doctors_by_service(request, service_id):
    doctors = User.objects.filter(user_type='DOCTOR', services__id=service_id).values('id', 'first_name', 'last_name')
    return JsonResponse(list(doctors), safe=False)

def get_available_times(request, doctor_id, date):
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        booked_times = Appointment.objects.filter(doctor_id=doctor_id, appointment_date__date=date_obj).values_list('appointment_date', flat=True)

        all_times = ["09:00", "09:30", "10:00", "10:30", "11:00"]  # Приклад
        available_times = [time for time in all_times if time not in [bt.strftime('%H:%M') for bt in booked_times]]

        return JsonResponse(available_times, safe=False)
    except ValueError:
        return JsonResponse({"error": "Invalid date format"}, status=400)

class MedicalRecordListView(ListAPIView):
    queryset = MedicalRecord.objects.all().select_related('patient').prefetch_related('services')
    serializer_class = MedicalRecordSerializer
