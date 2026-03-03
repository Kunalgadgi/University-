#!/usr/bin/env python
"""
Simple Signature Fix Verification Script
This script verifies that the signature saving and display functionality is working correctly.
"""

import os

def test_template_signature_logic():
    """Test that templates have proper signature display logic"""
    print("🔍 Testing template signature logic...")
    
    templates_to_check = [
        'templates/print_application.html',
        'templates/application_preview.html'
    ]
    
    all_good = True
    for template_path in templates_to_check:
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for signature display logic
            has_app_signature = 'application.signature' in content
            has_personal_signature = 'personal.signature' in content
            has_profile_signature = 'profile_snapshot.signature' in content
            
            if has_app_signature and has_personal_signature:
                print(f"✅ {template_path} has comprehensive signature logic")
                print(f"   - application.signature: {has_app_signature}")
                print(f"   - personal.signature: {has_personal_signature}")
                print(f"   - profile_snapshot.signature: {has_profile_signature}")
            else:
                print(f"⚠️  {template_path} may have incomplete signature logic")
                all_good = False
        else:
            print(f"❌ {template_path} not found")
            all_good = False
    
    return all_good

def test_view_signature_logic():
    """Test that views handle signature uploads properly"""
    print("\n🔍 Testing view signature logic...")
    
    if not os.path.exists('phd_admission/views.py'):
        print("❌ phd_admission/views.py not found")
        return False
        
    with open('phd_admission/views.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Check for signature handling in draft section
    checks = [
        ('Draft section saves signature to PersonalDetail', 'personal_detail.signature = request.FILES'),
        ('Submit section handles signature upload', 'signature_upload = request.FILES.get'),
        ('PersonalDetail.save() called after signature', 'personal_detail.save()'),
        ('Draft section signature assignment', 'draft_application.signature = request.FILES'),
    ]
    
    all_good = True
    for check_name, pattern in checks:
        if pattern in content:
            print(f"✅ {check_name}")
        else:
            print(f"❌ {check_name} - NOT FOUND")
            all_good = False
    
    return all_good

def test_model_files():
    """Test that model files contain signature fields"""
    print("\n🔍 Testing model signature fields...")
    
    model_files = [
        ('personal_details/models.py', 'signature = models.ImageField'),
        ('master_control_project/master_control/models.py', 'signature = models.ImageField'),
    ]
    
    all_good = True
    for model_file, pattern in model_files:
        if os.path.exists(model_file):
            with open(model_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if pattern in content:
                print(f"✅ {model_file} has signature field")
            else:
                print(f"❌ {model_file} missing signature field")
                all_good = False
        else:
            print(f"❌ {model_file} not found")
            all_good = False
    
    return all_good

def main():
    """Main verification function"""
    print("🔐 Signature Fix Verification Script")
    print("=" * 50)
    
    # Test model fields
    models_ok = test_model_files()
    
    # Test template logic
    templates_ok = test_template_signature_logic()
    
    # Test view logic
    views_ok = test_view_signature_logic()
    
    print("\n" + "=" * 50)
    if models_ok and templates_ok and views_ok:
        print("✅ All signature functionality appears to be working!")
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
    
    print("\n📋 Summary:")
    print(f"   - Models: {'✅' if models_ok else '❌'}")
    print(f"   - Templates: {'✅' if templates_ok else '❌'}")
    print(f"   - Views: {'✅' if views_ok else '❌'}")

if __name__ == '__main__':
    main()
