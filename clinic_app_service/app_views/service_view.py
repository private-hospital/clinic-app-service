from math import ceil
from django.db.models import QuerySet
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView
from ..models import Service, PriceList, PriceListEntry, Appointment


class ServiceView(APIView):
    def get(self, request):
        page = int(request.query_params.get('p', 1))
        per_page = int(request.query_params.get('q', 10))

        queryset: QuerySet[Service] = Service.objects.all().order_by('service_name')

        total_count = queryset.count()
        start_index = (page - 1) * per_page
        end_index = start_index + per_page

        page_qs = queryset[start_index:end_index]

        active_pl = PriceList.objects.filter(status='ACTIVE', is_archived=False).first()

        data = []
        for service in page_qs:
            price = None
            if active_pl:
                entry = PriceListEntry.objects.filter(price_list=active_pl, service=service).first()
                if entry:
                    price = str(entry.price)

            appointment_count = Appointment.objects.filter(
                price_list_entry__service=service,
                execution_status='COMPLETED'
            ).count()

            data.append({
                'id': service.id,
                'title': service.service_name,
                'price': price,
                'count': appointment_count,
                'isArchived': service.is_service_archived,
            })

        return JsonResponse({
            'payloadType': 'ServicesRegistryDto',
            'payload': {
                'page': page,
                'perPage': per_page,
                'totalPages': ceil(total_count / per_page),
                'entries': data
            }
        }, status=status.HTTP_200_OK)

    def post(self, request):
        body = request.data
        service_name = body.get('serviceName')
        price = body.get('price')

        service = Service.objects.create(
            service_name=service_name,
            is_service_archived=False
        )

        active_pl = PriceList.objects.filter(status='ACTIVE', is_archived=False).first()

        if active_pl:
            PriceListEntry.objects.create(
                price_list=active_pl,
                service=service,
                price=price
            )
        else:
            pass

        return JsonResponse(
            {
                'payloadType': 'StatusResponseDto',
                'payload': {
                    'status': 'OK',
                }
            },
            status=status.HTTP_201_CREATED
        )

    def delete(self, request):
        service_id = request.query_params.get('id')

        try:
            service = Service.objects.get(pk=service_id)
        except Service.DoesNotExist:
            return JsonResponse(
                {
                    'payloadType': 'ErrorResponseDto',
                    'payload': {
                        'detail': f"Service with ID={service_id} does not exist."
                    },
                },
                status=status.HTTP_404_NOT_FOUND
            )

        service.is_service_archived = True
        service.save()

        return JsonResponse(
            {
                'payloadType': 'StatusResponseDto',
                'payload': {
                    'status': 'OK',
                }
            },
            status=status.HTTP_200_OK
        )

    def put(self, request):
        service_id = request.query_params.get('id')
        if not service_id:
            return JsonResponse(
                {
                    'payloadType': 'ErrorResponseDto',
                    'payload': {
                        'detail': "Missing 'id' query parameter."
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            service = Service.objects.get(pk=service_id)
        except Service.DoesNotExist:
            return JsonResponse(
                {
                    'payloadType': 'ErrorResponseDto',
                    'payload': {
                        'detail': f"Service with ID={service_id} does not exist."
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )

        service.is_service_archived = False
        service.save()

        active_pl = PriceList.objects.filter(status='ACTIVE', is_archived=False).first()
        if not active_pl:
            return JsonResponse(
                {
                    'payloadType': 'StatusResponseDto',
                    'payload': {
                        'status': 'OK'
                    }
                },
                status=status.HTTP_200_OK
            )

        existing_entry = PriceListEntry.objects.filter(
            price_list=active_pl,
            service=service
        ).first()

        if existing_entry:
            return JsonResponse(
                {
                    'payloadType': 'StatusResponseDto',
                    'payload': {
                        'status': 'OK'
                    }
                },
                status=status.HTTP_200_OK
            )

        recent_entry = PriceListEntry.objects.filter(service=service).order_by('-price_list__id').first()
        if not recent_entry:
            return JsonResponse(
                {
                    'payloadType': 'StatusResponseDto',
                    'payload': {
                        'status': 'OK',
                    }
                },
                status=status.HTTP_200_OK
            )

        PriceListEntry.objects.create(
            price_list=active_pl,
            service=service,
            price=recent_entry.price
        )

        return JsonResponse(
            {
                'payloadType': 'StatusResponseDto',
                'payload': {
                    'status': 'OK'
                }
            },
            status=status.HTTP_200_OK
        )

