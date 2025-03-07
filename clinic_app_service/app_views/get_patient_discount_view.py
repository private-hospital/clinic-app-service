from django.http import JsonResponse
from django.views import View
from ..models import Patient

class GetPatientDiscountView(View):
    def get(self, request):
        patient_id = request.GET.get("patientId")

        if not patient_id:
            return JsonResponse({
                "payloadType": "ErrorResponseDto",
                "payload": {"detail": "Missing 'patientId' query parameter."}
            }, status=400)

        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return JsonResponse({
                "payloadType": "ErrorResponseDto",
                "payload": {"detail": f"Patient with id={patient_id} not found."}
            }, status=404)

        discount_mapping = {
            "military": 20,
            "elderly": 10,
            "disabled": 5,
            "staff_family": 40,
        }

        discount_percent = discount_mapping.get(patient.benefit_group, 0)

        return JsonResponse({
            "payloadType": "PatientDiscountDto",
            "payload": {
                "patientId": patient_id,
                "discountPercent": discount_percent
            }
        }, status=200)
