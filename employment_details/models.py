from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class EmploymentDetail(models.Model):
    """
    Model to store employment details for PhD admission
    Based on the employment_details.html form structure
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='employment_details')
    sr_no = models.PositiveIntegerField(default=1)
    post_held = models.CharField(max_length=200, verbose_name="Name of Post Held")
    organization = models.CharField(max_length=300, verbose_name="Name of Organization")
    from_date = models.DateField(verbose_name="From Date")
    to_date = models.DateField(verbose_name="To Date")
    experience_years = models.PositiveIntegerField(default=0, verbose_name="Experience in Years")
    experience_months = models.PositiveIntegerField(default=0, verbose_name="Experience in Months")
    job_type = models.CharField(max_length=100, verbose_name="Type/Nature of Job")
    remarks = models.TextField(blank=True, null=True, verbose_name="Remarks")
    
    # Additional fields for tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Employment Detail"
        verbose_name_plural = "Employment Details"
        ordering = ['sr_no']
    
    def __str__(self):
        return f"{self.post_held} at {self.organization}"
    
    def save(self, *args, **kwargs):
        # Calculate experience when saving - but only if dates are valid
        try:
            if self.from_date and self.to_date:
                self.calculate_experience()
        except Exception:
            # If there's any error, set experience to 0 and continue
            self.experience_years = 0
            self.experience_months = 0
        super().save(*args, **kwargs)
    
    def calculate_experience(self):
        """Calculate years and months of experience"""
        if self.from_date and self.to_date:
            try:
                # Ensure dates are date objects, not strings
                from_date = self.from_date
                to_date = self.to_date
                
                # Convert string dates to date objects if needed
                if isinstance(from_date, str):
                    from_date = timezone.datetime.strptime(from_date, '%Y-%m-%d').date()
                if isinstance(to_date, str):
                    to_date = timezone.datetime.strptime(to_date, '%Y-%m-%d').date()
                
                years = to_date.year - from_date.year
                months = to_date.month - from_date.month
                
                if to_date.day < from_date.day:
                    months -= 1
                
                if months < 0:
                    years -= 1
                    months += 12
                
                self.experience_years = max(0, years)
                self.experience_months = max(0, months)
            except Exception:
                # If there's any error with date calculation, set to 0
                self.experience_years = 0
                self.experience_months = 0
    
    @property
    def formatted_experience(self):
        """Return formatted experience string"""
        parts = []
        if self.experience_years > 0:
            parts.append(f"{self.experience_years} {'Year' if self.experience_years == 1 else 'Years'}")
        if self.experience_months > 0:
            parts.append(f"{self.experience_months} {'Month' if self.experience_months == 1 else 'Months'}")
        return ' '.join(parts) if parts else '< 1 Month'
    
    @property
    def total_months(self):
        """Return total experience in months"""
        return (self.experience_years * 12) + self.experience_months
