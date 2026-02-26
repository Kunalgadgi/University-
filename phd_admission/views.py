from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import re
from datetime import datetime
from .models import UserProfile

def home(request):
    """Home page view"""
    return render(request, 'home.html')

def dashboard(request):
    """Dashboard page view"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Get real data for the dashboard
    from employment_details.models import EmploymentDetail
    from phd_academic_qualifications.models import AcademicQualification
    from .models import UserProfile
    
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get user's personal data (filtered by user)
    user_employment_count = EmploymentDetail.objects.filter(user=request.user).count()
    user_qualifications_count = AcademicQualification.objects.filter(user=request.user).count()
    user_applications_count = 0  # No university admission model yet
    
    # Get overall statistics
    total_users = User.objects.count()
    total_employment = EmploymentDetail.objects.count()
    total_qualifications = AcademicQualification.objects.count()
    total_applications = 0  # No university admission model yet
    
    context = {
        'user_employment_count': user_employment_count,
        'user_qualifications_count': user_qualifications_count,
        'user_applications_count': user_applications_count,
        'total_users': total_users,
        'total_employment': total_employment,
        'total_qualifications': total_qualifications,
        'total_applications': total_applications,
        'user': request.user,
        'profile': profile,
        'profile_completion': profile.completion_percentage,
    }
    
    return render(request, 'dashboard.html', context)

def login_view(request):
    """Login page view"""
    if request.method == 'POST':
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username_or_email or not password:
            messages.error(request, 'Both username/email and password are required')
            return render(request, 'login.html')
        
        # Try to find user by username first, then by email
        user = None
        try:
            # First try to authenticate with username
            user = authenticate(request, username=username_or_email, password=password)
        except:
            pass
        
        if user is None:
            # If username didn't work, try email
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        
        if user is not None:
            login(request, user)
            messages.success(request, 'Welcome back! You have successfully logged in.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username/email or password. Please try again.')
    
    return render(request, 'login.html')

def register_view(request):
    """Register page view"""
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        date_of_birth = request.POST.get('date_of_birth', '').strip()
        mobile_number = request.POST.get('mobile_number', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        terms = request.POST.get('terms', '')
        
        # Validation
        error_found = False
        
        if not name:
            messages.error(request, 'Full name is required')
            error_found = True
        elif len(name) < 3:
            messages.error(request, 'Name must be at least 3 characters long')
            error_found = True
        
        if not email:
            messages.error(request, 'Email address is required')
            error_found = True
        else:
            try:
                validate_email(email)
            except ValidationError:
                messages.error(request, 'Please enter a valid email address')
                error_found = True
        
        if not date_of_birth:
            messages.error(request, 'Date of birth is required')
            error_found = True
        else:
            try:
                birth_date = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
                today = datetime.now().date()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                if age < 16:
                    messages.error(request, 'You must be at least 16 years old')
                    error_found = True
                elif age > 100:
                    messages.error(request, 'Please enter a valid date of birth')
                    error_found = True
            except ValueError:
                messages.error(request, 'Please enter a valid date of birth')
                error_found = True
        
        if not mobile_number:
            messages.error(request, 'Mobile number is required')
            error_found = True
        elif not re.match(r'^[0-9]{10}$', mobile_number.replace(' ', '')):
            messages.error(request, 'Please enter a valid 10-digit mobile number')
            error_found = True
        
        if not password:
            messages.error(request, 'Password is required')
            error_found = True
        elif len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long')
            error_found = True
        
        if not confirm_password:
            messages.error(request, 'Please confirm your password')
            error_found = True
        elif password != confirm_password:
            messages.error(request, 'Passwords do not match')
            error_found = True
        
        if not terms:
            messages.error(request, 'You must agree to the terms and conditions')
            error_found = True
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists')
            error_found = True
        
        if not error_found:
            try:
                # Create username from email (before @)
                username = email.split('@')[0]
                
                # Ensure username is unique
                original_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1
                
                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=name
                )
                
                # Create user profile with registration data
                UserProfile.objects.create(
                    user=user,
                    mobile_number=mobile_number,
                    date_of_birth=datetime.strptime(date_of_birth, '%Y-%m-%d').date() if date_of_birth else None
                )
                
                messages.success(request, f'Account created successfully! You can now login.')
                return redirect('login')
                
            except Exception as e:
                messages.error(request, f'An error occurred while creating your account: {str(e)}')
        else:
            # If there are errors, redirect back to registration page
            return redirect('register')
    
    return render(request, 'register.html')

def logout_view(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')

@login_required
def profile_personal_info(request):
    """Personal Information Step"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update personal information
        request.user.first_name = request.POST.get('name', '').strip()
        request.user.email = request.POST.get('email', '').strip()
        request.user.save()
        
        profile.mobile_number = request.POST.get('mobile_number', '').strip()
        date_of_birth = request.POST.get('date_of_birth', '').strip()
        if date_of_birth:
            profile.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
        profile.gender = request.POST.get('gender', '')
        profile.marital_status = request.POST.get('marital_status', '')
        
        profile.is_personal_info_complete = True
        profile.profile_step = 2
        profile.save()
        
        messages.success(request, 'Personal information updated successfully!')
        return redirect('profile_qualification')
    
    context = {
        'profile': profile,
        'user': request.user,
    }
    return render(request, 'profile/personal_info.html', context)

@login_required
def profile_qualification(request):
    """Qualification Step - Redirect to existing academic qualifications form"""
    profile = UserProfile.objects.get(user=request.user)
    
    if not profile.is_personal_info_complete:
        return redirect('profile_personal_info')
    
    if request.method == 'POST':
        profile.is_qualification_complete = True
        profile.profile_step = 3
        profile.save()
        
        messages.success(request, 'Qualification information updated successfully!')
        return redirect('profile_employment')
    
    # Redirect to the existing academic qualifications form
    return redirect('phd_academic_qualifications:academic_qualifications')

@login_required
def complete_qualification_step(request):
    """Mark qualification step as complete and redirect to employment"""
    profile = UserProfile.objects.get(user=request.user)
    profile.is_qualification_complete = True
    profile.profile_step = 3
    profile.save()
    
    messages.success(request, 'Qualification information updated successfully!')
    return redirect('profile_employment')

@login_required
def debug_profile(request):
    """Debug view to check profile status"""
    from employment_details.models import EmploymentDetail
    from phd_academic_qualifications.models import AcademicQualification
    
    profile = UserProfile.objects.get(user=request.user)
    
    user_quals = AcademicQualification.objects.filter(user=request.user)
    user_emps = EmploymentDetail.objects.filter(user=request.user)
    
    context = {
        'profile': profile,
        'user_quals': user_quals,
        'user_emps': user_emps,
        'completion_percentage': profile.completion_percentage,
    }
    
    return render(request, 'debug_profile.html', context)

@login_required
def complete_employment_step(request):
    """Mark employment step as complete and redirect to dashboard"""
    profile = UserProfile.objects.get(user=request.user)
    profile.is_employment_complete = True
    profile.profile_step = 4  # Complete
    profile.save()
    
    messages.success(request, 'Employment information updated successfully! Profile complete.')
    return redirect('dashboard')
