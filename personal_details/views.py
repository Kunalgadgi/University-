from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render

from .forms import PersonalDetailForm
from .models import PersonalDetail


@login_required
def personal_details_view(request):
    print("=== DEBUG: personal_details_view called ===")
    print(f"DEBUG: request method: {request.method}")
    print(f"DEBUG: request path: {request.path}")
    print(f"DEBUG: user: {request.user.username}")
    
    personal_detail, created = PersonalDetail.objects.get_or_create(
        user=request.user,
        defaults={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        },
    )
    print(f"DEBUG: get_or_create result: created={created}, id={personal_detail.id}")

    if request.method == 'POST':
        print("\n=== DEBUG: POST request received ===")
        print(f"DEBUG: POST data keys: {list(request.POST.keys())}")
        print(f"DEBUG: FILES data keys: {list(request.FILES.keys())}")
        for key, value in request.POST.items():
            print(f"DEBUG: POST[{key}] = {value!r}")
        for key, value in request.FILES.items():
            print(f"DEBUG: FILES[{key}] = {value}")

        aadhar1 = request.POST.get('aadhar1', '')
        aadhar2 = request.POST.get('aadhar2', '')
        aadhar3 = request.POST.get('aadhar3', '')
        full_aadhar = aadhar1 + aadhar2 + aadhar3 if (aadhar1 and aadhar2 and aadhar3) else ''

        post_data = request.POST.copy()
        if full_aadhar:
            post_data['aadhar_number'] = full_aadhar

        post_data['first_name'] = request.POST.get('fullName', '')
        # Split full name into first_name and last_name if possible
        full_name_val = post_data['first_name'].strip()
        if ' ' in full_name_val:
            parts = full_name_val.split(' ', 1)
            post_data['first_name'] = parts[0]
            post_data['last_name'] = parts[1]
        else:
            post_data['first_name'] = full_name_val
            post_data['last_name'] = ''
        post_data['father_name'] = request.POST.get('fatherName', '')
        post_data['mother_name'] = request.POST.get('motherName', '')
        post_data['date_of_birth'] = request.POST.get('date_of_birth', '')

        gender_raw = (request.POST.get('gender', '') or '').strip()
        gender_map = {
            'male': 'male',
            'm': 'male',
            'female': 'female',
            'f': 'female',
            'other': 'other',
            'o': 'other',
            'transgender': 'other',
            't': 'other',
        }
        post_data['gender'] = gender_map.get(gender_raw.lower(), gender_raw.lower())

        marital_raw = (request.POST.get('marital', '') or '').strip()
        marital_map = {
            'single': 'single',
            'married': 'married',
            'divorced': 'divorced',
            'widowed': 'widowed',
            's': 'single',
            'm': 'married',
            'd': 'divorced',
            'w': 'widowed',
        }
        post_data['marital_status'] = marital_map.get(marital_raw.lower(), marital_raw.lower())

        post_data['nationality'] = request.POST.get('nationality', '')
        post_data['category'] = request.POST.get('category', '')
        post_data['mobile_number'] = request.POST.get('mobile_number', '')
        post_data['email'] = request.POST.get('email', '')
        post_data['alternate_phone'] = request.POST.get('alternate_phone', '')

        post_data['permanent_address'] = request.POST.get('permanent_address', '')
        post_data['city'] = request.POST.get('city', '')
        post_data['state'] = request.POST.get('state', '')
        post_data['pincode'] = request.POST.get('pincode', '')

        post_data['current_address'] = request.POST.get('current_address', '') or request.POST.get(
            'permanent_address', ''
        )

        print(f"\nDEBUG: Processed POST data (sample):")
        print(f"  first_name: {post_data.get('first_name')!r}")
        print(f"  last_name: {post_data.get('last_name')!r}")
        print(f"  father_name: {post_data.get('father_name')!r}")
        print(f"  mother_name: {post_data.get('mother_name')!r}")
        print(f"  email: {post_data.get('email')!r}")
        print(f"  mobile_number: {post_data.get('mobile_number')!r}")

        form = PersonalDetailForm(post_data, request.FILES, instance=personal_detail)
        print(f"DEBUG: Form is valid: {form.is_valid()}")
        if not form.is_valid():
            print(f"DEBUG: Form errors: {form.errors}")

        if form.is_valid():
            saved_obj = form.save()
            print(f"\n=== DEBUG: Saved personal detail ID: {saved_obj.id} ===")
            print(f"DEBUG: Saved fields:")
            print(f"  first_name: {saved_obj.first_name!r}")
            print(f"  last_name: {saved_obj.last_name!r}")
            print(f"  Computed full_name: {saved_obj.full_name!r}")
            print(f"  father_name: {saved_obj.father_name!r}")
            print(f"  mother_name: {saved_obj.mother_name!r}")
            print(f"  email: {saved_obj.email!r}")
            print(f"  mobile_number: {saved_obj.mobile_number!r}")
            print(f"  aadhar_number: {saved_obj.aadhar_number!r}")
            print(f"  gender: {saved_obj.gender!r}")
            print(f"  marital_status: {saved_obj.marital_status!r}")
            print(f"  nationality: {saved_obj.nationality!r}")
            print(f"  category: {saved_obj.category!r}")
            print(f"  permanent_address: {saved_obj.permanent_address!r}")
            print(f"  city: {saved_obj.city!r}")
            print(f"  state: {saved_obj.state!r}")
            print(f"  pincode: {saved_obj.pincode!r}")
            print("=== END SAVE DEBUG ===\n")

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                if 'next' in request.POST:
                    return JsonResponse(
                        {
                            'status': 'success',
                            'message': 'Personal details saved! Redirecting to academic qualifications...',
                            'redirect_url': '/qualifications/',
                        }
                    )
                return JsonResponse({'status': 'success', 'message': 'Personal details saved successfully!'})

            messages.success(request, 'Personal details updated successfully!')
            if 'next' in request.POST:
                return redirect('phd_academic_qualifications:academic_qualifications')
            return redirect('personal_details:personal_details')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {
                    'status': 'error',
                    'message': 'Please correct the errors below.',
                    'errors': form.errors,
                }
            )

    else:
        form = PersonalDetailForm(instance=personal_detail)

    context = {
        'form': form,
        'personal_detail': personal_detail,
    }

    return render(request, 'personal_details.html', context)
