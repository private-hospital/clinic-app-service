from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status

from ..models import PriceList, PriceListEntry, Patient

class CartCalculationView(APIView):
    def post(self, request):
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

        found_services = {e.service.service_name: float(e.price) for e in entries_qs}

        prices_list = []
        for svc in services:
            if svc in found_services:
                prices_list.append({"service": svc, "price": found_services[svc]})
            else:
                prices_list.append({"service": svc, "price": 0.0})

        return JsonResponse({
            "payloadType": "ServicesPricesDto",
            "payload": {
                "prices": prices_list
            }
        }, status=status.HTTP_200_OK)
