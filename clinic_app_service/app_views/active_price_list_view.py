# views.py

from django.db.models.query import QuerySet
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from ..models import PriceList, PriceListEntry, Service
from ..serializers import CurrentPriceListEntrySerializer


class ActivePriceListView(APIView):
    def get(self, request):
        active_pl = PriceList.objects.filter(status='ACTIVE').first()
        if not active_pl:
            return JsonResponse({
                'payloadType': 'CurrentPriceListDto',
                'payload': {
                    'entries': []
                }
            }, status=status.HTTP_200_OK)
        entries_qs: QuerySet[PriceListEntry] = active_pl.entries.select_related('service')
        serializer = CurrentPriceListEntrySerializer(entries_qs, many=True)
        return JsonResponse({
            'payloadType': 'CurrentPriceListDto',
            'payload': {
                'entries': serializer.data
            }
        }, status=status.HTTP_200_OK)

    def post(self, request):
        pl_id = request.query_params.get('id')
        if not pl_id:
            return JsonResponse(
                {
                    "payloadType": "ErrorResponseDto",
                    "payload": {
                        "detail": "Missing 'id' query parameter"
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            pl = PriceList.objects.get(pk=pl_id)
        except PriceList.DoesNotExist:
            return JsonResponse(
                {
                    "payloadType": "ErrorResponseDto",
                    "payload": {
                        "detail": f"Price list with id={pl_id} does not exist"
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )

        PriceList.objects.update(status='INACTIVE')

        pl.status = 'ACTIVE'
        pl.save()

        non_archived_services = Service.objects.filter(is_service_archived=False)

        for service in non_archived_services:
            existing_entry = PriceListEntry.objects.filter(price_list=pl, service=service).exists()
            if existing_entry:
                continue

            recent_entry = PriceListEntry.objects.filter(service=service).order_by('-price_list__id').first()

            if not recent_entry:
                continue

            PriceListEntry.objects.create(
                price_list=pl,
                service=service,
                price=recent_entry.price
            )

        return JsonResponse({
            'payloadType': 'StatusResponseDto',
            'payload': {
                'status': 'OK'
            }
        }, status=status.HTTP_200_OK)
