from django import forms
from .models import EmploymentDetail

class EmploymentDetailForm(forms.ModelForm):
    class Meta:
        model = EmploymentDetail
        fields = [
            'sr_no', 'post_held', 'organization', 'from_date', 'to_date',
            'job_type', 'remarks'
        ]
        widgets = {
            'sr_no': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'post_held': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Assistant Professor'}),
            'organization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CBLU, Bhiwani'}),
            'from_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'to_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'job_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Teaching / Permanent'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional remarks'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sr_no'].label = 'Sr. No.'
        self.fields['post_held'].label = 'Name of Post Held'
        self.fields['organization'].label = 'Name of Organization'
        self.fields['from_date'].label = 'From Date'
        self.fields['to_date'].label = 'To Date'
        self.fields['job_type'].label = 'Type/Nature of Job'
        self.fields['remarks'].label = 'Remarks'
        
        for field in self.fields.values():
            field.required = field.name in ['post_held', 'organization', 'from_date', 'to_date', 'job_type']
    
    def clean(self):
        cleaned_data = super().clean()
        from_date = cleaned_data.get('from_date')
        to_date = cleaned_data.get('to_date')
        
        if from_date and to_date:
            if to_date < from_date:
                raise forms.ValidationError('"To" date must be after "From" date.')
        
        return cleaned_data
