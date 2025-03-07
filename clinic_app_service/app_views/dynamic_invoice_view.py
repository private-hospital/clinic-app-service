from rest_framework.views import APIView
from django.http import HttpResponse
from django.utils import timezone
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from io import BytesIO
import os

class DynamicInvoiceView(APIView):
    def post(self, request):
        body = request.data
        appointments = body.get('appointments', [])
        if not isinstance(appointments, list) or len(appointments) == 0:
            return HttpResponse("Invalid or empty 'appointments' array.", status=400)

        items_data = []
        for appt in appointments:
            appt_date_str = appt.get('date', '')
            appt_time_str = appt.get('time', '')
            combined_date = f"{appt_date_str} {appt_time_str}".strip()
            service_name = appt.get('service', '')
            items_data.append({
                "date": combined_date or '-',
                "service_name": service_name,
                "price": "0.00 грн"
            })

        subtotal_str = "0.00"
        total_str = "0.00"

        invoice_number = f"DYN-{timezone.now().strftime('%Y%m%d-%H%M%S')}"
        context = {
            "invoice_number": invoice_number,
            "generation_date": timezone.now().strftime('%d / %m / %Y'),
            "items": items_data,
            "subtotal": subtotal_str,
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
        response['Content-Disposition'] = (
            f'attachment; filename="Invoice.pdf"'
        )
        return response
