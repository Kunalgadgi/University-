from django.urls import path
from . import views

app_name = 'personal_details'

urlpatterns = [
    path('', views.personal_details_view, name='personal_details'),
]
