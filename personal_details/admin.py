from django.contrib import admin
from .models import PersonalDetail

@admin.register(PersonalDetail)
class PersonalDetailAdmin(admin.ModelAdmin):
    """Admin configuration for PersonalDetail model"""
    
    list_display = [
        'full_name', 'user', 'email', 'mobile_number', 'gender', 'category', 'state', 'created_at'
    ]
    
    list_filter = [
        'gender', 'marital_status', 
        'nationality', 'created_at'
    ]
    
    search_fields = [
        'first_name', 'last_name', 'user__username', 
        'email', 'mobile_number', 'city'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'user', 'photo',
                'first_name', 'last_name', 'father_name', 'mother_name',
                'date_of_birth', 'gender', 'marital_status',
                'nationality', 'category', 'aadhar_number',
            )
        }),
        ('Contact Information', {
            'fields': ('mobile_number', 'alternate_phone', 'email')
        }),
        ('Address Information', {
            'fields': ('current_address', 'permanent_address', 
                      'city', 'state', 'pincode', 'country')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Full Name'
