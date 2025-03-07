import os
from io import BytesIO
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.shortcuts import get_object_or_404
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from rest_framework.views import APIView

from ..models import Patient, PriceList, PriceListEntry

class DynamicInvoiceView(APIView):
    def post(self, request):
        patient_id = request.query_params.get('patientId')
        if not patient_id:
            return JsonResponse({
                'payloadType': 'ErrorResponseDto',
                'payload': {'detail': "Missing patientId query param."}
            }, status=400)

        patient = get_object_or_404(Patient, pk=patient_id)

        discount_map = {
            "military": 20,
            "elderly": 10,
            "disabled": 5,
            "staff_family": 40
        }
        discount_percent = discount_map.get(patient.benefit_group, 0)

        body = request.data
        appointments = body.get('appointments', [])
        if not isinstance(appointments, list) or len(appointments) == 0:
            return HttpResponse("Invalid or empty 'appointments' array.", status=400)

        try:
            active_price_list = PriceList.objects.get(status='ACTIVE')
        except PriceList.DoesNotExist:
            return HttpResponse("Active PriceList not found.", status=500)

        items_data = []
        subtotal = 0.0

        for appt in appointments:
            appt_date_str = appt.get('date', '')
            appt_time_str = appt.get('time', '')
            combined_date = f"{appt_date_str} {appt_time_str}".strip() or '-'
            service_name = appt.get('service', '').strip()

            entry = PriceListEntry.objects.filter(
                price_list=active_price_list,
                service__service_name=service_name
            ).first()

            price_value = float(entry.price) if entry else 0.00
            subtotal += price_value

            items_data.append({
                "date": combined_date,
                "service_name": service_name,
                "price": f"{price_value:.2f}"
            })

        # Calculate discount and total
        discount_value = subtotal * discount_percent / 100
        total = subtotal - discount_value

        subtotal_str = f"{subtotal:.2f}"
        discount_value_str = f"{discount_value:.2f}"
        total_str = f"{total:.2f}"

        invoice_number = f"DYN-{timezone.now().strftime('%Y%m%d-%H%M%S')}"
        context = {
            "invoice_number": invoice_number,
            "generation_date": timezone.now().strftime('%d / %m / %Y'),
            "items": items_data,
            "subtotal": subtotal_str,
            "discount_percent": discount_percent,
            "discount_value": discount_value_str,
            "total": total_str,
        }

        template_dir = os.path.join(os.getcwd(), 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('invoice_dynamic.html')
        compiled_html = template.render(context)

        pdf_buffer = BytesIO()
        HTML(string=compiled_html).write_pdf(pdf_buffer)
        pdf_bytes = pdf_buffer.getvalue()

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="Invoice.pdf"'
        return response
