from django.contrib import admin
from .models import EmploymentDetail

@admin.register(EmploymentDetail)
class EmploymentDetailAdmin(admin.ModelAdmin):
    list_display = [
        'sr_no', 'post_held', 'organization', 'from_date', 'to_date', 
        'formatted_experience', 'job_type'
    ]
    list_filter = ['job_type', 'from_date', 'to_date', 'created_at']
    search_fields = ['post_held', 'organization', 'job_type', 'remarks']
    list_editable = ['job_type']
    list_display_links = ['sr_no', 'post_held']
    ordering = ['sr_no', 'from_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('sr_no', 'post_held', 'organization', 'job_type')
        }),
        ('Employment Period', {
            'fields': ('from_date', 'to_date')
        }),
        ('Experience Details', {
            'fields': ('experience_years', 'experience_months'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('remarks',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ['experience_years', 'experience_months']
        return self.readonly_fields
