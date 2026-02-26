from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    """Extended user profile model"""
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    MARITAL_STATUS_CHOICES = [
        ('S', 'Single'),
        ('M', 'Married'),
        ('D', 'Divorced'),
        ('W', 'Widowed'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    marital_status = models.CharField(max_length=1, choices=MARITAL_STATUS_CHOICES, blank=True, null=True)
    
    # Profile completion tracking
    profile_step = models.PositiveIntegerField(default=1)  # 1: Personal Info, 2: Qualification, 3: Employment
    is_personal_info_complete = models.BooleanField(default=False)
    is_qualification_complete = models.BooleanField(default=False)
    is_employment_complete = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    @property
    def completion_percentage(self):
        """Calculate profile completion percentage"""
        completed_steps = 0
        if self.is_personal_info_complete:
            completed_steps += 1
        if self.is_qualification_complete:
            completed_steps += 1
        if self.is_employment_complete:
            completed_steps += 1
        return int((completed_steps / 3) * 100)
    
    def get_gender_display(self):
        """Get gender display text"""
        return dict(self.GENDER_CHOICES).get(self.gender, '')
    
    def get_marital_status_display(self):
        """Get marital status display text"""
        return dict(self.MARITAL_STATUS_CHOICES).get(self.marital_status, '')
