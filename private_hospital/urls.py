"""
URL configuration for private_hospital project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from clinic_app_service import views
from clinic_app_service.app_views.appointments_view import AppointmentsView
from clinic_app_service.app_views.available_doctors_view import AvailableDoctorsView
from clinic_app_service.app_views.available_times_view import AvailableTimesView
from clinic_app_service.app_views.calculate_totals_view import CalculateTotalsView
from clinic_app_service.app_views.cart_calculation_view import CartCalculationView
from clinic_app_service.app_views.check_service_exists_view import CheckServiceExistsView
from clinic_app_service.app_views.create_appointment_view import CreateAppointmentView
from clinic_app_service.app_views.dynamic_invoice_view import DynamicInvoiceView
from clinic_app_service.app_views.email_verification_view import SendVerificationCodeView, VerifyEmailView
from clinic_app_service.app_views.get_patient_discount_view import GetPatientDiscountView
from clinic_app_service.app_views.medical_records_view import MedicalRecordsView
from clinic_app_service.app_views.patient_appointments_view import PatientAppointmentsView
from clinic_app_service.app_views.price_lists_view import PriceListsView
from clinic_app_service.app_views.active_price_list_view import ActivePriceListView
from clinic_app_service.app_views.remove_verification_code_view import RemoveVerificationCodeView
from clinic_app_service.app_views.service_names_view import ServiceNamesView
from clinic_app_service.app_views.service_view import ServiceView
from clinic_app_service.app_views.statement_pdf_view import StatementPdfView
from clinic_app_service.app_views.statements_registry_view import StatementsRegistryView
from clinic_app_service.app_views.invoice_pdf_view import InvoicePdfView
from clinic_app_service.app_views.statistics_view import WeeklyStatsView, TodayCumulateView, DoctorsView, \
    DoctorDailyCountsView, DoctorDailyRevenuesView
from private_hospital.settings import API_PUB, API_OWN, API_DOC, API_REG
from rest_framework_simplejwt import views as jwt_views
from clinic_app_service.views import LoginView, PatientListView, PatientDetailView, create_patient, update_patient, \
    get_patient

urlpatterns = [
    path('admin/', admin.site.urls),
    path(f'{API_PUB}/health', views.health_check, name='service health'),
    path('api/token/', jwt_views.TokenObtainPairView.as_view(),  name='token_obtain_pair'),
    path('api/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path(f'{API_PUB}/login/', LoginView.as_view(), name='login'),
    path(f'{API_PUB}/registry/', PatientListView.as_view(), name='registry'),
    path(f'{API_PUB}/patient/<int:id>/', PatientDetailView.as_view(), name='patient_detail'),
    path(f'{API_PUB}/patients', create_patient, name='create_patient'),
    path(f'{API_OWN}/price-lists', PriceListsView.as_view(), name='price-lists-crud'),
    path(f'{API_OWN}/price-lists/active', ActivePriceListView.as_view(), name='active-price-list-ops'),
    path(f'{API_OWN}/services', ServiceView.as_view(), name='services-ops'),
    path(f'{API_OWN}/stats/week', WeeklyStatsView.as_view(), name='weekly-general-stats'),
    path(f'{API_OWN}/stats/cumulate', TodayCumulateView.as_view(), name='todays-visits-cumulate'),
    path(f'{API_OWN}/stats/doctor/counts', DoctorDailyCountsView.as_view(), name='doctor-weekly-count-stats'),
    path(f'{API_OWN}/stats/doctor/revenue', DoctorDailyRevenuesView.as_view(), name='doctor-weekly-revenue-stats'),
    path(f'{API_PUB}/doctors', DoctorsView.as_view(), name='doctors-get-public-api'),
    path(f'{API_PUB}/services/names', ServiceNamesView.as_view(), name='service-names-for-filter'),
    path(f'{API_OWN}/statements', StatementsRegistryView.as_view(), name='statements-view'),
    path(f'{API_OWN}/statements/export', StatementPdfView.as_view(), name='statement-pdf-export'),
    path(f'{API_OWN}/invoices/export', InvoicePdfView.as_view(), name='invoice-pdf-export'),
    path(f'{API_DOC}/appointments', AppointmentsView.as_view(), name='appointments-doctor-operations'),
    path(f'{API_DOC}/records', MedicalRecordsView.as_view(), name='medical-records-ops'),
    path(f'{API_REG}/patient-appointments/', PatientAppointmentsView.as_view(), name='patient-appointments-ops'),
    path(f'{API_REG}/available-doctors', AvailableDoctorsView.as_view(), name='available-doctors-view'),
    path(f'{API_REG}/available-times', AvailableTimesView.as_view(), name='available-times-view'),
    path(f'{API_REG}/create-appointments', CreateAppointmentView.as_view(), name='create-appointments-view'),
    path(f'{API_REG}/calculate-cart', CartCalculationView.as_view(), name='cart-calculation-view'),
    path(f'{API_REG}/calculate-totals', CalculateTotalsView.as_view(), name='calculate-totals-view'),
    path(f'{API_REG}/get-patient-discount', GetPatientDiscountView.as_view(), name='get-patient-discount-view'),
    path(f'{API_REG}/export-invoice', DynamicInvoiceView.as_view(), name='export-dynamic-invoice'),
    path(f'{API_PUB}/doctors', DoctorsView.as_view(), name='doctors-get-public-api'),
    path(f'{API_PUB}/patient/<int:pk>', update_patient, name='update-patient'),
    path(f'{API_PUB}/patient/<int:pk>', get_patient, name='get-patient'),
    path(f'{API_PUB}/send-verification', SendVerificationCodeView.as_view(), name='send-email-verification-view'),
    path(f'{API_PUB}/remove-verification', RemoveVerificationCodeView.as_view(), name='remove-email-verification-view'),
    path(f'{API_PUB}/verify', VerifyEmailView.as_view(), name='verify-email-view'),
    path(f'{API_OWN}/service-exists', CheckServiceExistsView.as_view(), name='check-if-service-exists')
]