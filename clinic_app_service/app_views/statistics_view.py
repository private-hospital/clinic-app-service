from django.http import JsonResponse
from datetime import timedelta
from django.utils import timezone
from django.db.models.functions import TruncDate
from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..models import Appointment, User

class WeeklyStatsView(APIView):
    def get(self, request):
        today = timezone.now().date()
        start_date = today - timedelta(days=6)

        qs = (
            Appointment.objects
            .filter(
                execution_status='COMPLETED',
                completion_date__date__gte=start_date
            )
            .annotate(day=TruncDate('completion_date'))
            .values('day')
            .annotate(count=Count('id'))
        )

        counts_by_date = {item['day']: item['count'] for item in qs}

        entries = []
        for i in range(7):
            d = start_date + timedelta(days=i)
            day_str = d.strftime('%d.%m')
            count_for_day = counts_by_date.get(d, 0)
            entries.append({
                'date': day_str,
                'count': count_for_day
            })

        return Response(
            {
                'payloadType': 'WeeklyStatsDto',
                'payload': {
                    'entries': entries
                }
            },
            status=status.HTTP_200_OK
        )

class TodayCumulateView(APIView):
    def get(self, request):
        today = timezone.now().date()
        qs = Appointment.objects.filter(
            execution_status='COMPLETED',
            completion_date__date=today
        ).order_by('completion_date')

        completed_times = [appt.completion_date for appt in qs]

        results = []
        running_total = 0
        idx = 0

        for hour in range(9, 19):
            cutoff = timezone.datetime(
                year=today.year,
                month=today.month,
                day=today.day,
                hour=hour,
                minute=0,
                second=0,
                tzinfo=timezone.get_current_timezone()
            )

            while idx < len(completed_times) and completed_times[idx] < cutoff:
                running_total += 1
                idx += 1

            hour_str = f"{hour:02d}:00"
            results.append({
                'hour': hour_str,
                'count': running_total
            })

        return Response(
            {
                'payloadType': 'TodayCumulateDto',
                'payload': {
                    'entries': results
                }
            },
            status=status.HTTP_200_OK
        )

class DoctorsView(APIView):
    def get(self, request):
        doctors = User.objects.filter(user_type='DOCTOR').order_by('last_name', 'first_name')

        entries = []
        for doc in doctors:
            full_name = f"{doc.last_name} {doc.first_name} {doc.middle_name}".strip()
            entries.append({
                'id': doc.id,
                'name': full_name
            })

        return JsonResponse(
            {
                'payloadType': 'DoctorRegistryDto',
                'payload': {
                    'entries': entries
                }
            },
            status=status.HTTP_200_OK
        )

class DoctorDailyCountsView(APIView):
    def get(self, request):
        doctor_id = request.query_params.get('doctorId')
        if not doctor_id:
            return Response(
                {
                    "payloadType": "ErrorResponseDto",
                    "payload": {
                        "detail": "Missing 'doctorId' query parameter"
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            doctor = User.objects.get(pk=doctor_id, user_type='DOCTOR')
        except User.DoesNotExist:
            return Response(
                {
                    "payloadType": "ErrorResponseDto",
                    "payload": {
                        "detail": f"Doctor with ID={doctor_id} does not exist."
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )

        today = timezone.now().date()
        start_date = today - timedelta(days=6)

        qs = (
            Appointment.objects
            .filter(
                doctor=doctor,
                execution_status='COMPLETED',
                completion_date__date__gte=start_date
            )
            .annotate(day=TruncDate('completion_date'))
            .values('day')
            .order_by('day')
        )

        counts_by_date = {}
        for item in qs.annotate(count=Count('id')):
            day = item['day']
            cnt = item['count']
            counts_by_date[day] = cnt

        entries = []
        for i in range(7):
            d = start_date + timedelta(days=i)
            day_str = d.strftime('%d.%m')
            entries.append({
                'date': day_str,
                'count': counts_by_date.get(d, 0)
            })

        return Response(
            {
                'payloadType': 'DoctorDailyCountsDto',
                'payload': {
                    'entries': entries
                }
            },
            status=status.HTTP_200_OK
        )

class DoctorDailyRevenuesView(APIView):
    def get(self, request):
        doctor_id = request.query_params.get('doctorId')
        if not doctor_id:
            return Response(
                {
                    "payloadType": "ErrorResponseDto",
                    "payload": {
                        "detail": "Missing 'doctorId' query parameter"
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            doctor = User.objects.get(pk=doctor_id, user_type='DOCTOR')
        except User.DoesNotExist:
            return Response(
                {
                    "payloadType": "ErrorResponseDto",
                    "payload": {
                        "detail": f"Doctor with ID={doctor_id} does not exist."
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )

        today = timezone.now().date()
        start_date = today - timedelta(days=6)

        qs = (
            Appointment.objects
            .filter(
                doctor=doctor,
                execution_status='COMPLETED',
                completion_date__date__gte=start_date
            )
            .select_related('price_list_entry', 'invoice')
            .annotate(day=TruncDate('completion_date'))
            .order_by('day')
        )

        revenue_by_date = {}

        for appt in qs:
            day = appt.completion_date.date()
            if day < start_date:
                continue

            base_price = appt.price_list_entry.price

            discount_percent = appt.invoice.discount_percent or 0
            revenue = base_price * (100 - discount_percent) / 100

            if day not in revenue_by_date:
                revenue_by_date[day] = revenue
            else:
                revenue_by_date[day] += revenue

        entries = []
        for i in range(7):
            d = start_date + timedelta(days=i)
            day_str = d.strftime('%d.%m')
            rev = revenue_by_date.get(d, 0)
            rev_float = float(rev)
            entries.append({
                'date': day_str,
                'count': rev_float
            })

        return Response(
            {
                'payloadType': 'DoctorDailyRevenuesDto',
                'payload': {
                    'entries': entries
                }
            },
            status=status.HTTP_200_OK
        )

