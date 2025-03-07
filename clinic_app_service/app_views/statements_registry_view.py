from math import ceil
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status
from ..models import Appointment

class StatementsRegistryView(APIView):
    def post(self, request):
        body = request.data

        services = body.get('services', [])
        statuses = body.get('statuses', [])
        sort_by = body.get('sortBy', 'id')
        order = body.get('order', 'asc')
        page = int(request.query_params.get('p', 1))
        per_page = int(request.query_params.get('q', 10))

        qs = Appointment.objects.select_related(
            'patient',
            'invoice',
            'price_list_entry',
            'price_list_entry__service'
        )

        if services and len(services) != 0:
            print(services)
            qs = qs.filter(price_list_entry__service__service_name__in=services)

        if statuses and len(statuses) != 0:
            qs = qs.filter(execution_status__in=statuses)

        sort_field_map = {
            'id': 'id',
            'service': 'price_list_entry__service__service_name',
            'endDate': 'completion_date'
        }
        sort_field = sort_field_map.get(sort_by, 'id')
        if order == 'desc':
            sort_field = '-' + sort_field

        qs = qs.order_by(sort_field)

        total_count = qs.count()
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        page_qs = qs[start_index:end_index]

        entries = []
        for appt in page_qs:
            appt_id = appt.id
            service_name = appt.price_list_entry.service.service_name

            pat = appt.patient
            patient_name = f"{pat.last_name} {pat.first_name} {pat.middle_name}".strip()

            base_price = appt.price_list_entry.price
            discount_percent = appt.invoice.discount_percent or 0
            total_price = base_price * (100 - discount_percent) / 100
            total_price_float = float(total_price)

            appt_date_ts = (
                int(appt.appointment_date.timestamp() * 1000)
                if appt.appointment_date else 0
            )
            end_date_ts = (
                int(appt.completion_date.timestamp() * 1000)
                if appt.completion_date else 0
            )

            entries.append({
                "id": appt_id,
                "service": service_name,
                "patientName": patient_name,
                "total": total_price_float,
                "appointmentDate": appt_date_ts,
                "endDate": end_date_ts if end_date_ts else None,
                "status": appt.execution_status,
                "invoiceId": appt.invoice_id
            })

        total_pages = ceil(total_count / per_page)

        return JsonResponse(
            {
                "payloadType": "StatementRegistryDto",
                "payload": {
                    "page": page,
                    "perPage": per_page,
                    "totalPages": total_pages,
                    "entries": entries
                }
            },
            status=status.HTTP_200_OK
        )
