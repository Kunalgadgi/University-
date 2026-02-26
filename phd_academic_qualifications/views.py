from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from .models import AcademicQualification
from .forms import AcademicQualificationForm

def academic_qualifications(request):
    """Display academic qualifications form (original HTML)"""
    qualifications = AcademicQualification.objects.all().order_by('-year_of_passing')
    
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
            
            # Validate required fields
            if not all([examination, university_board, year_of_passing, roll_number, subjects]):
                return JsonResponse({'status': 'error', 'message': 'Please fill all required fields'})
            
            # Validate grade OR marks
            has_grade = grade.strip()
            has_marks = marks_obtained.strip() and max_marks.strip()
            
            if not has_grade and not has_marks:
                return JsonResponse({'status': 'error', 'message': 'Enter Grade OR Marks Obtained / Max Marks'})
            
            # Create qualification
            qualification = AcademicQualification.objects.create(
                examination_passed=examination,
                custom_examination=custom_examination if examination == 'other' else '',
                university_board=university_board,
                year_of_passing=int(year_of_passing),
                roll_number=roll_number,
                grade=grade if has_grade else None,
                marks_obtained=float(marks_obtained) if has_marks else None,
                max_marks=float(max_marks) if has_marks else None,
                subjects=subjects
            )
            
            return JsonResponse({'status': 'success', 'message': 'Academic qualifications saved successfully!'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
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
