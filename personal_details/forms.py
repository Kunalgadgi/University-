from django import forms
from .models import PersonalDetail

class PersonalDetailForm(forms.ModelForm):
    """Form for personal details"""
    
    class Meta:
        model = PersonalDetail
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender', 'blood_group',
            'mobile_number', 'email', 'alternate_email',
            'current_address', 'permanent_address', 'city', 'state', 'pincode', 'country',
            'nationality', 'marital_status',
            'emergency_contact_name', 'emergency_contact_number', 'emergency_contact_relation'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'blood_group': forms.Select(attrs={'class': 'form-control'}),
            'marital_status': forms.Select(attrs={'class': 'form-control'}),
            'current_address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'permanent_address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if field_name not in ['gender', 'blood_group', 'marital_status', 'date_of_birth', 
                                 'current_address', 'permanent_address']:
                field.widget.attrs.update({'class': 'form-control'})
        
        # Add placeholders
        self.fields['first_name'].widget.attrs.update({'placeholder': 'Enter your first name'})
        self.fields['last_name'].widget.attrs.update({'placeholder': 'Enter your last name'})
        self.fields['mobile_number'].widget.attrs.update({'placeholder': 'Enter mobile number'})
        self.fields['email'].widget.attrs.update({'placeholder': 'Enter email address'})
        self.fields['alternate_email'].widget.attrs.update({'placeholder': 'Enter alternate email (optional)'})
        self.fields['city'].widget.attrs.update({'placeholder': 'Enter city'})
        self.fields['state'].widget.attrs.update({'placeholder': 'Enter state'})
        self.fields['pincode'].widget.attrs.update({'placeholder': 'Enter pincode'})
        self.fields['country'].widget.attrs.update({'placeholder': 'Enter country'})
        self.fields['nationality'].widget.attrs.update({'placeholder': 'Enter nationality'})
        self.fields['emergency_contact_name'].widget.attrs.update({'placeholder': 'Enter emergency contact name'})
        self.fields['emergency_contact_number'].widget.attrs.update({'placeholder': 'Enter emergency contact number'})
        self.fields['emergency_contact_relation'].widget.attrs.update({'placeholder': 'Enter relationship'})
    
    def clean_mobile_number(self):
        """Validate mobile number"""
        mobile = self.cleaned_data.get('mobile_number')
        if mobile and not mobile.isdigit():
            raise forms.ValidationError('Mobile number should contain only digits.')
        if mobile and len(mobile) < 10:
            raise forms.ValidationError('Mobile number should be at least 10 digits.')
        return mobile
    
    def clean_emergency_contact_number(self):
        """Validate emergency contact number"""
        emergency_mobile = self.cleaned_data.get('emergency_contact_number')
        if emergency_mobile and not emergency_mobile.isdigit():
            raise forms.ValidationError('Emergency contact number should contain only digits.')
        if emergency_mobile and len(emergency_mobile) < 10:
            raise forms.ValidationError('Emergency contact number should be at least 10 digits.')
        return emergency_mobile
