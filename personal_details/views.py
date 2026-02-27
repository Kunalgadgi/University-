from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PersonalDetail
from .forms import PersonalDetailForm

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
        form = PersonalDetailForm(request.POST, instance=personal_detail)
        if form.is_valid():
            form.save()
            messages.success(request, 'Personal details updated successfully!')
            return redirect('personal_details')
    else:
        form = PersonalDetailForm(instance=personal_detail)
    
    context = {
        'form': form,
        'personal_detail': personal_detail,
    }
    
    return render(request, 'personal_details.html', context)
