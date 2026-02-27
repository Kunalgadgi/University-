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
from django.utils import timezone
from .models import UserProfile
from personal_details.models import PersonalDetail
from personal_details.forms import PersonalDetailForm


def _get_next_url(request):
    return request.POST.get('next') or request.GET.get('next')


def _safe_redirect_next_or(request, fallback_name):
    next_url = _get_next_url(request)
    if next_url:
        return redirect(next_url)
    return redirect(fallback_name)


def _generate_application_no():
    from master_control_project.master_control.models import AdmissionApplication

    prefix = timezone.now().strftime('PHD%Y%m%d')
    for seq in range(1, 10000):
        candidate = f"{prefix}{seq:04d}"
        if not AdmissionApplication.objects.filter(application_no=candidate).exists():
            return candidate
    raise RuntimeError('Unable to generate unique application number')


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
    from master_control_project.master_control.models import AdmissionApplication
    from .models import UserProfile
    
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get user's personal data (filtered by user)
    user_employment_count = EmploymentDetail.objects.filter(user=request.user).count()
    user_qualifications_count = AcademicQualification.objects.filter(user=request.user).count()
    user_applications_count = AdmissionApplication.objects.filter(student=request.user).count()
    
    # Get user's latest application for preview
    latest_application = AdmissionApplication.objects.filter(student=request.user).order_by('-submitted_at').first()
    
    # Get overall statistics
    total_users = User.objects.count()
    total_employment = EmploymentDetail.objects.count()
    total_qualifications = AcademicQualification.objects.count()
    total_applications = AdmissionApplication.objects.count()
    
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
        'latest_application': latest_application,
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
            return _safe_redirect_next_or(request, 'dashboard')
        else:
            messages.error(request, 'Invalid username/email or password. Please try again.')
    
    context = {
        'next': _get_next_url(request) or '',
    }
    return render(request, 'login.html', context)

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
                next_url = request.POST.get('next') or request.GET.get('next')
                if next_url:
                    return redirect(f"/login/?next={next_url}")
                return redirect('login')
                
            except Exception as e:
                messages.error(request, f'An error occurred while creating your account: {str(e)}')
        else:
            # If there are errors, redirect back to registration page
            return redirect('register')
    
    context = {
        'next': _get_next_url(request) or '',
    }
    return render(request, 'register.html', context)

