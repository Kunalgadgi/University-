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
from personal_details.models import PersonalDetail
from personal_details.forms import PersonalDetailForm

def home(request):
    """Home page view"""
    return render(request, 'home.html')

def admin_login_view(request):
    """Admin login view - only for staff users"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_staff:
                login(request, user)
                messages.success(request, 'Admin login successful!')
                return redirect('/admin/')
            else:
                messages.error(request, 'Access denied. This login is for admin users only.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'admin_login.html')

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
        mobile_number = request.POST.get('mobile_number', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        
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
                
                # Create user profile with registration data (without date_of_birth)
                UserProfile.objects.create(
                    user=user,
                    mobile_number=mobile_number
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
    from personal_details.models import PersonalDetail
    
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    personal_detail, created = PersonalDetail.objects.get_or_create(
        user=request.user,
        defaults={
            'first_name': request.user.first_name or '',
            'last_name': request.user.last_name or '',
            'email': request.user.email or '',  # From registration
            'mobile_number': profile.mobile_number or '',  # From registration
            'date_of_birth': profile.date_of_birth or datetime(1990, 1, 1).date(),  # From registration if available
        }
    )
    
    if request.method == 'POST':
        # Delegate POST handling to the dedicated personal_details_view
        from personal_details.views import personal_details_view as dedicated_personal_details_view
        return dedicated_personal_details_view(request)
    
    context = {
        'profile': profile,
        'user': request.user,
        'personal_detail': personal_detail,
    }
    return render(request, 'profile/personal_info.html', context)

@login_required
def profile_qualification(request):
    """Qualification Step - Redirect to academic qualifications form"""
    from personal_details.models import PersonalDetail
    
    profile = UserProfile.objects.get(user=request.user)
    
    # Check if personal info is complete
    if not profile.is_personal_info_complete:
        messages.warning(request, 'Please complete your personal information first.')
        return redirect('profile_personal_info')
    
    # Check if personal details exist
    try:
        personal_detail = PersonalDetail.objects.get(user=request.user)
        if not personal_detail.first_name or not personal_detail.email:
            messages.warning(request, 'Please complete your personal information first.')
            return redirect('profile_personal_info')
    except PersonalDetail.DoesNotExist:
        messages.warning(request, 'Please complete your personal information first.')
        return redirect('profile_personal_info')
    
    if request.method == 'POST':
        profile.is_qualification_complete = True
        profile.profile_step = 3
        profile.save()
        
        messages.success(request, 'Moving to employment details!')
        return redirect('profile_employment')
    
    # Redirect to academic qualifications form
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
def profile_employment(request):
    """Employment Step - Conditional based on qualifications"""
    from personal_details.models import PersonalDetail
    from phd_academic_qualifications.models import AcademicQualification
    
    profile = UserProfile.objects.get(user=request.user)
    
    # Check if personal info is complete
    if not profile.is_personal_info_complete:
        messages.warning(request, 'Please complete your personal information first.')
        return redirect('profile_personal_info')
    
    # Check if qualifications are complete
    if not profile.is_qualification_complete:
        messages.warning(request, 'Please complete your academic qualifications first.')
        return redirect('profile_qualification')
    
    # Check if user has any academic qualifications
    qualifications = AcademicQualification.objects.filter(user=request.user)
    if not qualifications.exists():
        messages.warning(request, 'Please add at least one academic qualification first.')
        return redirect('phd_academic_qualifications:academic_qualifications')
    
    if request.method == 'POST':
        profile.is_employment_complete = True
        profile.profile_step = 4
        profile.save()
        
        messages.success(request, 'Application completed successfully!')
        return redirect('dashboard')
    
    # Redirect to employment details form
    return redirect('employment_details:employment_add')

@login_required
def complete_employment_step(request):
    """Mark employment step as complete and redirect to dashboard"""
    profile = UserProfile.objects.get(user=request.user)
    profile.is_employment_complete = True
    profile.profile_step = 4
    profile.save()
    
    messages.success(request, 'Employment details completed successfully!')
    return redirect('dashboard')

@login_required
def personal_details_view(request):
    """View and edit personal details"""
    
    # Get or create personal details for the user
    personal_detail, created = PersonalDetail.objects.get_or_create(
        user=request.user,
        defaults={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        }
    )
    
    if request.method == 'POST':
        print("DEBUG: POST request received")
        print(f"DEBUG: POST data keys: {list(request.POST.keys())}")
        print(f"DEBUG: FILES data keys: {list(request.FILES.keys())}")
        
        # Handle photo upload
        if 'photo' in request.FILES:
            print(f"DEBUG: Photo file received: {request.FILES['photo']}")
            personal_detail.photo = request.FILES['photo']
        
        # Combine Aadhaar number parts
        aadhar1 = request.POST.get('aadhar1', '')
        aadhar2 = request.POST.get('aadhar2', '')
        aadhar3 = request.POST.get('aadhar3', '')
        full_aadhar = aadhar1 + aadhar2 + aadhar3 if (aadhar1 and aadhar2 and aadhar3) else ''
        print(f"DEBUG: Combined Aadhaar: {full_aadhar}")
        
        # Update POST data with combined Aadhaar
        post_data = request.POST.copy()
        if full_aadhar:
            post_data['aadhar_number'] = full_aadhar
        
        # Handle other fields
        post_data['first_name'] = request.POST.get('fullName', '')
        post_data['father_name'] = request.POST.get('fatherName', '')
        post_data['mother_name'] = request.POST.get('motherName', '')
        post_data['date_of_birth'] = request.POST.get('date_of_birth', '')
        post_data['gender'] = request.POST.get('gender', '')
        post_data['marital_status'] = request.POST.get('marital', '')
        post_data['email'] = request.POST.get('email', '')
        post_data['alternate_phone'] = request.POST.get('alternate_phone', '')
        
        print(f"DEBUG: Processed POST data: {dict(post_data)}")
        
        form = PersonalDetailForm(post_data, request.FILES, instance=personal_detail)
        print(f"DEBUG: Form is valid: {form.is_valid()}")
        if not form.is_valid():
            print(f"DEBUG: Form errors: {form.errors}")
        
        if form.is_valid():
            saved_obj = form.save()
            print(f"DEBUG: Saved personal detail ID: {saved_obj.id}")
            
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Check if "Save & Continue" was clicked
                if 'next' in request.POST:
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Personal details saved! Redirecting to academic qualifications...',
                        'redirect_url': '/qualifications/'
                    })
                else:
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Personal details saved successfully!'
                    })
            else:
                messages.success(request, 'Personal details updated successfully!')
                # Check if "Save & Continue" was clicked
                if 'next' in request.POST:
                    return redirect('phd_academic_qualifications:academic_qualifications')
                return redirect('personal_details')
        else:
            # Handle form validation errors for AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Please correct the errors below.',
                    'errors': form.errors
                })
    else:
        form = PersonalDetailForm(instance=personal_detail)
    
    context = {
        'form': form,
        'personal_detail': personal_detail,
    }
    
    return render(request, 'personal_details.html', context)
