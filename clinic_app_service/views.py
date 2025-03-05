# views.py
import bcrypt
from django.shortcuts import render, redirect
from .models import MedicalRecord
from .forms import MedicalRecordForm
from django.http import JsonResponse
from django.db import connection
from django.db.utils import OperationalError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import User
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status

def index(request):
    medi = MedicalRecord.objects.all()
    form = MedicalRecordForm()
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('index')  # або на іншу сторінку
    return render(request, 'index.html', {'medi': medi, 'form': form})

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
            return Response({"error": "Невірний email або пароль"}, status=status.HTTP_401_UNAUTHORIZED)

        # Перевірка пароля
        if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            return Response({"error": "Невірний email або пароль"}, status=status.HTTP_401_UNAUTHORIZED)

        # Генеруємо токен
        refresh = MyRefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({
            "payloadType": "LoginResponseDto",
            "payload": {
                "accessToken": access_token
            }
        })