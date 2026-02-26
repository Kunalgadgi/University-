from django.contrib import admin
from .models import AcademicQualification

@admin.register(AcademicQualification)
class AcademicQualificationAdmin(admin.ModelAdmin):
    list_display = [
        'examination_name', 'university_board', 'year_of_passing', 
        'roll_number', 'result_display', 'subjects'
    ]
    list_filter = [
        'examination_passed', 'year_of_passing', 'created_at'
    ]
    search_fields = [
        'examination_passed', 'custom_examination', 'university_board', 
        'roll_number', 'subjects'
    ]
    ordering = ['-year_of_passing', 'examination_passed']
    
    fieldsets = (
        ('Examination Details', {
            'fields': (
                'examination_passed', 'custom_examination', 
                'university_board', 'year_of_passing', 'roll_number'
            )
        }),
        ('Results - Grade OR Marks', {
            'fields': ('grade', 'marks_obtained', 'max_marks', 'percentage'),
            'description': 'Enter either Grade OR both Marks Obtained and Maximum Marks'
        }),
        ('Subjects', {
            'fields': ('subjects',)
        }),
    )
    
    readonly_fields = ['percentage', 'created_at', 'updated_at']
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields
        return ['percentage']  # percentage is always calculated
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'custom_examination' in form.base_fields:
            form.base_fields['custom_examination'].required = False
        return form
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
