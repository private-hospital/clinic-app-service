from django.db import transaction
from django.utils.timezone import now
from ..models import Invoice, PriceListEntry, Appointment, Patient, PriceList, User
from datetime import datetime
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status
import pytz

from ..mail_service import send_appointment_notification

class CreateAppointmentView(APIView):
    def post(self, request):
        patient_id = request.query_params.get('patientId')
        body = request.data

        if not patient_id or 'appointments' not in body:
            return JsonResponse({
                "payloadType": "ErrorResponseDto",
                "payload": {"detail": "Missing 'patientId' query parameter or appointments data."}
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            patient = Patient.objects.get(pk=patient_id)
        except Patient.DoesNotExist:
            return JsonResponse({
                "payloadType": "ErrorResponseDto",
                "payload": {"detail": f"Patient with id={patient_id} does not exist."}
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            price_list = PriceList.objects.get(status='ACTIVE')
        except PriceList.DoesNotExist:
            return JsonResponse({
                "payloadType": "ErrorResponseDto",
                "payload": {"detail": "No active price list found."}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        service_names = {appt['service'] for appt in body['appointments']}
        price_entries = PriceListEntry.objects.filter(
            price_list=price_list,
            service__service_name__in=service_names
        ).select_related('service')

        if not price_entries.exists():
            return JsonResponse({
                "payloadType": "ErrorResponseDto",
                "payload": {"detail": "No price list entries found for provided services."}
            }, status=status.HTTP_404_NOT_FOUND)

        subtotal = sum(entry.price for entry in price_entries)
        discount_percent = {
            'military': 20,
            'elderly': 10,
            'disabled': 5,
            'staff_family': 40
        }.get(patient.benefit_group, 0)
        total = subtotal * (100 - discount_percent) / 100

        with transaction.atomic():
            invoice = Invoice.objects.create(
                subtotal=subtotal,
                discount_percent=discount_percent,
                total=total,
                paid_date=now()
            )

            appointments = []
            for appt in body['appointments']:
                service_name = appt['service']
                doctor_id = appt['doctorId']
                appt_date_str = appt['date']
                appt_time_str = appt['time'].split(" - ")[0]

                try:
                    price_entry = price_entries.get(service__service_name=service_name)
                except PriceListEntry.DoesNotExist:
                    return JsonResponse({
                        "payloadType": "ErrorResponseDto",
                        "payload": {"detail": f"Price entry not found for service: {service_name}"}
                    }, status=status.HTTP_404_NOT_FOUND)

                appointment_datetime = datetime.strptime(
                    f"{appt_date_str} {appt_time_str}", "%Y-%m-%d %H:%M"
                )
                utc_plus_2 = pytz.FixedOffset(120)
                dt_with_tz = utc_plus_2.localize(appointment_datetime)

                appointment = Appointment(
                    patient=patient,
                    doctor_id=doctor_id,
                    price_list_entry=price_entry,
                    invoice=invoice,
                    execution_status="PLANNED",
                    appointment_date=dt_with_tz,
                    completion_date=None
                )
                appointments.append(appointment)

            Appointment.objects.bulk_create(appointments)

            for appt in appointments:
                try:
                    doctor = User.objects.get(pk=appt.doctor_id)
                except User.DoesNotExist:
                    continue

                doctor_name = f"{doctor.first_name} {doctor.last_name}"
                doctor_email = doctor.email
                patient_name = f"{patient.last_name} {patient.first_name}"
                appt_date_formatted = appt.appointment_date.strftime("%d.%m.%Y")
                appt_time_formatted = appt.appointment_date.strftime("%H:%M")

                send_appointment_notification(
                    doctor_email=doctor_email,
                    doctor_name=doctor_name,
                    patient_name=patient_name,
                    appointment_date=appt_date_formatted,
                    appointment_time=appt_time_formatted,
                    patient_id=patient.id
                )

        return JsonResponse({
            "payloadType": "StatusResponseDto",
            "payload": {"status": "Appointments successfully created."}
        }, status=status.HTTP_201_CREATED)
