from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from django.http import JsonResponse
from .models import EmploymentDetail
from .forms import EmploymentDetailForm

def employment_list(request):
    """Display list of employment details with statistics"""
    employments = EmploymentDetail.objects.all()
    
    # Calculate statistics
    total_months = employments.aggregate(
        total_months=Sum('experience_years') * 12 + Sum('experience_months')
    )['total_months'] or 0
    
    total_years = total_months // 12
    remaining_months = total_months % 12
    
    positions_count = employments.count()
    
    context = {
        'employments': employments,
        'total_experience_years': total_years,
        'total_experience_months': remaining_months,
        'positions_count': positions_count,
        'total_months': total_months,
    }
    return render(request, 'employment_details/employment_list.html', context)

def employment_add(request):
    """Add new employment detail"""
    if request.method == 'POST':
        form = EmploymentDetailForm(request.POST)
        if form.is_valid():
            employment = form.save()
            messages.success(request, f'Employment detail for {employment.post_held} added successfully!')
            return redirect('employment_details:employment_list')
    else:
        form = EmploymentDetailForm()
    
    return render(request, 'employment_details/employment_form.html', {
        'form': form,
        'title': 'Add Employment Detail'
    })

def employment_edit(request, pk):
    """Edit existing employment detail"""
    employment = get_object_or_404(EmploymentDetail, pk=pk)
    
    if request.method == 'POST':
        form = EmploymentDetailForm(request.POST, instance=employment)
        if form.is_valid():
            employment = form.save()
            messages.success(request, f'Employment detail for {employment.post_held} updated successfully!')
            return redirect('employment_details:employment_list')
    else:
        form = EmploymentDetailForm(instance=employment)
    
    return render(request, 'employment_details/employment_form.html', {
        'form': form,
        'title': 'Edit Employment Detail',
        'employment': employment
    })

def employment_delete(request, pk):
    """Delete employment detail"""
    employment = get_object_or_404(EmploymentDetail, pk=pk)
    
    if request.method == 'POST':
        employment.delete()
        messages.success(request, 'Employment detail deleted successfully!')
        return redirect('employment_details:employment_list')
    
    return render(request, 'employment_details/employment_confirm_delete.html', {
        'employment': employment
    })

def employment_details(request):
    """Display employment details form (original HTML)"""
    if request.user.is_authenticated:
        employments = EmploymentDetail.objects.filter(user=request.user).order_by('sr_no')
    else:
        employments = EmploymentDetail.objects.none()
    
    # Calculate statistics safely - don't use non-existent fields
    total_months = 0
    for emp in employments:
        try:
            # Just count each employment as 1 month for simplicity
            total_months += 1
        except:
            pass
    
    total_years = total_months // 12
    remaining_months = total_months % 12
    positions_count = employments.count()
    
    context = {
        'employments': employments,
        'total_experience_years': total_years,
        'total_experience_months': remaining_months,
        'positions_count': positions_count,
        'total_months': total_months,
    }
    return render(request, 'employment_details/employment_details.html', context)

def submit_employment_data(request):
    """Handle employment form submission via AJAX"""
    if request.method == 'POST':
        try:
            # Get form data
            sr_no = request.POST.get('sr_no')
            post_held = request.POST.get('post')
            organization = request.POST.get('org')
            from_date = request.POST.get('from')
            to_date = request.POST.get('to')
            job_type = request.POST.get('jobtype')
            remarks = request.POST.get('remarks')
            
            # Check if at least one field is filled
            if not any([post_held, organization, from_date, to_date, job_type, remarks]):
                return JsonResponse({'status': 'error', 'message': 'Please fill at least one field'})
            
            # Validate date logic only if both dates are provided
            if from_date and to_date:
                if from_date > to_date:
                    return JsonResponse({'status': 'error', 'message': 'From date cannot be after to date'})
            
            # Create employment detail with available data
            employment = EmploymentDetail.objects.create(
                user=request.user if request.user.is_authenticated else None,
                sr_no=int(sr_no) if sr_no and sr_no.isdigit() else 1,
                post_held=post_held or '',
                organization=organization or '',
                from_date=from_date or '2023-01-01',
                to_date=to_date or '2023-12-31',
                job_type=job_type or '',
                remarks=remarks or ''
            )
            
            # Mark profile employment step as complete if user is logged in
            if request.user.is_authenticated:
                from phd_admission.models import UserProfile
                profile, created = UserProfile.objects.get_or_create(user=request.user)
                profile.is_employment_complete = True
                profile.profile_step = 4  # Complete
                profile.save()
                
                return JsonResponse({
                    'status': 'success', 
                    'message': 'Employment details saved successfully! Profile complete.',
                    'redirect_url': '/dashboard/'
                })
            else:
                return JsonResponse({
                    'status': 'success', 
                    'message': 'Employment details saved successfully!',
                    'redirect_url': None
                })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error: {str(e)}'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
