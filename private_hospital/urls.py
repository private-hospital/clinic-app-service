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
from private_hospital.settings import API_PUB
from rest_framework_simplejwt import views as jwt_views
from clinic_app_service.views import LoginView, PatientListView, PatientDetailView

urlpatterns = [
    path('admin/', admin.site.urls),
    path(f'{API_PUB}/health', views.health_check, name='service health'),
    path('api/token/', jwt_views.TokenObtainPairView.as_view(),  name='token_obtain_pair'),
    path('api/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path(f'{API_PUB}/login/', LoginView.as_view(), name='login'),
    path(f'{API_PUB}/registry/', PatientListView.as_view(), name='registry'),
path(f'{API_PUB}/patient/<int:id>/', PatientDetailView.as_view(), name='patient_detail'),
]