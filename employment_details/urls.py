from django.urls import path
from . import views

app_name = 'employment_details'

urlpatterns = [
    path('', views.employment_details, name='employment_details'),
    path('submit/', views.submit_employment_data, name='submit_employment_data'),
    # Keep the old URLs for admin functionality
    path('list/', views.employment_list, name='employment_list'),
    path('add/', views.employment_add, name='employment_add'),
    path('edit/<int:pk>/', views.employment_edit, name='employment_edit'),
    path('delete/<int:pk>/', views.employment_delete, name='employment_delete'),
]
