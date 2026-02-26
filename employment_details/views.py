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
    employments = EmploymentDetail.objects.all().order_by('sr_no')
    
    # Calculate statistics
    total_exp_years = employments.aggregate(total=Sum('experience_years'))['total'] or 0
    total_exp_months = employments.aggregate(total=Sum('experience_months'))['total'] or 0
    total_months = (total_exp_years * 12) + total_exp_months
    
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
            
            # Validate required fields
            if not all([sr_no, post_held, organization, from_date, to_date, job_type]):
                return JsonResponse({'status': 'error', 'message': 'Please fill all required fields'})
            
            # Create employment detail
            employment = EmploymentDetail.objects.create(
                sr_no=int(sr_no),
                post_held=post_held,
                organization=organization,
                from_date=from_date,
                to_date=to_date,
                job_type=job_type,
                remarks=remarks or ''
            )
            
            return JsonResponse({'status': 'success', 'message': 'Employment details saved successfully!'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
