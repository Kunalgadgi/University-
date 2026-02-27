from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from personal_details.models import PersonalDetail

class Command(BaseCommand):
    help = 'Check personal information data in database'

    def handle(self, *args, **options):
        self.stdout.write('=== Personal Information Data in Database ===\n')
        
        # Get all users
        users = User.objects.all()
        self.stdout.write(f'Total users: {users.count()}')
        
        for user in users:
            self.stdout.write(f'\n--- User: {user.username} ({user.email}) ---')
            
            try:
                personal_detail = PersonalDetail.objects.get(user=user)
                self.stdout.write(f'✅ PersonalDetail found:')
                self.stdout.write(f'  First Name: {personal_detail.first_name}')
                self.stdout.write(f'  Last Name: {personal_detail.last_name}')
                self.stdout.write(f'  Email: {personal_detail.email}')
                self.stdout.write(f'  Mobile: {personal_detail.mobile_number}')
                self.stdout.write(f'  Date of Birth: {personal_detail.date_of_birth}')
                self.stdout.write(f'  Gender: {personal_detail.gender}')
                self.stdout.write(f'  Blood Group: {personal_detail.blood_group}')
                self.stdout.write(f'  Marital Status: {personal_detail.marital_status}')
                self.stdout.write(f'  Nationality: {personal_detail.nationality}')
                self.stdout.write(f'  Current Address: {personal_detail.current_address}')
                self.stdout.write(f'  Permanent Address: {personal_detail.permanent_address}')
                self.stdout.write(f'  City: {personal_detail.city}')
                self.stdout.write(f'  State: {personal_detail.state}')
                self.stdout.write(f'  Pincode: {personal_detail.pincode}')
                self.stdout.write(f'  Country: {personal_detail.country}')
                self.stdout.write(f'  Emergency Contact: {personal_detail.emergency_contact_name}')
                self.stdout.write(f'  Emergency Phone: {personal_detail.emergency_contact_number}')
                self.stdout.write(f'  Emergency Relation: {personal_detail.emergency_contact_relation}')
                if personal_detail.photo:
                    self.stdout.write(f'  Photo: ✅ Uploaded ({personal_detail.photo})')
                else:
                    self.stdout.write(f'  Photo: ❌ Not uploaded')
                    
            except PersonalDetail.DoesNotExist:
                self.stdout.write(f'❌ No PersonalDetail found for this user')
        
        self.stdout.write('\n=== Summary ===')
        total_personal_details = PersonalDetail.objects.count()
        self.stdout.write(f'Total PersonalDetail records: {total_personal_details}')
        
        # Check photos
        with_photos = PersonalDetail.objects.exclude(photo__isnull=True).exclude(photo='').count()
        self.stdout.write(f'Records with photos: {with_photos}')
