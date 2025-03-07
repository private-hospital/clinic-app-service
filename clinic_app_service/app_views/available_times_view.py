from datetime import datetime, timedelta
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status
import pytz

from clinic_app_service.models import Appointment

class AvailableTimesView(APIView):
    def get(self, request):
        doctor_id = request.query_params.get('doctorId')
        date_str = request.query_params.get('date')

        if not doctor_id or not date_str:
            return JsonResponse({
                "payloadType": "ErrorResponseDto",
                "payload": {"detail": "Missing 'doctorId' or 'date' query parameter."}
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            naive_date = datetime.strptime(date_str, "%Y-%m-%d")
            tz = pytz.FixedOffset(120)
            local_date = tz.localize(naive_date)
        except ValueError:
            return JsonResponse({
                "payloadType": "ErrorResponseDto",
                "payload": {"detail": "Invalid date format. Use YYYY-MM-DD."}
            }, status=status.HTTP_400_BAD_REQUEST)

        if local_date.weekday() in [5, 6]:
            return JsonResponse({
                "payloadType": "AvailableTimes",
                "payload": {"entries": []}
            }, status=status.HTTP_200_OK)

        existing_appointments = Appointment.objects.filter(
            doctor_id=doctor_id,
            appointment_date__year=local_date.year,
            appointment_date__month=local_date.month,
            appointment_date__day=local_date.day
        ).exclude(execution_status='CANCELED').values_list('appointment_date', flat=True)

        tz = pytz.FixedOffset(120)
        taken_slots = {appt.astimezone(tz).time() for appt in existing_appointments}

        start_time = datetime.strptime("09:00", "%H:%M").time()
        end_time = datetime.strptime("18:00", "%H:%M").time()
        slot_duration = timedelta(minutes=30)

        available_slots = []

        naive_start = datetime.combine(local_date.date(), start_time)
        current_time = tz.localize(naive_start)

        while current_time.time() < end_time:
            next_time = current_time + slot_duration

            if current_time.time() not in taken_slots:
                available_slots.append(
                    f"{current_time.strftime('%H:%M')} - {next_time.strftime('%H:%M')}"
                )

            current_time = next_time

        return JsonResponse({
            "payloadType": "AvailableTimes",
            "payload": {"entries": available_slots}
        }, status=status.HTTP_200_OK)
