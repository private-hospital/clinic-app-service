from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status

from ..models import PriceList, PriceListEntry, Patient

class CalculateTotalsView(APIView):
    def post(self, request):
        patient_id = request.query_params.get("patientId")
        if not patient_id:
            return JsonResponse({
                "payloadType": "ErrorResponseDto",
                "payload": {"detail": "Missing 'patientId' query parameter."}
            }, status=status.HTTP_400_BAD_REQUEST)

        body = request.data
        services = body.get("services", [])
        if not isinstance(services, list) or len(services) == 0:
            return JsonResponse({
                "payloadType": "ErrorResponseDto",
                "payload": {
                    "detail": "Request body must include 'services' as a non-empty list."
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            patient = Patient.objects.get(pk=patient_id)
        except Patient.DoesNotExist:
            return JsonResponse({
                "payloadType": "ErrorResponseDto",
                "payload": {"detail": f"Patient with id={patient_id} not found."}
            }, status=status.HTTP_404_NOT_FOUND)

        discount_map = {
            "military": 20,
            "elderly": 10,
            "disabled": 5,
            "staff_family": 40
        }
        discount_percent = discount_map.get(patient.benefit_group, 0)

        try:
            active_pl = PriceList.objects.get(status='ACTIVE')
        except PriceList.DoesNotExist:
            return JsonResponse({
                "payloadType": "ErrorResponseDto",
                "payload": {"detail": "No active price list found."}
            }, status=status.HTTP_404_NOT_FOUND)

        entries_qs = PriceListEntry.objects.select_related('service').filter(
            price_list=active_pl,
            service__service_name__in=services
        )

        subtotal = 0.0
        found_services = {e.service.service_name: float(e.price) for e in entries_qs}
        for svc in services:
            price_val = found_services.get(svc, 0.0)
            subtotal += price_val

        total = subtotal * (100 - discount_percent) / 100.0

        return JsonResponse({
            "payloadType": "ServicesTotalDto",
            "payload": {
                "subtotal": round(subtotal, 2),
                "discount": float(discount_percent),
                "total": round(total, 2)
            }
        }, status=status.HTTP_200_OK)