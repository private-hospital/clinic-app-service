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
from clinic_app_service.app_views.price_lists_view import PriceListsView

from clinic_app_service.app_views.active_price_list_view import ActivePriceListView
from clinic_app_service.app_views.service_view import ServiceView
from private_hospital.settings import API_PUB, API_OWN
from rest_framework_simplejwt import views as jwt_views
from clinic_app_service.views import LoginView, PatientListView, PatientDetailView, create_patient

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
    path(f'{API_OWN}/services', ServiceView.as_view(), name='services-ops')
]