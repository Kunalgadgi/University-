from django import forms
from .models import PersonalDetail

class PersonalDetailForm(forms.ModelForm):
    """Form for personal details"""
    
    class Meta:
        model = PersonalDetail
        fields = [
            'photo',
            'first_name', 'last_name', 'father_name', 'mother_name',
            'date_of_birth', 'gender',
            'aadhar_number', 'category',
            'mobile_number', 'email', 'alternate_phone',
            'current_address', 'permanent_address', 'city', 'state', 'pincode', 'country',
            'nationality', 'marital_status',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'marital_status': forms.Select(attrs={'class': 'form-control'}),
            'current_address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'permanent_address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if field_name not in ['gender', 'marital_status', 'date_of_birth', 
                                 'current_address', 'permanent_address']:
                field.widget.attrs.update({'class': 'form-control'})
        
        # Add placeholders
        self.fields['first_name'].widget.attrs.update({'placeholder': 'Enter your first name'})
        self.fields['last_name'].widget.attrs.update({'placeholder': 'Enter your last name'})
        self.fields['mobile_number'].widget.attrs.update({'placeholder': 'Enter mobile number'})
        self.fields['email'].widget.attrs.update({'placeholder': 'Enter email address'})
        self.fields['alternate_phone'].widget.attrs.update({'placeholder': 'Enter alternate phone (optional)'})
        self.fields['city'].widget.attrs.update({'placeholder': 'Enter city'})
        self.fields['state'].widget.attrs.update({'placeholder': 'Enter state'})
        self.fields['pincode'].widget.attrs.update({'placeholder': 'Enter pincode'})
        self.fields['country'].widget.attrs.update({'placeholder': 'Enter country'})
        self.fields['nationality'].widget.attrs.update({'placeholder': 'Enter nationality'})
    
    def clean_mobile_number(self):
        """Validate mobile number"""
        mobile = self.cleaned_data.get('mobile_number')
        if mobile and not mobile.isdigit():
            raise forms.ValidationError('Mobile number should contain only digits.')
        if mobile and len(mobile) < 10:
            raise forms.ValidationError('Mobile number should be at least 10 digits.')
        return mobile
    
