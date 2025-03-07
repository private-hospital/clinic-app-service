from django.utils import timezone
from django.http import HttpResponse
from django.views import View
from django.middleware.csrf import get_token
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from io import BytesIO
import os

from ..models import Appointment

class StatementPdfView(View):
    def get(self, request):
        services = request.GET.getlist('services', [])
        statuses = request.GET.getlist('statuses', [])
        sort_by = request.GET.get('sortBy', 'id')
        order = request.GET.get('order', 'asc')

        qs = Appointment.objects.select_related(
            'patient',
            'invoice',
            'price_list_entry',
            'price_list_entry__service'
        )

        if services:
            qs = qs.filter(price_list_entry__service__service_name__in=services)

        if statuses:
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

        appointments_data = []
        for appt in qs:
            appt_id = appt.id
            service_name = appt.price_list_entry.service.service_name
            pat = appt.patient
            patient_name = f"{pat.last_name} {pat.first_name} {pat.middle_name}".strip()

            base_price = appt.price_list_entry.price
            discount_percent = appt.invoice.discount_percent or 0
            total_price = base_price * (100 - discount_percent) / 100
            total_price_float = float(total_price)

            appt_date_str = (
                appt.appointment_date.strftime('%d.%m.%Y %H:%M')
                if appt.appointment_date else None
            )
            end_date_str = (
                appt.completion_date.strftime('%d.%m.%Y %H:%M')
                if appt.completion_date else None
            )

            appointments_data.append({
                "id": appt_id,
                "service": service_name,
                "patientName": patient_name,
                "total": f"{total_price_float:.2f}",
                "appointmentDate": appt_date_str,
                "endDate": end_date_str,
                "status": to_readable_status(appt.execution_status),
            })

        context = {
            "generation_date": timezone.now().strftime('%d / %m / %Y'),
            "appointments": appointments_data
        }

        print(context)
        template_dir = os.path.join(os.getcwd(), 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('statement.html')
        compiled_html = template.render(context)

        pdf_buffer = BytesIO()
        HTML(string=compiled_html).write_pdf(pdf_buffer)
        pdf_bytes = pdf_buffer.getvalue()

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="Statement.pdf"'
        )

        token = get_token(request)
        response.set_cookie('csrftoken', token)

        return response

def to_readable_status(status):
    if status == 'COMPLETED':
        return 'Завершений'
    if status == 'CANCELED':
        return 'Скасований'
    return 'Запланований'