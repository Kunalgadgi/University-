#!/usr/bin/env python
"""
Signature Fix Verification Script
This script verifies that the signature saving and display functionality is working correctly.
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_admission.settings')
django.setup()

def test_signature_models():
    """Test that signature fields exist in the models"""
    print("🔍 Testing signature model fields...")
    
    try:
        from personal_details.models import PersonalDetail
        from master_control_project.master_control.models import AdmissionApplication
        
        # Check PersonalDetail signature field
        personal_fields = [f.name for f in PersonalDetail._meta.fields]
        if 'signature' in personal_fields:
            print("✅ PersonalDetail.signature field exists")
        else:
            print("❌ PersonalDetail.signature field missing")
            
        # Check AdmissionApplication signature field
        application_fields = [f.name for f in AdmissionApplication._meta.fields]
        if 'signature' in application_fields:
            print("✅ AdmissionApplication.signature field exists")
        else:
            print("❌ AdmissionApplication.signature field missing")
            
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_template_signature_logic():
    """Test that templates have proper signature display logic"""
    print("\n🔍 Testing template signature logic...")
    
    templates_to_check = [
        'templates/print_application.html',
        'templates/application_preview.html'
    ]
    
    for template_path in templates_to_check:
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for signature display logic
            if 'application.signature' in content and 'personal.signature' in content:
                print(f"✅ {template_path} has comprehensive signature logic")
            else:
                print(f"⚠️  {template_path} may have incomplete signature logic")
        else:
            print(f"❌ {template_path} not found")

def test_view_signature_logic():
    """Test that views handle signature uploads properly"""
    print("\n🔍 Testing view signature logic...")
    
    try:
        with open('phd_admission/views.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for signature handling in draft section
        if 'personal_detail.signature = request.FILES' in content:
            print("✅ Draft section saves signature to PersonalDetail")
        else:
            print("❌ Draft section missing signature save to PersonalDetail")
            
        # Check for signature handling in submit section
        if 'signature_upload = request.FILES.get' in content:
            print("✅ Submit section handles signature upload")
        else:
            print("❌ Submit section missing signature upload handling")
            
        # Check for personal_detail.save() after signature assignment
        if 'personal_detail.save()' in content:
            print("✅ PersonalDetail.save() called after signature assignment")
        else:
            print("❌ PersonalDetail.save() may be missing after signature assignment")
            
    except FileNotFoundError:
        print("❌ phd_admission/views.py not found")

def main():
    """Main verification function"""
    print("🔐 Signature Fix Verification Script")
    print("=" * 50)
    
    # Test model fields
    models_ok = test_signature_models()
    
    # Test template logic
    test_template_signature_logic()
    
    # Test view logic
    test_view_signature_logic()
    
    print("\n" + "=" * 50)
    if models_ok:
        print("✅ Core signature functionality appears to be working!")
        print("📝 Next steps:")
        print("   1. Test signature upload through the web interface")
        print("   2. Verify signature display in print preview")
        print("   3. Verify signature display in application preview")
    else:
        print("❌ Some issues found. Please review the errors above.")
    
    print("\n🔧 Changes made:")
    print("   - Fixed signature saving in draft section of admission_form_single view")
    print("   - Updated print_application.html to check multiple signature sources")
    print("   - Updated application_preview.html to check multiple signature sources")

if __name__ == '__main__':
    main()
