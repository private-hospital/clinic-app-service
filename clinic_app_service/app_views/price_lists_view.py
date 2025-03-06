# views.py
from math import ceil

from django.db.models.expressions import Case, When
from django.db.models.fields import IntegerField
from django.db.models.query import QuerySet
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView

from ..models import PriceList, PriceListEntry, Service
from ..serializers import PriceListSerializer


class PriceListsView(APIView):
    def get(self, request):
        page = int(request.query_params.get('p', 1))
        per_page = int(request.query_params.get('q', 10))
        is_archived = request.query_params.get('a')

        queryset: QuerySet[PriceList] = PriceList.objects.all()

        if is_archived is not None:
            if is_archived.lower() == 'true':
                queryset = queryset.filter(is_archived=True)
            elif is_archived.lower() == 'false':
                queryset = queryset.filter(is_archived=False)

        queryset = queryset.annotate(
            order_by_active=Case(
                When(status='ACTIVE', then=0),
                default=1,
                output_field=IntegerField(),
            )
        ).order_by('order_by_active', 'id')

        start_index = (page - 1) * per_page
        end_index = start_index + per_page

        total_count = queryset.count()

        page_qs = queryset[start_index:end_index]

        serializer = PriceListSerializer(page_qs, many=True)

        return JsonResponse({
            'payloadType': 'PriceListRegistryDto',
            'payload': {
                'page': page,
                'perPage': per_page,
                'totalPages': ceil(total_count / per_page),
                'entries': serializer.data
            }
        }, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data

        name = data.get('name')
        entries = data.get('entries', [])
        print('Creating new price list')
        print(name)
        print(entries)

        new_price_list = PriceList.objects.create(
            name=name,
            status='INACTIVE',
            is_archived=False,
        )

        created_entries = []
        for entry in entries:
            service_id = entry.get('serviceId')
            price = entry.get('price')

            service = Service.objects.get(pk=service_id)

            ple = PriceListEntry.objects.create(
                price_list=new_price_list,
                service=service,
                price=price
            )
            created_entries.append(ple)

        return JsonResponse(
            {
                'payloadType': 'StatusResponseDto',
                'payload': {
                    'status': 'OK'
                }
            },
            status=status.HTTP_201_CREATED
        )

    def put(self, request):
        id = request.query_params.get('id')
        if not id:
            return JsonResponse(
                {
                    'payloadType': 'ErrorResponseDto',
                    'payload': {
                        'detail': "Missing 'id' query param."
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            price_list = PriceList.objects.get(pk=id)
        except PriceList.DoesNotExist:
            return JsonResponse(
                {
                    'payloadType': 'ErrorResponseDto',
                    'payload': {
                        'detail': f"Price list with ID={id} does not exist."
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if price_list.status == 'ACTIVE':
            return JsonResponse(
                {
                    'payloadType': 'ErrorResponseDto',
                    'payload': {
                        'detail': 'Cannot archive an ACTIVE price list.'
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        reason = request.data.get('reason')
        price_list.is_archived = True
        price_list.archive_reason = reason
        price_list.archivation_date = timezone.now()
        price_list.save()

        return JsonResponse(
            {
                'payloadType': 'StatusResponseDto',
                'payload': {
                    'status': 'OK',
                }
            },
            status=status.HTTP_200_OK
        )
