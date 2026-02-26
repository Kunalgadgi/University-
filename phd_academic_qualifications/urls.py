from django.urls import path
from . import views

app_name = 'phd_academic_qualifications'

urlpatterns = [
    path('', views.phd_academic_qualifications, name='academic_qualifications'),
    path('submit/', views.submit_qualification_data, name='submit_qualification_data'),
    # Keep the old URLs for admin functionality
    path('list/', views.qualification_list, name='qualification_list'),
    path('add/', views.qualification_add, name='qualification_add'),
    path('edit/<int:pk>/', views.qualification_edit, name='qualification_edit'),
    path('delete/<int:pk>/', views.qualification_delete, name='qualification_delete'),
]
