from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class AcademicQualification(models.Model):
    """
    Model to store academic qualifications for PhD admission
    Based on the phd_academic_qualifications.html form structure
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='academic_qualifications')
    
    # Fixed examination types from the HTML form
    EXAM_TYPES = [
        ('matric', 'Matric'),
        ('10+2', '10+2'),
        ('bachelor', 'Bachelor Degree'),
        ('master', 'Master Degree'),
        ('mphil', 'M.Phil.'),
        ('net_jrf_gate_gpat', 'NET/JRF/GATE/GPAT'),
        ('fellowship', 'Any Other Fellowship'),
        ('other', 'Any Other Qualification'),
    ]
    
    examination_passed = models.CharField(
        max_length=50, 
        choices=EXAM_TYPES,
        verbose_name="Examination Passed"
    )
    custom_examination = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name="Custom Examination Name"
    )
    university_board = models.CharField(
        max_length=300, 
        verbose_name="Name of University / Board"
    )
    year_of_passing = models.PositiveIntegerField(
        verbose_name="Year of Passing",
        validators=[MinValueValidator(1950), MaxValueValidator(2050)]
    )
    roll_number = models.CharField(
        max_length=50, 
        verbose_name="Roll No."
    )
    
    # Grade system
    grade = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name="Grade"
    )
    
    # Marks system
    marks_obtained = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Marks Obtained"
    )
    max_marks = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Maximum Marks"
    )
    
    # Auto-calculated percentage
    percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Percentage of Marks"
    )
    
    subjects = models.CharField(
        max_length=500, 
        verbose_name="Subjects"
    )
    
    # Additional fields for tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Academic Qualification"
        verbose_name_plural = "Academic Qualifications"
        ordering = ['-year_of_passing']
    
    def __str__(self):
        exam_name = self.get_examination_display()
        if self.examination_passed == 'other' and self.custom_examination:
            exam_name = self.custom_examination
        return f"{exam_name} - {self.university_board} ({self.year_of_passing})"
    
    def save(self, *args, **kwargs):
        # Calculate percentage when saving if marks are provided
        if self.marks_obtained and self.max_marks and self.max_marks > 0:
            self.calculate_percentage()
        super().save(*args, **kwargs)
    
    def calculate_percentage(self):
        """Calculate percentage from marks"""
        if self.marks_obtained and self.max_marks and self.max_marks > 0:
            self.percentage = (self.marks_obtained / self.max_marks) * 100
        else:
            self.percentage = None
    
    @property
    def examination_name(self):
        """Get the actual examination name"""
        if self.examination_passed == 'other' and self.custom_examination:
            return self.custom_examination
        return self.get_examination_display()
    
    @property
    def has_grade(self):
        """Check if grade is provided"""
        return bool(self.grade and self.grade.strip())
    
    @property
    def has_marks(self):
        """Check if marks are provided"""
        return bool(self.marks_obtained is not None and self.max_marks is not None)
    
    @property
    def result_display(self):
        """Get formatted result (grade or percentage)"""
        if self.has_grade:
            return f"Grade: {self.grade}"
        elif self.has_marks and self.percentage is not None:
            return f"{self.percentage:.2f}%"
        elif self.has_marks:
            return f"{self.marks_obtained}/{self.max_marks}"
        else:
            return "N/A"
