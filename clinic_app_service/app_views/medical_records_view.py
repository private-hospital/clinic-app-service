from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status
from django.utils import timezone
import os
import boto3
import uuid

from ..models import MedicalRecord, Patient, Service


class MedicalRecordsView(APIView):
    def get(self, request):
        patient_id = request.query_params.get('patientId')
        if not patient_id:
            return JsonResponse(
                {
                    "payloadType": "ErrorResponseDto",
                    "payload": {
                        "detail": "Missing 'patientId' query parameter."
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            patient = Patient.objects.get(pk=patient_id)
        except Patient.DoesNotExist:
            return JsonResponse(
                {
                    "payloadType": "ErrorResponseDto",
                    "payload": {
                        "detail": f"Patient with id={patient_id} does not exist."
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )

        records_qs = MedicalRecord.objects.select_related('patient').filter(patient=patient).order_by('-id')

        entries = []
        for record in records_qs:
            record_type = record.record_type
            date_ts = int(record.created_at.timestamp() * 1000)

            title_str = record.title

            diagnosis_val = None
            analysis_results_val = None
            examinations_val = None

            if record_type == 'DIAGNOSIS':
                diagnosis_val = record.doctor_conclusion

            elif record_type == 'ANALYSIS_RESULTS':
                analysis_results_val = record.pdf_links

            elif record_type == 'NECESSARY_EXAMINATIONS':
                service_names = list(record.services.values_list('service_name', flat=True))
                examinations_val = service_names

            record_dto = {
                "title": title_str,
                "type": record_type,
                "date": date_ts
            }
            if diagnosis_val is not None:
                record_dto["diagnosis"] = diagnosis_val
            if analysis_results_val is not None:
                record_dto["analysisResults"] = analysis_results_val
            if examinations_val is not None:
                record_dto["examinations"] = examinations_val

            entries.append(record_dto)

        return JsonResponse(
            {
                "payloadType": "MedicalCardDto",
                "payload": {
                    "entries": entries
                }
            },
            status=status.HTTP_200_OK
        )

    def post(self, request):
        patient_id = request.GET.get('patientId')
        if not patient_id:
            return JsonResponse({
                'payloadType': 'ErrorResponseDto',
                'payload': {
                    "detail": "Missing 'patientId' query parameter."
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            patient = Patient.objects.get(pk=patient_id)
        except Patient.DoesNotExist:
            return JsonResponse({
                'payloadType': 'ErrorResponseDto',
                'payload': {
                    "detail": f"Patient with id={patient_id} does not exist."
                }
            }, status=status.HTTP_404_NOT_FOUND)

        title = request.data.get('title')
        record_type = request.data.get('type')
        diagnosis = request.data.get('diagnosis')
        examinations = request.data.getlist('examinations', [])
        analysis_files = request.FILES.getlist('analysisResults')

        if not title or not record_type:
            return JsonResponse({
                'payloadType': 'ErrorResponseDto',
                'payload': {
                    "detail": "Missing required fields 'title' or 'type'."
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        if record_type == 'DIAGNOSIS' and not (diagnosis and diagnosis.strip()):
            return JsonResponse({
                'payloadType': 'ErrorResponseDto',
                'payload': {
                    "detail": "Missing diagnosis"
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        if record_type == 'ANALYSIS_RESULTS':
            if not analysis_files or len(analysis_files) == 0:
                return JsonResponse({
                    'payloadType': 'ErrorResponseDto',
                    'payload': {
                        "detail": "No analysis files provided"
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            if len(analysis_files) > 5:
                return JsonResponse({
                    'payloadType': 'ErrorResponseDto',
                    'payload': {
                        "detail": "Too many files"
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

        if record_type == 'NECESSARY_EXAMINATIONS':
            if not examinations:
                return JsonResponse({
                    'payloadType': 'ErrorResponseDto',
                    'payload': {
                        "detail": "No neccessary examinations provided"
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

        new_record = MedicalRecord.objects.create(
            title=title,
            patient=patient,
            record_type=record_type,
            created_at=timezone.now()
        )

        if record_type == 'DIAGNOSIS':
            new_record.doctor_conclusion = diagnosis

        if record_type == 'NECESSARY_EXAMINATIONS':
            matched_services = Service.objects.filter(service_name__in=examinations)
            new_record.save()
            new_record.services.set(matched_services)

        if record_type == 'ANALYSIS_RESULTS' and analysis_files:
            s3_links = []
            s3 = boto3.client(
                's3',
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            )
            bucket_name = 'private-hospital-public'

            for f in analysis_files:
                key = f"analysis-results/patient-{patient_id}/{uuid.uuid4()}.pdf"

                s3.upload_fileobj(
                    f,
                    bucket_name,
                    key,
                    ExtraArgs={'ContentType': 'application/pdf'}
                )

                file_url = f"https://cdn.vitalineph.com/{key}"
                s3_links.append(file_url)

            new_record.pdf_links = s3_links

        new_record.save()

        return JsonResponse(
            {
                "payloadType": "StatusResponseDto",
                "payload": {
                    "status": f"New medical record (type={record_type}) created for patient {patient_id}."
                }
            },
            status=status.HTTP_201_CREATED
        )
