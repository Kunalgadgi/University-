"""
Master Control URL Configuration
"""
from django.urls import path
from . import views

app_name = "master_control"

urlpatterns = [
    # Dashboard
    path("", views.dashboard, name="dashboard"),
    path("dashboard/", views.dashboard, name="dashboard_alt"),
    
    # Custom Forms
    path("add/course/", views.add_course, name="add_course"),
    path("add/advertisement/", views.add_advertisement, name="add_advertisement"),
    path("add/notice/", views.add_notice, name="add_notice"),
    
    # Reports
    path("reports/departments/", views.department_report, name="department_report"),
    path("system/health/", views.system_health, name="system_health"),
]
