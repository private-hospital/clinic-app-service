# views.py
from django.shortcuts import render, redirect
from .models import MedicalRecord
from .forms import MedicalRecordForm
from django.http import JsonResponse
from django.db import connection
from django.db.utils import OperationalError

# def index(request):
#     medi = MedicalRecord.objects.all()
#     form = MedicalRecordForm()
#     if request.method == 'POST':
#         form = MedicalRecordForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('index')  # або на іншу сторінку
#     return render(request, 'index.html', {'medi': medi, 'form': form})

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