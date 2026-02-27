#!/usr/bin/env python
"""
Simple script to populate existing AdmissionApplication records
"""

import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phd_admission.settings')
django.setup()

from django.db import transaction
from master_control_project.master_control.models import AdmissionApplication
from personal_details.models import PersonalDetail
from phd_academic_qualifications.models import AcademicQualification
from employment_details.models import EmploymentDetail

def populate_applications():
    print("Populating existing applications...")
    
    applications = AdmissionApplication.objects.all()
    print(f"Found {applications.count()} applications")
    
    for app in applications:
        print(f"Processing: {app.application_no}")
        
        # Get personal details
        personal = PersonalDetail.objects.filter(user=app.student).first()
        if personal:
            app.first_name = personal.first_name or ''
            app.last_name = personal.last_name or ''
            app.full_name = f"{personal.first_name or ''} {personal.last_name or ''}".strip()
            app.date_of_birth = personal.date_of_birth
            app.gender = personal.gender
            app.father_name = personal.father_name
            app.mother_name = personal.mother_name
            app.marital_status = personal.marital_status
            app.nationality = personal.nationality
            app.aadhar_number = personal.aadhar_number
            app.category = personal.category
            app.mobile_number = personal.mobile_number
            app.email = personal.email
            app.permanent_address = personal.permanent_address
            app.current_address = personal.current_address
            app.district = personal.city
            app.state = personal.state
            app.pincode = personal.pincode
            app.photo = personal.photo
            app.signature = personal.signature
            print(f"  Updated personal: {app.full_name}")
        
        # Get academic qualifications
        qualifications = AcademicQualification.objects.filter(user=app.student)
        if qualifications.exists():
            academic_data = []
            for qual in qualifications:
                academic_data.append({
                    'examination_name': qual.examination_name,
                    'board_university': qual.university_board,
                    'passing_year': qual.year_of_passing,
                    'roll_number': qual.roll_number,
                    'marks_obtained': qual.marks_obtained,
                    'total_marks': qual.max_marks,
                    'subjects': qual.subjects,
                })
            app.academic_data = {'qualifications': academic_data}
            print(f"  Updated {qualifications.count()} qualifications")
        
        # Get employment details
        employments = EmploymentDetail.objects.filter(user=app.student)
        if employments.exists():
            employment_data = []
            for emp in employments:
                employment_data.append({
                    'post_held': emp.post_held,
                    'organization': emp.organization,
                    'from_date': emp.from_date.isoformat() if emp.from_date else None,
                    'to_date': emp.to_date.isoformat() if emp.to_date else None,
                    'job_type': emp.job_type,
                    'remarks': getattr(emp, 'remarks', ''),
                })
            app.employment_history = {'employments': employment_data}
            print(f"  Updated {employments.count()} employments")
        
        app.save()
        print(f"  ✓ Saved {app.application_no}")
    
    print("Done!")

if __name__ == "__main__":
    populate_applications()
