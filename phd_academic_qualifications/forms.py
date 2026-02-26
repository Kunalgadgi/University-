from django import forms
from .models import AcademicQualification

class AcademicQualificationForm(forms.ModelForm):
    class Meta:
        model = AcademicQualification
        fields = [
            'examination_passed', 'custom_examination', 'university_board',
            'year_of_passing', 'roll_number', 'grade', 'marks_obtained',
            'max_marks', 'subjects'
        ]
        widgets = {
            'examination_passed': forms.Select(attrs={'class': 'form-control'}),
            'custom_examination': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter custom examination name'}),
            'university_board': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CBLU, Haryana'}),
            'year_of_passing': forms.NumberInput(attrs={'class': 'form-control', 'min': '1950', 'max': '2050'}),
            'roll_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Roll No.'}),
            'grade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'A / A+ / O / Distinction'}),
            'marks_obtained': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Obtained'}),
            'max_marks': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Max'}),
            'subjects': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Physics, Chemistry'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['examination_passed'].label = 'Examination Passed'
        self.fields['custom_examination'].label = 'Custom Examination Name'
        self.fields['university_board'].label = 'Name of University / Board'
        self.fields['year_of_passing'].label = 'Year of Passing'
        self.fields['roll_number'].label = 'Roll No.'
        self.fields['grade'].label = 'Grade'
        self.fields['marks_obtained'].label = 'Marks Obtained'
        self.fields['max_marks'].label = 'Maximum Marks'
        self.fields['subjects'].label = 'Subjects'
        
        # Set required fields
        for field in self.fields.values():
            if field.name in ['examination_passed', 'university_board', 'year_of_passing', 'roll_number', 'subjects']:
                field.required = True
            else:
                field.required = False
    
    def clean(self):
        cleaned_data = super().clean()
        examination = cleaned_data.get('examination_passed')
        custom_examination = cleaned_data.get('custom_examination')
        grade = cleaned_data.get('grade')
        marks_obtained = cleaned_data.get('marks_obtained')
        max_marks = cleaned_data.get('max_marks')
        
        # Require custom examination if "other" is selected
        if examination == 'other' and not custom_examination:
            raise forms.ValidationError('Custom examination name is required when "Any Other Qualification" is selected.')
        
        # Require either grade OR both marks
        has_grade = grade and grade.strip()
        has_marks = marks_obtained is not None and max_marks is not None
        
        if not has_grade and not has_marks:
            raise forms.ValidationError('Either Grade OR both Marks Obtained and Maximum Marks must be provided.')
        
        if has_marks and max_marks and max_marks <= 0:
            raise forms.ValidationError('Maximum marks must be greater than 0.')
        
        if has_marks and marks_obtained and max_marks and marks_obtained > max_marks:
            raise forms.ValidationError('Marks obtained cannot be greater than maximum marks.')
        
        return cleaned_data
