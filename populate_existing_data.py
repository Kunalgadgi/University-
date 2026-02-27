#!/usr/bin/env python
"""
Script to populate existing AdmissionApplication records with data from PersonalDetail, 
AcademicQualification, and EmploymentDetail tables.
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(r'C:\Users\HP\CascadeProjects\phd_admission')
sys.path.append(r'C:\Users\HP\CascadeProjects\phd_admission\master_control_project')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phd_admission.settings')
django.setup()

from django.db import transaction
from master_control_project.master_control.models import AdmissionApplication, UnifiedApplicationData
from personal_details.models import PersonalDetail
from phd_academic_qualifications.models import AcademicQualification
from employment_details.models import EmploymentDetail
from django.contrib.auth.models import User

def populate_existing_applications():
    """Populate existing applications with data from related tables"""
    
    print("Starting to populate existing applications...")
    
    # Get all existing applications
    applications = AdmissionApplication.objects.all()
    print(f"Found {applications.count()} applications to process")
    
    for app in applications:
        print(f"\nProcessing application: {app.application_no}")
        
        try:
            # Get personal details
            personal = PersonalDetail.objects.filter(user=app.student).first()
            if personal:
                print(f"  Found personal details for {app.student.username}")
                
                # Update personal information
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
                
                print(f"  Updated personal info: {app.full_name}")
            
            # Get academic qualifications
            qualifications = AcademicQualification.objects.filter(user=app.student)
            if qualifications.exists():
                print(f"  Found {qualifications.count()} academic qualifications")
                
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
                print(f"  Updated academic data")
            
            # Get employment details
            employments = EmploymentDetail.objects.filter(user=app.student)
            if employments.exists():
                print(f"  Found {employments.count()} employment records")
                
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
                print(f"  Updated employment history")
            
            # Save the application
            app.save()
            print(f"  ✓ Saved application {app.application_no}")
            
        except Exception as e:
            print(f"  ✗ Error processing application {app.application_no}: {str(e)}")
            continue
    
    print(f"\n✅ Completed processing {applications.count()} applications")

if __name__ == "__main__":
    populate_existing_applications()
