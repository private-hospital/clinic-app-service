from django.db.models import QuerySet
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status

from ..models import Appointment, Patient

class PatientAppointmentsView(APIView):
    def get(self, request):
        patient_id = request.query_params.get('id')

        if not patient_id:
            return JsonResponse({
                'payloadType': 'ErrorResponseDto',
                'payload': {'detail': 'Missing "id" query parameter.'}
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            patient = Patient.objects.get(pk=patient_id)
        except Patient.DoesNotExist:
            return JsonResponse({
                'payloadType': 'ErrorResponseDto',
                'payload': {'detail': f'Patient with id={patient_id} does not exist.'}
            }, status=status.HTTP_404_NOT_FOUND)

        qs: QuerySet[Appointment] = Appointment.objects.filter(patient=patient).select_related(
            'doctor',
            'price_list_entry',
            'price_list_entry__service',
            'invoice'
        ).order_by('-appointment_date')

        entries = []
        for appt in qs:
            doc = appt.doctor
            service_name = appt.price_list_entry.service.service_name
            base_price = float(appt.price_list_entry.price)

            discount_percent = appt.invoice.discount_percent if appt.invoice else 0
            total_price = base_price * (100 - discount_percent) / 100

            doc_name = f"{doc.last_name} {doc.first_name} {doc.middle_name}".strip()
            patient_name = f"{patient.last_name} {patient.first_name} {patient.middle_name}".strip()

            appt_date_ts = int(appt.appointment_date.timestamp() * 1000) if appt.appointment_date else 0

            entries.append({
                "id": appt.id,
                "service": service_name,
                "appointmentDate": appt_date_ts,
                "status": appt.execution_status,
                "price": round(total_price, 2),
                "doctorName": doc_name,
                "patientName": patient_name
            })

            print(entries)

        return JsonResponse({
            "payloadType": "AppointmentsRegistryDto",
            "payload": {
                "page": 0,
                "perPage": 0,
                "totalPages": 0,
                "entries": entries
            }
        }, status=status.HTTP_200_OK)
