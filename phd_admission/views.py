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

def create_application_snapshots(user):
    """Create snapshots for all draft applications when user completes profile"""
    from master_control.models import (
        AdmissionApplication, ApplicationProfileSnapshot, 
        ApplicationEducationSnapshot, ApplicationExperienceSnapshot
    )
    from personal_details.models import PersonalDetail
    from phd_academic_qualifications.models import AcademicQualification
    from employment_details.models import EmploymentDetail
    from django.utils import timezone
    
    # Get all draft applications for this user
    draft_applications = AdmissionApplication.objects.filter(
        student=user,
        status='draft',
        is_data_locked=False
    )
    
    for application in draft_applications:
        try:
            # Get personal details
            personal_detail = PersonalDetail.objects.filter(user=user).first()
            if personal_detail:
                # Create profile snapshot
                ApplicationProfileSnapshot.objects.create(
                    application=application,
                    first_name=personal_detail.first_name,
                    last_name=personal_detail.last_name,
                    father_name=personal_detail.father_name,
                    mother_name=personal_detail.mother_name,
                    date_of_birth=personal_detail.date_of_birth,
                    gender=personal_detail.gender,
                    marital_status=personal_detail.marital_status,
                    nationality=personal_detail.nationality,
                    category=personal_detail.category,
                    aadhar_number=personal_detail.aadhar_number,
                    mobile_number=personal_detail.mobile_number,
                    alternate_phone=personal_detail.alternate_phone,
                    email=personal_detail.email,
                    permanent_address=personal_detail.permanent_address,
                    city=personal_detail.city,
                    state=personal_detail.state,
                    pincode=personal_detail.pincode,
                    photo=personal_detail.photo,
                    snapshot_created_at=timezone.now()
                )
            
            # Get education details
            education_records = AcademicQualification.objects.filter(user=user)
            for education in education_records:
                ApplicationEducationSnapshot.objects.create(
                    application=application,
                    examination_passed=education.examination_passed,
                    university_board=education.university_board,
                    year_of_passing=education.year_of_passing,
                    roll_number=education.roll_number,
                    marks_obtained=education.marks_obtained,
                    total_marks=education.total_marks,
                    percentage=education.percentage,
                    grade=education.grade,
                    subjects=education.subjects,
                    snapshot_created_at=timezone.now()
                )
            
            # Get employment details
            employment_records = EmploymentDetail.objects.filter(user=user)
            for employment in employment_records:
                ApplicationExperienceSnapshot.objects.create(
                    application=application,
                    post_held=employment.post_held,
                    organization=employment.organization,
                    date_of_joining=employment.date_of_joining,
                    date_of_leaving=employment.date_of_leaving,
                    experience_years=employment.experience_years,
                    experience_months=employment.experience_months,
                    total_experience=employment.total_experience,
                    snapshot_created_at=timezone.now()
                )
            
            # Update application status and lock it
            application.status = 'submitted'
            application.is_data_locked = True
            application.submitted_at = timezone.now()
            application.save()
            
        except Exception as e:
            # Log error but continue with other applications
            print(f"Error creating snapshots for application {application.id}: {str(e)}")
            continue

@login_required
def complete_employment_step(request):
    """Mark employment step as complete and redirect to dashboard"""
    profile = UserProfile.objects.get(user=request.user)
    profile.is_employment_complete = True
    profile.profile_step = 4
    profile.save()
    
    # Create application snapshots if there's a draft application
    create_application_snapshots(request.user)
    
    messages.success(request, 'Application completed successfully!')
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

@login_required
def apply_now(request):
    """Display active advertisements and available courses for application"""
    from master_control.models import Advertisement, AdvertisementCourse, Course
    from django.utils import timezone
    
    # Get active advertisements
    active_advertisements = Advertisement.objects.filter(
        is_active=True,
        start_date__lte=timezone.now().date(),
        end_date__gte=timezone.now().date()
    ).order_by('-priority', '-created_at')
    
    # Prepare advertisement data with courses
    advertisements_with_courses = []
    for ad in active_advertisements:
        ad_courses = AdvertisementCourse.objects.filter(advertisement=ad).select_related('course')
        courses_data = []
        for ad_course in ad_courses:
            courses_data.append({
                'course': ad_course.course,
                'available_seats': ad_course.available_seats,
                'application_fee': ad_course.application_fee,
                'total_seats': ad_course.total_seats,
            })
        
        advertisements_with_courses.append({
            'advertisement': ad,
            'courses': courses_data,
        })
    
    context = {
        'advertisements_with_courses': advertisements_with_courses,
    }
    
    return render(request, 'apply/apply_now.html', context)

@login_required
def create_application(request):
    """Create a draft application when student applies for a course"""
    from master_control.models import AdmissionApplication, AdvertisementCourse
    from django.shortcuts import get_object_or_404
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('apply_now')
    
    advertisement_id = request.POST.get('advertisement_id')
    course_id = request.POST.get('course_id')
    
    if not advertisement_id or not course_id:
        messages.error(request, 'Advertisement and course are required.')
        return redirect('apply_now')
    
    try:
        # Get the advertisement course
        ad_course = get_object_or_404(AdvertisementCourse, 
                                     advertisement_id=advertisement_id, 
                                     course_id=course_id)
        
        # Check if seats are available
        if ad_course.available_seats <= 0:
            messages.error(request, 'No seats available for this course.')
            return redirect('apply_now')
        
        # Check if student already has an application for this advertisement and course
        existing_application = AdmissionApplication.objects.filter(
            student=request.user,
            advertisement_id=advertisement_id,
            course_id=course_id
        ).first()
        
        if existing_application:
            if existing_application.is_data_locked:
                messages.error(request, 'You have already submitted an application for this course.')
                return redirect('apply_now')
            else:
                messages.info(request, 'You already have a draft application for this course. Please complete it.')
                return redirect('profile_personal_info')
        
        # Create new draft application
        application = AdmissionApplication.objects.create(
            student=request.user,
            advertisement=ad_course.advertisement,
            course=ad_course.course,
            status='draft',
            application_fee=ad_course.application_fee
        )
        
        messages.success(request, f'Application started for {ad_course.course.name}. Please complete your profile.')
        
        # Redirect to profile personal info to start the application process
        return redirect('profile_personal_info')
        
    except Exception as e:
        messages.error(request, f'Error creating application: {str(e)}')
        return redirect('apply_now')


@login_required
def application_preview(request):
    from personal_details.models import PersonalDetail
    from phd_academic_qualifications.models import AcademicQualification
    from employment_details.models import EmploymentDetail

    profile = request.user.profile

    # 🔒 Step validation
    if not (
        profile.is_personal_info_complete and
        profile.is_qualification_complete and
        profile.is_employment_complete
    ):
        messages.warning(request, "Please complete all steps first.")
        return redirect('dashboard')

    # ✅ Fetch SINGLE data
    personal = PersonalDetail.objects.filter(user=request.user).select_related().first()

    # ✅ Fetch MULTIPLE data (FK related)
    qualifications = AcademicQualification.objects.filter(user=request.user).select_related()

    employments = EmploymentDetail.objects.filter(user=request.user).select_related()

    context = {
        "profile": profile,
        "personal": personal,
        "qualifications": qualifications,
        "employments": employments,
    }

    return render(request, "application_preview.html", context)