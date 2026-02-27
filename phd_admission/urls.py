"""
URL configuration for phd_admission project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin/login/', views.admin_login_view, name='admin_login'),
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admission-form/', views.admission_form_single, name='admission_form_single'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_personal_info, name='profile_personal_info'),
    path('profile/qualification/', views.profile_qualification, name='profile_qualification'),
    path('profile/employment/', views.profile_employment, name='profile_employment'),
    path('profile/complete-qualification/', views.complete_qualification_step, name='complete_qualification'),
    path('profile/complete-employment/', views.complete_employment_step, name='complete_employment'),
    path('personal-details/', include('personal_details.urls')),
    path('debug/', views.debug_profile, name='debug_profile'),
    path('employment/', include('employment_details.urls')),
    path('qualifications/', include('phd_academic_qualifications.urls')),
    path('personal/', include(('personal_details.urls', 'personal_details'), namespace='personal_details_legacy')),
    path('apply/', views.apply_now, name='apply_now'),
    path('apply/create/', views.create_application, name='create_application'),
    path('application_preview/', views.application_preview, name='application_preview'),
    path('print_application/', views.print_application, name='print_application'),
    path('application_single_table/', views.application_single_table, name='application_single_table'),
    path('unified_application/', views.unified_application_view, name='unified_application'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
