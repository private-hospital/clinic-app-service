from math import ceil
from django.db.models import QuerySet
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status
from django.utils import timezone

from ..models import Appointment

class AppointmentsView(APIView):
    def get(self, request):
        page = int(request.query_params.get('p', 1))
        per_page = int(request.query_params.get('q', 10))
        status_filter = request.query_params.get('status')

        qs: QuerySet[Appointment] = Appointment.objects.select_related(
            'doctor',
            'patient',
            'price_list_entry',
            'price_list_entry__service'
        ).all()

        if status_filter in ['PLANNED', 'CANCELED', 'COMPLETED']:
            qs = qs.filter(execution_status=status_filter)

        qs = qs.order_by('appointment_date')

        total_count = qs.count()

        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        page_qs = qs[start_index:end_index]

        entries = []
        for appt in page_qs:
            doc = appt.doctor
            patient = appt.patient
            doc_name = f"{doc.last_name} {doc.first_name} {doc.middle_name}".strip()
            patient_name = f"{patient.last_name} {patient.first_name} {patient.middle_name}".strip()

            service_name = appt.price_list_entry.service.service_name
            base_price = float(appt.price_list_entry.price)

            if appt.appointment_date:
                appt_ts = int(appt.appointment_date.timestamp() * 1000)
            else:
                appt_ts = 0

            entries.append({
                "id": appt.id,
                "service": service_name,
                "appointmentDate": appt_ts,
                "status": appt.execution_status,
                "price": base_price,
                "doctorName": doc_name,
                "patientName": patient_name
            })

        total_pages = ceil(total_count / per_page)

        return JsonResponse({
            "payloadType": "AppointmentsRegistryDto",
            "payload": {
                "page": page,
                "perPage": per_page,
                "totalPages": total_pages,
                "entries": entries
            }
        }, status=status.HTTP_200_OK)

    def post(self, request):
        appt_id = request.query_params.get('id')
        if not appt_id:
            return JsonResponse({
                'payloadType': 'ErrorResponseDto',
                'payload': {
                    'detail': 'Missing "id" query parameter.'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            appt = Appointment.objects.select_related('doctor').get(pk=appt_id)
        except Appointment.DoesNotExist:
            return JsonResponse({
                'payloadType': 'ErrorResponseDto',
                'payload': {
                    'detail': f'Appointment with id={appt_id} does not exist.'
                }
            }, status=status.HTTP_404_NOT_FOUND)

        now = timezone.now()
        if not appt.appointment_date or appt.appointment_date >= now:
            return JsonResponse({
                'payloadType': 'ErrorResponseDto',
                'payload': {
                    "detail": "Cannot complete an appointment that hasn't started yet."
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        appt.execution_status = 'COMPLETED'
        appt.completion_date = timezone.now()
        appt.save()

        return JsonResponse({
            'payloadType': 'StatusResponseDto',
            'payload': {
                'status': f'Appointment {appt_id} marked as COMPLETED.'
            }
        }, status=status.HTTP_200_OK)

    def put(self, request):
        appt_id = request.query_params.get('id')

        if not appt_id:
            return JsonResponse({
                'payloadType': 'ErrorResponseDto',
                'payload': {'detail': 'Missing "id" query parameter.'}
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            appt = Appointment.objects.get(pk=appt_id)
        except Appointment.DoesNotExist:
            return JsonResponse({
                'payloadType': 'ErrorResponseDto',
                'payload': {'detail': f'Appointment with id={appt_id} does not exist.'}
            }, status=status.HTTP_404_NOT_FOUND)

        appt.execution_status = 'CANCELED'
        appt.save()

        return JsonResponse({
            'payloadType': 'StatusResponseDto',
            'payload': {'status': f'Appointment {appt_id} marked as CANCELED.'}
        }, status=status.HTTP_200_OK)
