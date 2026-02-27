from django.db import models
from django.contrib.auth.models import User

class PersonalDetail(models.Model):
    """Personal details model for user profile information"""
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    
    MARITAL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='personal_detail')
    
    # Photo
    photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    
    # Basic Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True, null=True)
    
    # Contact Information
    mobile_number = models.CharField(max_length=15)
    email = models.EmailField()
    alternate_email = models.EmailField(blank=True, null=True)
    
    # Address Information
    current_address = models.TextField()
    permanent_address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    country = models.CharField(max_length=100, default='India')
    
    # Additional Information
    nationality = models.CharField(max_length=100, default='Indian')
    marital_status = models.CharField(max_length=10, choices=MARITAL_STATUS_CHOICES)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_number = models.CharField(max_length=15)
    emergency_contact_relation = models.CharField(max_length=50)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Personal Detail"
        verbose_name_plural = "Personal Details"
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.user.username}"
    
    @property
    def full_name(self):
        """Get full name"""
        return f"{self.first_name} {self.last_name}"
