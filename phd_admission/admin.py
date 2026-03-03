from django.contrib import admin
from .models import UserProfile

# @admin.register(UserProfile)
# class UserProfileAdmin(admin.ModelAdmin):
#     list_display = ('user', 'get_email', 'mobile_number', 'date_of_birth', 'is_personal_info_complete', 'is_qualification_complete', 'is_employment_complete', 'profile_step')
#     list_filter = ('is_personal_info_complete', 'is_qualification_complete', 'is_employment_complete', 'profile_step')
#     search_fields = ('user__username', 'user__email', 'mobile_number')
#     readonly_fields = ('user', 'created_at', 'updated_at')
    
#     fieldsets = (
#         ('User Information', {
#             'fields': ('user', 'email', 'mobile_number', 'date_of_birth')
#         }),
#         ('Profile Completion', {
#             'fields': ('is_personal_info_complete', 'is_qualification_complete', 'is_employment_complete', 'profile_step')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )
    
#     def get_email(self, obj):
#         return obj.user.email if obj.user else obj.email
#     get_email.short_description = 'Email'
    
#     def get_queryset(self, request):
#         return super().get_queryset(request).select_related('user')
