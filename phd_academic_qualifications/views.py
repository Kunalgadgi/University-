from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from .models import AcademicQualification
from .forms import AcademicQualificationForm

def phd_academic_qualifications(request):
    """Display academic qualifications form"""
    if request.user.is_authenticated:
        qualifications = AcademicQualification.objects.filter(user=request.user).order_by('-created_at')
    else:
        qualifications = AcademicQualification.objects.none()
    
    context = {
        'qualifications': qualifications,
    }
    return render(request, 'phd_academic_qualifications/phd_academic_qualifications.html', context)

def submit_qualification_data(request):
    """Handle qualification form submission via AJAX"""
    if request.method == 'POST':
        try:
            # Get form data
            examination = request.POST.get('exam')
            custom_examination = request.POST.get('custom_exam', '')
            university_board = request.POST.get('board')
            year_of_passing = request.POST.get('year')
            roll_number = request.POST.get('roll')
            grade = request.POST.get('grade', '')
            marks_obtained = request.POST.get('obtained', '')
            max_marks = request.POST.get('max', '')
            subjects = request.POST.get('subjects')
            
            # Check if at least one field is filled
            if not any([examination, university_board, year_of_passing, roll_number, subjects, grade, marks_obtained, max_marks]):
                return JsonResponse({'status': 'error', 'message': 'Please fill at least one field'})
            
            # Create qualification with available data
            qualification = AcademicQualification.objects.create(
                user=request.user if request.user.is_authenticated else None,
                examination_passed=examination or 'other',
                custom_examination=custom_examination if examination == 'other' else custom_examination or '',
                university_board=university_board or '',
                year_of_passing=int(year_of_passing) if year_of_passing and year_of_passing.isdigit() else 2023,
                roll_number=roll_number or '',
                grade=grade if grade.strip() else None,
                marks_obtained=float(marks_obtained) if marks_obtained.strip() else None,
                max_marks=float(max_marks) if max_marks.strip() else None,
                subjects=subjects or ''
            )
            
            # Mark profile qualification step as complete if user is logged in
            if request.user.is_authenticated:
                from phd_admission.models import UserProfile
                profile, created = UserProfile.objects.get_or_create(user=request.user)
                profile.is_qualification_complete = True
                profile.profile_step = 3
                profile.save()
                
                return JsonResponse({
                    'status': 'success', 
                    'message': 'Academic qualifications saved successfully!',
                    'redirect_url': '/employment/'
                })
            else:
                return JsonResponse({
                    'status': 'success', 
                    'message': 'Academic qualifications saved successfully!',
                    'redirect_url': None
                })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error: {str(e)}'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def qualification_list(request):
    """Display list of academic qualifications"""
    qualifications = AcademicQualification.objects.all()
    
    context = {
        'qualifications': qualifications,
    }
    return render(request, 'phd_academic_qualifications/qualification_list.html', context)

def qualification_add(request):
    """Add new academic qualification"""
    if request.method == 'POST':
        form = AcademicQualificationForm(request.POST)
        if form.is_valid():
            qualification = form.save()
            messages.success(request, f'Academic qualification for {qualification.examination_name} added successfully!')
            return redirect('phd_academic_qualifications:qualification_list')
    else:
        form = AcademicQualificationForm()
    
    return render(request, 'phd_academic_qualifications/qualification_form.html', {
        'form': form,
        'title': 'Add Academic Qualification'
    })

def qualification_edit(request, pk):
    """Edit existing academic qualification"""
    qualification = get_object_or_404(AcademicQualification, pk=pk)
    
    if request.method == 'POST':
        form = AcademicQualificationForm(request.POST, instance=qualification)
        if form.is_valid():
            qualification = form.save()
            messages.success(request, f'Academic qualification for {qualification.examination_name} updated successfully!')
            return redirect('phd_academic_qualifications:qualification_list')
    else:
        form = AcademicQualificationForm(instance=qualification)
    
    return render(request, 'phd_academic_qualifications/qualification_form.html', {
        'form': form,
        'title': 'Edit Academic Qualification',
        'qualification': qualification
    })

def qualification_delete(request, pk):
    """Delete academic qualification"""
    qualification = get_object_or_404(AcademicQualification, pk=pk)
    
    if request.method == 'POST':
        qualification.delete()
        messages.success(request, 'Academic qualification deleted successfully!')
        return redirect('phd_academic_qualifications:qualification_list')
    
    return render(request, 'phd_academic_qualifications/qualification_confirm_delete.html', {
        'qualification': qualification
    })
