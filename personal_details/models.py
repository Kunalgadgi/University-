from django.db import models
from django.contrib.auth.models import User


class PersonalDetail(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    MARITAL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='personal_detail')

    photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    signature = models.ImageField(upload_to='signatures/', blank=True, null=True)

    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    father_name = models.CharField(max_length=100, blank=True, null=True)
    mother_name = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)

    aadhar_number = models.CharField(max_length=12, blank=True, null=True)
    category = models.CharField(max_length=50, default='General', blank=True, null=True)

    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    alternate_phone = models.CharField(max_length=15, blank=True, null=True)

    current_address = models.TextField(blank=True, null=True)
    permanent_address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=100, default='India', blank=True, null=True)

    nationality = models.CharField(max_length=100, default='Indian', blank=True, null=True)
    marital_status = models.CharField(max_length=10, choices=MARITAL_STATUS_CHOICES, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Personal Detail'
        verbose_name_plural = 'Personal Details'

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.user.username}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