def logout_view(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')


@login_required
def admission_form_single(request):
    personal_detail, _ = PersonalDetail.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        from master_control_project.master_control.models import AdmissionApplication, ApplicationProfileSnapshot, ApplicationEducationSnapshot, ApplicationExperienceSnapshot
        from master_control_project.master_control.models import Advertisement, Course

        # Check if this is save or submit action
        action = request.POST.get('action', 'save')
        
        # For save action, create/update draft in AdmissionApplication
        if action == 'save':
            # Get or create draft application
            ad = Advertisement.objects.filter(is_active=True).order_by('-created_at').first()
            course = Course.objects.filter(is_active=True).order_by('display_priority', 'course_name').first()
            
            if not ad or not course:
                messages.error(request, 'No active Advertisement/Course found. Please add them in Master Control first.')
                return redirect('admission_form_single')
            
            # Get existing draft or create new one
            draft_application = AdmissionApplication.objects.filter(
                student=request.user,
                status='draft'
            ).first()
            
            if not draft_application:
                app_no = _generate_application_no()
                draft_application = AdmissionApplication.objects.create(
                    application_no=app_no,
                    student=request.user,
                    advertisement=ad,
                    course=course,
                    department_name=getattr(course, 'department_name', '') or '',
                    status='draft'
                )
            
            # Update PersonalDetail
            personal_detail.first_name = request.POST.get('full_name') or personal_detail.first_name
            personal_detail.father_name = request.POST.get('father_name') or personal_detail.father_name
            personal_detail.mother_name = request.POST.get('mother_name') or personal_detail.mother_name
            personal_detail.nationality = request.POST.get('nationality') or personal_detail.nationality
            personal_detail.marital_status = request.POST.get('marital_status') or personal_detail.marital_status
            personal_detail.gender = request.POST.get('gender') or personal_detail.gender
            personal_detail.aadhar_number = request.POST.get('aadhar') or personal_detail.aadhar_number
            personal_detail.permanent_address = request.POST.get('perm_address') or personal_detail.permanent_address
            personal_detail.current_address = request.POST.get('corr_address') or personal_detail.current_address
            personal_detail.mobile_number = request.POST.get('mobile') or personal_detail.mobile_number
            personal_detail.email = request.POST.get('email') or personal_detail.email
            personal_detail.category = request.POST.get('category') or personal_detail.category
            personal_detail.state = request.POST.get('state') or personal_detail.state
            personal_detail.city = request.POST.get('district') or personal_detail.city
            personal_detail.pincode = request.POST.get('pincode') or personal_detail.pincode
            personal_detail.date_of_birth = request.POST.get('dob') or personal_detail.date_of_birth

            upload = request.FILES.get('photo')
            if upload:
                personal_detail.photo = upload

            personal_detail.save()
            
            # Update draft application with form data
            draft_application.first_name = request.POST.get('full_name') or ''
            draft_application.father_name = request.POST.get('father_name') or ''
            draft_application.mother_name = request.POST.get('mother_name') or ''
            draft_application.nationality = request.POST.get('nationality') or ''
            draft_application.marital_status = request.POST.get('marital_status') or ''
            draft_application.gender = request.POST.get('gender') or ''
            draft_application.aadhar_number = request.POST.get('aadhar') or ''
            draft_application.category = request.POST.get('category') or ''
            draft_application.category_tick = request.POST.get('category_tick') or ''
            draft_application.category_other = request.POST.get('category_other') or ''
            draft_application.ugc_category = request.POST.get('ugc_category') or ''
            draft_application.mobile_number = request.POST.get('mobile') or ''
            draft_application.email = request.POST.get('email') or ''
            draft_application.permanent_address = request.POST.get('perm_address') or ''
            draft_application.current_address = request.POST.get('corr_address') or ''
            draft_application.corr_address_block = request.POST.get('corr_address_block') or ''
            draft_application.district = request.POST.get('district') or ''
            draft_application.state = request.POST.get('state') or ''
            draft_application.pincode = request.POST.get('pincode') or ''
            draft_application.mobile_telephone = request.POST.get('mobile_telephone') or ''
            draft_application.email_correspondence = request.POST.get('email_correspondence') or ''
            
            # Handle photo upload for application
            if upload:
                draft_application.photo = upload
            
            signature_upload = request.FILES.get('signature')
            if signature_upload:
                draft_application.signature = signature_upload
            
            draft_application.save()
            
            messages.success(request, f'Application draft saved successfully! Your draft (Application No: {draft_application.application_no}) is saved in the database.')
            return redirect('admission_form_single')

        # For submit action, create/update AdmissionApplication
        # Initialize data collections for unified storage
        employment_history_data = []
        academic_qualifications = []

        # 1) Update PersonalDetail (basic fields + photo)
        personal_detail.first_name = request.POST.get('full_name') or personal_detail.first_name
        personal_detail.father_name = request.POST.get('father_name') or personal_detail.father_name
        personal_detail.mother_name = request.POST.get('mother_name') or personal_detail.mother_name
        personal_detail.nationality = request.POST.get('nationality') or personal_detail.nationality
        personal_detail.marital_status = request.POST.get('marital_status') or personal_detail.marital_status
        personal_detail.gender = request.POST.get('gender') or personal_detail.gender
        personal_detail.aadhar_number = request.POST.get('aadhar') or personal_detail.aadhar_number
        personal_detail.permanent_address = request.POST.get('perm_address') or personal_detail.permanent_address
        personal_detail.current_address = request.POST.get('corr_address') or personal_detail.current_address
        personal_detail.mobile_number = request.POST.get('mobile') or personal_detail.mobile_number
        personal_detail.email = request.POST.get('email') or personal_detail.email
        personal_detail.category = request.POST.get('category') or personal_detail.category
        personal_detail.state = request.POST.get('state') or personal_detail.state
        personal_detail.city = request.POST.get('district') or personal_detail.city
        personal_detail.pincode = request.POST.get('pincode') or personal_detail.pincode

        upload = request.FILES.get('photo')
        if upload:
            personal_detail.photo = upload

        signature_upload = request.FILES.get('signature')
        if signature_upload:
            personal_detail.signature = signature_upload

        personal_detail.save()

        # 2) Create application shell (needs advertisement/course)
        ad = Advertisement.objects.filter(is_active=True).order_by('-created_at').first()
        course = Course.objects.filter(is_active=True).order_by('display_priority', 'course_name').first()
        if not ad or not course:
            messages.error(request, 'No active Advertisement/Course found. Please add them in Master Control first.')
            return redirect('admission_form_single')

        # Check if user already has a submitted application (prevent duplicates)
        existing_application = AdmissionApplication.objects.filter(
            student=request.user,
            status='submitted'
        ).first()
        
        if existing_application:
            messages.error(request, f'You have already submitted an application (Application No: {existing_application.application_no}). You cannot submit multiple applications.')
            return redirect('admission_form_single')

        app_no = _generate_application_no()
        application = AdmissionApplication.objects.create(
            application_no=app_no,
            student=request.user,
            advertisement=ad,
            course=course,
            department_name=getattr(course, 'department_name', '') or '',
            status='submitted',
            submitted_at=timezone.now(),
            is_data_locked=True,
        )

        # 6) Save unified data to single table for database viewing
        try:
            from master_control_project.master_control.models import UnifiedApplicationData
        except ImportError:
            UnifiedApplicationData = None

        # Prepare academic data as JSON
        aq_exam = request.POST.getlist('aq_exam[]')
        aq_board = request.POST.getlist('aq_board[]')
        aq_year = request.POST.getlist('aq_year[]')
        aq_roll = request.POST.getlist('aq_roll[]')
        aq_marks_obtained = request.POST.getlist('aq_marks_obtained[]')
        aq_total_marks = request.POST.getlist('aq_total_marks[]')
        aq_subjects = request.POST.getlist('aq_subjects[]')

        row_count = max(len(aq_exam), len(aq_board), len(aq_year), len(aq_roll), len(aq_marks_obtained), len(aq_total_marks), len(aq_subjects))
        for i in range(row_count):
            qualification = (aq_exam[i] if i < len(aq_exam) else '').strip()
            board_university = (aq_board[i] if i < len(aq_board) else '').strip()
            passing_year = (aq_year[i] if i < len(aq_year) else '').strip()
            roll_number = (aq_roll[i] if i < len(aq_roll) else '').strip()
            marks_obtained = (aq_marks_obtained[i] if i < len(aq_marks_obtained) else '').strip()
            total_marks = (aq_total_marks[i] if i < len(aq_total_marks) else '').strip()
            subjects = (aq_subjects[i] if i < len(aq_subjects) else '').strip()

            if not (qualification or board_university or passing_year or roll_number or marks_obtained or total_marks or subjects):
                continue

            # Validation: marks obtained should not be greater than total marks
            if marks_obtained and total_marks:
                try:
                    marks_obtained_num = float(marks_obtained)
                    total_marks_num = float(total_marks)
                    if marks_obtained_num > total_marks_num:
                        messages.error(request, f'Error: Marks obtained ({marks_obtained}) cannot be greater than total marks ({total_marks}) for {qualification or "examination"}')
                        return redirect('admission_form_single')
                except ValueError:
                    pass

            # Calculate percentage if both values are provided
            percentage = ""
            if marks_obtained and total_marks:
                try:
                    marks_obtained_num = float(marks_obtained)
                    total_marks_num = float(total_marks)
                    if total_marks_num > 0:
                        percentage = f"{(marks_obtained_num / total_marks_num) * 100:.2f}%"
                except ValueError:
                    percentage = f"{marks_obtained}/{total_marks}"
            elif marks_obtained or total_marks:
                percentage = f"{marks_obtained or '-'}/{total_marks or '-'}"

            ApplicationEducationSnapshot.objects.create(
                application=application,
                qualification=qualification,
                board_university=board_university,
                passing_year=passing_year,
                roll_number=roll_number,
                percentage=percentage,
                subjects=subjects,
            )

        # 5) Save employment rows as snapshots
        emp_post = request.POST.getlist('emp_post[]')
        emp_org = request.POST.getlist('emp_org[]')
        emp_from = request.POST.getlist('emp_from[]')
        emp_to = request.POST.getlist('emp_to[]')
        emp_type = request.POST.getlist('emp_type[]')
        emp_remarks = request.POST.getlist('emp_remarks[]')

        emp_rows = max(len(emp_post), len(emp_org), len(emp_from), len(emp_to), len(emp_type), len(emp_remarks))
        for i in range(emp_rows):
            designation = (emp_post[i] if i < len(emp_post) else '').strip()
            org = (emp_org[i] if i < len(emp_org) else '').strip()
            from_raw = (emp_from[i] if i < len(emp_from) else '').strip()
            to_raw = (emp_to[i] if i < len(emp_to) else '').strip()
            typ = (emp_type[i] if i < len(emp_type) else '').strip()
            remarks = (emp_remarks[i] if i < len(emp_remarks) else '').strip()

            if not (designation or org or from_raw or to_raw or typ or remarks):
                continue

            from_dt = None
            to_dt = None
            try:
                from_dt = datetime.strptime(from_raw, '%Y-%m-%d').date() if from_raw else None
            except Exception:
                from_dt = None
            try:
                to_dt = datetime.strptime(to_raw, '%Y-%m-%d').date() if to_raw else None
            except Exception:
                to_dt = None

            ApplicationExperienceSnapshot.objects.create(
                application=application,
                organization_name=org,
                designation=designation,
                from_date=from_dt,
                to_date=to_dt,
                experience_type=typ,
                remarks=remarks,
            )

        # 7) Save all data directly to AdmissionApplication table for unified database view
        application.first_name = personal_detail.first_name or ''
        application.last_name = personal_detail.last_name or ''
        application.full_name = f"{personal_detail.first_name or ''} {personal_detail.last_name or ''}".strip()
        application.date_of_birth = personal_detail.date_of_birth
        application.gender = personal_detail.gender
        application.father_name = personal_detail.father_name
        application.mother_name = personal_detail.mother_name
        application.marital_status = personal_detail.marital_status
        application.nationality = personal_detail.nationality
        application.aadhar_number = personal_detail.aadhar_number or ''
        application.category = personal_detail.category
        application.category_tick = request.POST.get('category_tick') or ''
        application.category_other = request.POST.get('category_other') or ''
        application.ugc_category = request.POST.get('ugc_category') or ''
        application.mobile_number = personal_detail.mobile_number or request.POST.get('mobile') or '0000000000'
        application.email = personal_detail.email or request.POST.get('email') or 'no-email@example.com'
        application.permanent_address = personal_detail.permanent_address
        application.current_address = personal_detail.current_address
        application.corr_address_block = request.POST.get('corr_address_block') or ''
        application.district = personal_detail.city
        application.state = personal_detail.state
        application.pincode = personal_detail.pincode
        application.mobile_telephone = request.POST.get('mobile_telephone') or ''
        application.email_correspondence = request.POST.get('email_correspondence') or ''
        application.academic_data = {'qualifications': academic_qualifications}
        application.specialization_area = request.POST.get('specialization_area') or ''
        application.proposed_supervisor = request.POST.get('proposed_supervisor') or ''
        application.fellowship_validity = datetime.strptime(request.POST.get('fellowship_validity'), '%Y-%m-%d').date() if request.POST.get('fellowship_validity') else None
        application.fellowship_category = request.POST.get('fellowship_category') or ''
        application.employed_status = request.POST.get('employed_status') or ''
        application.emp_post_current = request.POST.get('emp_post_current') or ''
        application.job_nature = request.POST.get('job_nature') or ''
        application.date_of_joining = datetime.strptime(request.POST.get('date_of_joining'), '%Y-%m-%d').date() if request.POST.get('date_of_joining') else None
        application.service_period = request.POST.get('service_period') or ''
        application.organization_name_current = request.POST.get('organization_name_current') or ''
        application.organization_address = request.POST.get('organization_address') or ''
        application.org_telephone = request.POST.get('org_telephone') or ''
        application.org_email = request.POST.get('org_email') or ''
        application.employment_history = {'employments': employment_history_data}
        application.research_experience = request.POST.get('research_experience') or ''
        application.publications = request.POST.get('publications') or ''
        application.pursuing_other_course = request.POST.get('pursuing_other_course') or ''
        application.other_institution = request.POST.get('other_institution') or ''
        application.other_class = request.POST.get('other_class') or ''
        application.other_session = request.POST.get('other_session') or ''
        application.other_result = request.POST.get('other_result') or ''
        # Save photo and signature directly to application as well
        photo_upload = request.FILES.get('photo')
        if photo_upload:
            application.photo = photo_upload
        else:
            application.photo = personal_detail.photo

        signature_upload = request.FILES.get('signature')
        if signature_upload:
            application.signature = signature_upload
        else:
            application.signature = personal_detail.signature

        application.save()
        
        # Also save to UnifiedApplicationData if available
        if UnifiedApplicationData:
            UnifiedApplicationData.objects.update_or_create(
                application=application,
                defaults={
                    'application_no': application.application_no,
                    'first_name': personal_detail.first_name or '',
                    'last_name': personal_detail.last_name or '',
                    'full_name': f"{personal_detail.first_name or ''} {personal_detail.last_name or ''}".strip(),
                    'date_of_birth': personal_detail.date_of_birth,
                    'gender': personal_detail.gender,
                    'father_name': personal_detail.father_name,
                    'mother_name': personal_detail.mother_name,
                    'marital_status': personal_detail.marital_status,
                    'nationality': personal_detail.nationality,
                    'aadhar_number': personal_detail.aadhar_number,
                    'category': personal_detail.category,
                    'category_tick': request.POST.get('category_tick') or '',
                    'category_other': request.POST.get('category_other') or '',
                    'mobile_number': personal_detail.mobile_number,
                    'email': personal_detail.email,
                    'permanent_address': personal_detail.permanent_address,
                    'current_address': personal_detail.current_address,
                    'corr_address_block': request.POST.get('corr_address_block') or '',
                    'district': personal_detail.city,
                    'state': personal_detail.state,
                    'pincode': personal_detail.pincode,
                    'mobile_telephone': request.POST.get('mobile_telephone') or '',
                    'email_correspondence': request.POST.get('email_correspondence') or '',
                    'academic_data': {'qualifications': academic_qualifications},
                    'specialization_area': request.POST.get('specialization_area') or '',
                    'proposed_supervisor': request.POST.get('proposed_supervisor') or '',
                    'fellowship_validity': datetime.strptime(request.POST.get('fellowship_validity'), '%Y-%m-%d').date() if request.POST.get('fellowship_validity') else None,
                    'fellowship_category': request.POST.get('fellowship_category') or '',
                    'employed_status': request.POST.get('employed_status') or '',
                    'emp_post_current': request.POST.get('emp_post_current') or '',
                    'job_nature': request.POST.get('job_nature') or '',
                    'date_of_joining': datetime.strptime(request.POST.get('date_of_joining'), '%Y-%m-%d').date() if request.POST.get('date_of_joining') else None,
                    'service_period': request.POST.get('service_period') or '',
                    'organization_name_current': request.POST.get('organization_name_current') or '',
                    'organization_address': request.POST.get('organization_address') or '',
                    'org_telephone': request.POST.get('org_telephone') or '',
                    'org_email': request.POST.get('org_email') or '',
                    'employment_history': {'employments': employment_history_data},
                    'research_experience': request.POST.get('research_experience') or '',
                    'publications': request.POST.get('publications') or '',
                    'pursuing_other_course': request.POST.get('pursuing_other_course') or '',
                    'other_institution': request.POST.get('other_institution') or '',
                    'other_class': request.POST.get('other_class') or '',
                    'other_session': request.POST.get('other_session') or '',
                    'other_result': request.POST.get('other_result') or '',
                    'photo': personal_detail.photo,
                    'signature': personal_detail.signature,
                }
            )

        messages.success(request, f'Application submitted successfully! Application No: {application.application_no}')
        return redirect(f"/application_preview/?app={application.id}")

    # Check if user already has a submitted application
    has_submitted_application = False
    draft_application = None
    try:
        from master_control_project.master_control.models import AdmissionApplication
        existing_app = AdmissionApplication.objects.filter(
            student=request.user,
            status='submitted'
        ).first()
        has_submitted_application = existing_app is not None
        
        # Get draft application if it exists
        draft_application = AdmissionApplication.objects.filter(
            student=request.user,
            status='draft'
        ).first()
    except ImportError:
        pass

    context = {
        'user': request.user,
        'personal_detail': personal_detail,
        'has_submitted_application': has_submitted_application,
        'draft_application': draft_application,
    }
    return render(request, 'admission_form_single.html', context)

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
    from master_control_project.master_control.models import (
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
    from master_control_project.master_control.models import Advertisement, AdvertisementCourse, Course
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
    from master_control_project.master_control.models import AdmissionApplication, AdvertisementCourse
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
        
        # Check if seats are available (schema uses total_seats)
        if getattr(ad_course, 'total_seats', 0) <= 0:
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
        
        # Create new draft application (AdmissionApplication requires application_no)
        application = AdmissionApplication.objects.create(
            application_no=_generate_application_no(),
            student=request.user,
            advertisement=ad_course.advertisement,
            course=ad_course.course,
            department_name=getattr(ad_course.course, 'department_name', '') or '',
            status='draft',
        )
        
        messages.success(request, f'Application started for {ad_course.course.course_name}. Please complete your profile.')
        
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

    app_id = request.GET.get('app')
    if app_id:
        from master_control_project.master_control.models import AdmissionApplication

        try:
            application = AdmissionApplication.objects.select_related('advertisement', 'course').get(id=app_id, student=request.user)
        except AdmissionApplication.DoesNotExist:
            messages.error(request, 'Application not found.')
            return redirect('dashboard')

        personal = PersonalDetail.objects.filter(user=request.user).first()
        profile_snapshot = getattr(application, 'profile_snapshot', None)
        edu = getattr(application, 'education_snapshots', None)
        exp = getattr(application, 'experience_snapshots', None)

        context = {
            'application': application,
            'application_no': application.application_no,
            'personal': personal,
            'profile_snapshot': profile_snapshot,
            'qualifications': edu.all() if edu else [],
            'employments': exp.all() if exp else [],
        }
        return render(request, 'application_preview.html', context)

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


@login_required
def application_single_table(request):
    """Display complete application data in a single table with print option"""
    app_id = request.GET.get('app')
    
    if app_id:
        application = get_object_or_404(AdmissionApplication, id=app_id, user=request.user)
        
        personal = PersonalDetail.objects.filter(user=request.user).first()
        profile_snapshot = getattr(application, 'profile_snapshot', None)
        edu = getattr(application, 'education_snapshots', None)
        exp = getattr(application, 'experience_snapshots', None)

        context = {
            'application': application,
            'application_no': application.application_no,
            'personal': personal,
            'profile_snapshot': profile_snapshot,
            'qualifications': edu.all() if edu else [],
            'employments': exp.all() if exp else [],
        }
        return render(request, 'application_single_table.html', context)

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

    return render(request, "application_single_table.html", context)


@login_required
def print_application(request):
    """Print admission application from database"""
    from django.shortcuts import get_object_or_404
    app_id = request.GET.get('app')
    
    if not app_id:
        messages.error(request, 'Application ID is required')
        return redirect('dashboard')
    
    try:
        from master_control_project.master_control.models import AdmissionApplication
        
        application = get_object_or_404(AdmissionApplication, id=app_id)
        
        # Check if user owns this application or is staff
        if not (request.user.is_staff or application.student == request.user):
            messages.error(request, 'Access denied')
            return redirect('dashboard')
        
        # Get personal data like application_preview does
        from personal_details.models import PersonalDetail
        personal = PersonalDetail.objects.filter(user=request.user).first()
        profile_snapshot = getattr(application, 'profile_snapshot', None)
        
        # Mark as printed
        application.is_printed = True
        application.printed_date = timezone.now()
        application.printed_by = request.user
        application.save()
        
        # Get academic qualifications from ApplicationEducationSnapshots
        try:
            from master_control_project.master_control.models import ApplicationEducationSnapshot
            academic_qualifications = ApplicationEducationSnapshot.objects.filter(application=application)
        except:
            academic_qualifications = []
        
        # Get employment history from ApplicationExperienceSnapshots
        try:
            from master_control_project.master_control.models import ApplicationExperienceSnapshot
            employment_history = ApplicationExperienceSnapshot.objects.filter(application=application)
        except:
            employment_history = []
        
        context = {
            'application': application,
            'personal': personal,
            'profile_snapshot': profile_snapshot,
            'academic_qualifications': academic_qualifications,
            'employment_history': employment_history,
        }
        
        return render(request, 'print_application.html', context)
        
    except Exception as e:
        messages.error(request, f'Error printing application: {str(e)}')
        return redirect('dashboard')


@login_required
def unified_application_view(request):
    """Display unified application data from single database table"""
    try:
        from master_control_project.master_control.models import UnifiedApplicationData
    except ImportError:
        UnifiedApplicationData = None
    
    app_id = request.GET.get('app')
    
    if app_id:
        # Get specific application
        if UnifiedApplicationData:
            unified_data = get_object_or_404(UnifiedApplicationData, application__id=app_id)
            
            context = {
                'unified_data': unified_data,
                'application': unified_data.application,
                'academic_qualifications': unified_data.get_academic_qualifications(),
                'employment_history': unified_data.get_employment_history(),
            }
            
            # Mark as printed if requested
            if request.POST.get('mark_printed'):
                unified_data.mark_as_printed(request.user)
                messages.success(request, "Application marked as printed!")
            
            return render(request, 'unified_application_display.html', context)
        else:
            # Fallback to AdmissionApplication
            application = get_object_or_404(AdmissionApplication, id=app_id, user=request.user)
            context = {
                'unified_data': application,
                'application': application,
                'academic_qualifications': application.get_academic_qualifications(),
                'employment_history': application.get_employment_history(),
            }
            return render(request, 'unified_application_display.html', context)
    
    # Get all applications for admin view
    if request.user.is_staff:
        if UnifiedApplicationData:
            all_applications = UnifiedApplicationData.objects.all().order_by('-created_at')
        else:
            all_applications = AdmissionApplication.objects.all().order_by('-created_at')
        context = {
            'all_applications': all_applications,
        }
        return render(request, 'unified_applications_list.html', context)
    
    # Redirect regular users to dashboard
    return redirect('dashboard')