from django.utils import timezone
from django.http import HttpResponse
from django.views import View
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from io import BytesIO
import os

from ..models import Invoice

class InvoicePdfView(View):
    def get(self, request):
        invoice_id = request.GET.get('invoiceId')
        if not invoice_id:
            return HttpResponse("Missing 'invoiceId' query param.", status=400)

        try:
            invoice = Invoice.objects.get(pk=invoice_id)
        except Invoice.DoesNotExist:
            return HttpResponse(f"Invoice {invoice_id} not found.", status=404)

        invoice_number = f"RL-2025-{invoice_id.zfill(5)}"

        first_appt = invoice.appointments.first()
        patient_name = f"{first_appt.patient.last_name} {first_appt.patient.first_name} {first_appt.patient.middle_name}"

        items_data = []
        subtotal = 0.0

        for appt in invoice.appointments.all():
            date_str = (appt.appointment_date.strftime('%d / %m / %Y')
                        if appt.appointment_date else '-')
            service_name = appt.price_list_entry.service.service_name
            base_price = float(appt.price_list_entry.price)

            subtotal += base_price
            items_data.append({
                "date": date_str,
                "service_name": service_name,
                "price": f"{base_price:.2f} грн"
            })

        discount_percent = invoice.discount_percent or 0
        discount_amount = subtotal * discount_percent / 100.0
        total = subtotal - discount_amount

        context = {
            "invoice_number": invoice_number,
            "generation_date": timezone.now().strftime('%d / %m / %Y'),
            "patient_name": patient_name,
            "items": items_data,
            "subtotal": f"{subtotal:.2f}",
            "discount_percent": discount_percent,
            "discount": f"{discount_amount:.2f} грн",
            "total": f"{total:.2f}",
        }

        template_dir = os.path.join(os.getcwd(), 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('invoice.html')
        compiled_html = template.render(context)

        pdf_buffer = BytesIO()
        HTML(string=compiled_html).write_pdf(pdf_buffer)
        pdf_bytes = pdf_buffer.getvalue()

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="Invoice.pdf"'
        )

        return response
