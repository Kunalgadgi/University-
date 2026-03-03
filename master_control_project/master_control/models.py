"""



Master Control Models - Production Grade Django Models



University Admission Portal - Administrative Control System



"""







import os



import logging



from datetime import date



from django.db import models



from django.core.exceptions import ValidationError



from django.utils import timezone



from django.conf import settings







logger = logging.getLogger('master_control')











def upload_path(instance, filename):



    """Dynamic upload path based on model name and environment variable."""



    base_path = os.environ.get("FILE_UPLOAD_PATH", "uploads/")



    return f"{base_path}{instance.__class__.__name__.lower()}/{filename}"











class TimeStampedModel(models.Model):



    """



    Abstract base model providing created_at and updated_at timestamps



    and is_active field for all models.



    """



    created_at = models.DateTimeField(auto_now_add=True, db_index=True)



    updated_at = models.DateTimeField(auto_now=True)



    is_active = models.BooleanField(default=True, db_index=True)







    class Meta:



        abstract = True











# ---------------------------



# 1. PortalSettings (Singleton)



# ---------------------------



class PortalSettings(TimeStampedModel):



    """



    Singleton configuration model for the entire portal.



    Only ONE instance should exist - enforced at model level.



    """



    portal_name = models.CharField(



        max_length=255,



        verbose_name="Portal Name",



        help_text="Name of the university admission portal"



    )



    current_academic_year = models.CharField(



        max_length=20,



        verbose_name="Current Academic Year",



        help_text="e.g., 2024-2025"



    )



    is_portal_active = models.BooleanField(



        default=True,



        verbose_name="Portal Active",



        help_text="Whether the portal is accessible to users"



    )



    maintenance_mode = models.BooleanField(



        default=False,



        verbose_name="Maintenance Mode",



        help_text="When enabled, portal shows maintenance message"



    )



    application_start_date = models.DateField(



        verbose_name="Application Start Date"



    )



    application_end_date = models.DateField(



        verbose_name="Application End Date"



    )



    contact_email = models.EmailField(



        verbose_name="Contact Email",



        help_text="Support email displayed on the portal"



    )



    support_phone = models.CharField(



        max_length=20,



        verbose_name="Support Phone",



        help_text="Support phone number displayed on the portal"



    )







    class Meta:



        verbose_name = "Portal Setting"



        verbose_name_plural = "Portal Settings"



        app_label = 'master_control'







    def clean(self):



        """Validate singleton pattern and date logic."""



        # Singleton enforcement



        if PortalSettings.objects.exclude(id=self.id).exists():



            raise ValidationError("Only one PortalSettings instance is allowed. Please edit the existing configuration.")



        



        # Date validation



        if self.application_start_date and self.application_end_date:



            if self.application_start_date > self.application_end_date:



                raise ValidationError("Application start date must be before end date.")







    def save(self, *args, **kwargs):



        """Override save to log configuration changes."""



        is_new = self.id is None



        super().save(*args, **kwargs)



        



        action = "created" if is_new else "updated"



        logger.info(f"PortalSettings {action}: {self.portal_name} (ID: {self.id})")







    def __str__(self):



        return f"{self.portal_name} - {self.current_academic_year}"











# ---------------------------



# 2. Course



# ---------------------------



class Course(TimeStampedModel):



    """



    Academic course/degree program model.



    Controls which programs are available for admission.



    """



    course_name = models.CharField(



        max_length=255,



        db_index=True,



        verbose_name="Course Name",



        help_text="Name of the academic program"



    )



    department_name = models.CharField(



        max_length=255,



        verbose_name="Department",



        help_text="Department offering this course"



    )



    degree_type = models.CharField(



        max_length=100,



        verbose_name="Degree Type",



        help_text="e.g., B.Tech, M.Sc, Ph.D"



    )



    duration_years = models.PositiveIntegerField(



        verbose_name="Duration (Years)",



        help_text="Program duration in years"



    )



    total_seats = models.PositiveIntegerField(



        verbose_name="Total Seats",



        help_text="Total available seats for this course"



    )



    display_priority = models.PositiveIntegerField(



        default=0,



        verbose_name="Display Priority",



        help_text="Lower number = appears first on frontend"



    )







    class Meta:



        ordering = ["display_priority", "course_name"]



        verbose_name = "Course"



        verbose_name_plural = "Courses"



        indexes = [



            models.Index(fields=["course_name", "is_active"]),



            models.Index(fields=["department_name", "is_active"]),



        ]







    def clean(self):



        """Validate course data."""



        if self.total_seats == 0:



            raise ValidationError("Total seats must be greater than zero.")







    def save(self, *args, **kwargs):



        """Log course changes."""



        is_new = self.id is None



        super().save(*args, **kwargs)



        



        action = "created" if is_new else "updated"



        logger.info(f"Course {action}: {self.course_name} - {self.department_name}")







    def __str__(self):



        return f"{self.course_name} ({self.degree_type})"











# ---------------------------



# 3. FormConfiguration



# ---------------------------



class FormConfiguration(TimeStampedModel):



    """



    Controls form availability, payment settings, and application limits



    for each course.



    """



    course = models.ForeignKey(



        Course,



        on_delete=models.CASCADE,



        related_name="form_configs",



        verbose_name="Course",



        help_text="Course this form configuration applies to"



    )



    is_form_open = models.BooleanField(



        default=False,



        verbose_name="Form Open",



        help_text="Whether applications are currently being accepted"



    )



    is_payment_required = models.BooleanField(



        default=True,



        verbose_name="Payment Required",



        help_text="Whether application fee payment is mandatory"



    )



    application_fee = models.DecimalField(



        max_digits=10,



        decimal_places=2,



        default=0.00,



        verbose_name="Application Fee (₹)",



        help_text="Fee amount in INR"



    )



    max_applications_allowed = models.PositiveIntegerField(



        default=100,



        verbose_name="Max Applications",



        help_text="Maximum number of applications to accept"



    )



    form_start_date = models.DateField(



        null=True,



        blank=True,



        verbose_name="Form Start Date",



        help_text="Date when form opens for applications"



    )



    form_end_date = models.DateField(



        null=True,



        blank=True,



        verbose_name="Form End Date",



        help_text="Date when form closes for applications"



    )







    class Meta:



        verbose_name = "Form Configuration"



        verbose_name_plural = "Form Configurations"



        unique_together = ["course"]  # One config per course







    def clean(self):



        """Validate form configuration dates and logic."""



        if self.form_start_date and self.form_end_date:



            if self.form_start_date > self.form_end_date:



                raise ValidationError("Form start date must be before end date.")







    def is_currently_open(self):



        """Check if form is currently open based on dates and is_form_open flag."""



        today = date.today()



        



        if not self.is_form_open:



            return False



            



        if self.form_start_date and self.form_end_date:



            return self.form_start_date <= today <= self.form_end_date



            



        return True







    def save(self, *args, **kwargs):



        """Log form configuration changes."""



        is_new = self.id is None



        super().save(*args, **kwargs)



        



        action = "created" if is_new else "updated"



        status = "OPEN" if self.is_form_open else "CLOSED"



        logger.info(f"FormConfig {action}: {self.course.course_name} - Status: {status}")







    def __str__(self):



        return f"Form Config - {self.course.course_name}"











# ---------------------------



# 4. Advertisement



# ---------------------------



class Advertisement(TimeStampedModel):



    """



    Advertisement/Banner model for displaying promotional content.



    Supports multiple display types: banner, sidebar, notice.



    """



    DISPLAY_TYPE_CHOICES = [



        ("banner", "Banner"),



        ("sidebar", "Sidebar"),



        ("notice", "Notice"),



    ]







    title = models.CharField(



        max_length=255,



        db_index=True,



        verbose_name="Advertisement Title"



    )



    description = models.TextField(



        blank=True,



        verbose_name="Description",



        help_text="Brief description of the advertisement"



    )



    file = models.FileField(



        upload_to=upload_path,



        null=True,



        blank=True,



        verbose_name="Advertisement File",



        help_text="Upload advertisement file (PDF recommended for best results)"



    )



    redirect_url = models.URLField(



        blank=True,



        verbose_name="Redirect URL",



        help_text="URL to redirect when clicked"



    )



    display_type = models.CharField(



        max_length=20,



        choices=DISPLAY_TYPE_CHOICES,



        default="banner",



        verbose_name="Display Type",



        help_text="Where to display this advertisement"



    )



    priority = models.PositiveIntegerField(



        default=0,



        verbose_name="Priority",



        help_text="Lower number = displayed first"



    )



    start_date = models.DateField(



        verbose_name="Start Date",



        help_text="Date when advertisement becomes visible"



    )



    end_date = models.DateField(



        verbose_name="End Date",



        help_text="Date when advertisement expires"



    )







    class Meta:



        ordering = ["priority", "-created_at"]



        verbose_name = "Advertisement"



        verbose_name_plural = "Advertisements"



        indexes = [



            models.Index(fields=["priority", "is_active", "display_type"]),



            models.Index(fields=["start_date", "end_date", "is_active"]),



        ]







    def clean(self):



        """Validate advertisement data including date ranges."""



        if self.start_date and self.end_date:



            if self.start_date > self.end_date:



                raise ValidationError("Start date must be before end date.")







    def is_currently_active(self):



        """Check if advertisement should be displayed today."""



        today = date.today()



        return (



            self.is_active 



            and self.start_date <= today <= self.end_date



        )







    def save(self, *args, **kwargs):



        """Log advertisement changes."""



        is_new = self.id is None



        super().save(*args, **kwargs)



        



        action = "created" if is_new else "updated"



        logger.info(f"Advertisement {action}: {self.title} (Type: {self.display_type})")







    def __str__(self):



        return f"{self.title} ({self.display_type})"











class AdvertisementCourse(TimeStampedModel):



    advertisement = models.ForeignKey(



        Advertisement,



        on_delete=models.CASCADE,



        related_name="advertisement_courses",



    )



    course = models.ForeignKey(



        "Course",



        on_delete=models.CASCADE,



        related_name="advertisement_courses",



    )



    total_seats = models.PositiveIntegerField(default=0)



    application_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)







    class Meta:



        unique_together = ["advertisement", "course"]



        indexes = [



            models.Index(fields=["advertisement", "course", "is_active"]),



        ]







    def __str__(self):



        return f"{self.advertisement.title} -> {self.course.course_name}"











class AdvertisementField(TimeStampedModel):



    FIELD_TYPE_CHOICES = [



        ("text", "Text"),



        ("textarea", "Textarea"),



        ("number", "Number"),



        ("date", "Date"),



        ("select", "Select"),



        ("radio", "Radio"),



        ("checkbox", "Checkbox"),



        ("boolean", "Boolean"),



        ("file", "File"),



    ]







    CONDITIONAL_OPERATOR_CHOICES = [



        ("equals", "Equals"),



        ("not_equals", "Not Equals"),



        ("in", "In"),



        ("not_in", "Not In"),



        ("exists", "Exists"),



        ("not_exists", "Not Exists"),



    ]







    advertisement = models.ForeignKey(



        Advertisement,



        on_delete=models.CASCADE,



        related_name="fields",



    )



    course = models.ForeignKey(



        "Course",



        on_delete=models.CASCADE,



        null=True,



        blank=True,



        related_name="advertisement_fields",



    )







    label = models.CharField(max_length=255)



    name = models.SlugField(max_length=80)



    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES, default="text")



    help_text = models.CharField(max_length=500, blank=True)







    is_required = models.BooleanField(default=False)



    display_order = models.PositiveIntegerField(default=0)







    conditional_field_name = models.SlugField(max_length=80, null=True, blank=True)



    conditional_operator = models.CharField(



        max_length=20,



        choices=CONDITIONAL_OPERATOR_CHOICES,



        null=True,



        blank=True,



    )



    conditional_value = models.CharField(max_length=255, null=True, blank=True)







    class Meta:



        constraints = [



            models.UniqueConstraint(



                fields=["advertisement", "name"],



                name="uniq_advertisement_field_name",



            )



        ]



        indexes = [



            models.Index(fields=["advertisement", "course", "is_active"]),



            models.Index(fields=["advertisement", "display_order"]),



        ]







    def __str__(self):



        return f"{self.advertisement.title}: {self.label}"











class AdvertisementFieldOption(TimeStampedModel):



    field = models.ForeignKey(



        AdvertisementField,



        on_delete=models.CASCADE,



        related_name="options",



    )



    value = models.CharField(max_length=255)



    label = models.CharField(max_length=255)



    display_order = models.PositiveIntegerField(default=0)







    class Meta:



        indexes = [



            models.Index(fields=["field", "display_order"]),



        ]







    def __str__(self):



        return f"{self.field.name}: {self.label}"











class AdmissionApplication(TimeStampedModel):



    STATUS_CHOICES = [



        ("draft", "Draft"),



        ("submitted", "Submitted"),



        ("payment_pending", "Payment Pending"),



        ("payment_success", "Payment Success"),



        ("under_review", "Under Review"),



        ("admitted", "Admitted"),



        ("rejected", "Rejected"),



    ]







    application_no = models.CharField(max_length=30, unique=True, db_index=True)



    student = models.ForeignKey(



        settings.AUTH_USER_MODEL,



        on_delete=models.PROTECT,



        related_name="admission_applications",



    )



    advertisement = models.ForeignKey(



        Advertisement,



        on_delete=models.PROTECT,



        related_name="applications",



    )



    course = models.ForeignKey(



        "Course",



        on_delete=models.PROTECT,



        related_name="applications",



    )



    department_name = models.CharField(max_length=255, blank=True, default="")



    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="draft", db_index=True)



    is_data_locked = models.BooleanField(default=False, db_index=True)



    submitted_at = models.DateTimeField(null=True, blank=True)


    # 1. APPLY COURSE (moved to top to match form order)
    apply_course = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ('Ph.D.', 'Ph.D.'),
            ('PGDRP', 'PGDRP'),
        ],
        help_text="Select course to apply for"
    )

    # DEPARTMENT FIELD (For Ph.D. selection)
    department = models.CharField(
        max_length=100,
        blank=True,
        choices=[
            ('Physical Education', 'Physical Education'),
            ('Zoology', 'Zoology'),
            ('Commerce', 'Commerce'),
            ('Biotechnology', 'Biotechnology'),
            ('Physics', 'Physics'),
            ('Pharmaceutical', 'Pharmaceutical'),
            ('Psychology', 'Psychology'),
            ('History', 'History'),
            ('Chemistry', 'Chemistry'),
            ('Management', 'Management'),
            ('Math', 'Math'),
            ('English', 'English'),
        ],
        help_text="Select department for Ph.D. program"
    )

    # STUDY MODE FIELD (For Ph.D. selection)
    study_mode = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ('Full Time', 'Full Time'),
            ('Part Time', 'Part Time'),
        ],
        help_text="Select study mode for Ph.D. program"
    )

    # 2. PERSONAL INFORMATION

    first_name = models.CharField(max_length=100, blank=True)

    last_name = models.CharField(max_length=100, blank=True)

    full_name = models.CharField(max_length=200, blank=True)

    date_of_birth = models.DateField(null=True, blank=True)

    gender = models.CharField(max_length=10, blank=True)

    father_name = models.CharField(max_length=100, blank=True)

    mother_name = models.CharField(max_length=100, blank=True)

    marital_status = models.CharField(max_length=20, blank=True)

    nationality = models.CharField(max_length=50, blank=True)

    aadhar_number = models.CharField(max_length=20, blank=True)

    # 3. CONTACT INFORMATION
    mobile_number = models.CharField(max_length=20, blank=True)

    email = models.EmailField(blank=True)

    mobile_telephone = models.CharField(max_length=20, blank=True)

    email_correspondence = models.EmailField(blank=True)

    # 4. ADDRESS INFORMATION
    permanent_address = models.TextField(blank=True)

    current_address = models.TextField(blank=True)

    corr_address_block = models.TextField(blank=True)

    district = models.CharField(max_length=100, blank=True)

    state = models.CharField(max_length=100, blank=True)

    pincode = models.CharField(max_length=10, blank=True)

    # 5. CATEGORY INFORMATION
    category = models.CharField(max_length=50, blank=True)

    category_tick = models.CharField(max_length=50, blank=True)

    category_other = models.CharField(max_length=100, blank=True)

    # UGC CATEGORY (as per UGC notification regarding NET as entrance test 27.03.2024)
    ugc_category = models.CharField(
        max_length=50, 
        blank=True,
        choices=[
            ('Category I (JRF)', 'Category I (JRF)'),
            ('Category II (NET)', 'Category II (NET)'),
            ('Category III (Ph.D. Only)', 'Category III (Ph.D. Only)'),
            ('Not Applicable', 'Not Applicable'),
        ],
        help_text="UGC category as per NET entrance test notification"
    )
    ugc_validity_date = models.DateField(
        null=True, 
        blank=True,
        help_text="UGC validity date for NET/JRF certificate"
    )

    # 6. SPECIALIZATION AND ACADEMIC DETAILS
    specialization_area = models.TextField(blank=True)

    proposed_supervisor = models.TextField(blank=True)

    # 7. FELLOWSHIP DETAILS
    fellowship_validity = models.DateField(null=True, blank=True)

    fellowship_category = models.CharField(max_length=100, blank=True)

    # 8. EMPLOYMENT DETAILS
    employed_status = models.CharField(max_length=10, blank=True)

    emp_post_current = models.CharField(max_length=200, blank=True)

    job_nature = models.CharField(max_length=100, blank=True)

    date_of_joining = models.DateField(null=True, blank=True)

    service_period = models.CharField(max_length=100, blank=True)

    organization_name_current = models.CharField(max_length=200, blank=True)

    organization_address = models.TextField(blank=True)

    org_telephone = models.CharField(max_length=20, blank=True)

    org_email = models.EmailField(blank=True)

    # 9. RESEARCH AND PUBLICATIONS
    research_experience = models.TextField(blank=True)

    publications = models.TextField(blank=True)

    # 10. OTHER COURSE INFORMATION
    pursuing_other_course = models.CharField(max_length=10, blank=True)

    other_institution = models.CharField(max_length=200, blank=True)

    other_class = models.CharField(max_length=100, blank=True)

    other_session = models.CharField(max_length=50, blank=True)

    other_result = models.CharField(max_length=50, blank=True)

    # 11. SIGNATURE INFORMATION
    # signature_name field handled via property/method
    
    # 12. PAYMENT INFORMATION
    payment_date = models.DateField(null=True, blank=True, verbose_name="Payment Date", help_text="Date when payment was made")

    payment_id = models.CharField(max_length=100, blank=True, verbose_name="Payment ID", help_text="Payment transaction ID")

    # 13. DOCUMENT UPLOADS (SOP Certificates)
    # No Objection cum Service Certificate from employer (SOP-II)
    no_objection_certificate = models.FileField(
        upload_to='applications/documents/no_objection/', 
        null=True, 
        blank=True, 
        verbose_name="No Objection cum Service Certificate (SOP-II)",
        help_text="Required for employed candidates"
    )

    # Certificate from Father/Guardian (SOP-III)
    father_guardian_certificate = models.FileField(
        upload_to='applications/documents/father_guardian/', 
        null=True, 
        blank=True, 
        verbose_name="Certificate from Father/Guardian (SOP-III)"
    )

    # Affidavit of parent/guardian (SOP-IV)
    parent_guardian_affidavit = models.FileField(
        upload_to='applications/documents/affidavit/', 
        null=True, 
        blank=True, 
        verbose_name="Affidavit of Parent/Guardian (SOP-IV)",
        help_text="Attested by executive magistrate/oath commissioner/notary public"
    )

    # Character Certificate (SOP-V)
    character_certificate = models.FileField(
        upload_to='applications/documents/character/', 
        null=True, 
        blank=True, 
        verbose_name="Character Certificate (SOP-V)",
        help_text="Required if there is gap in study"
    )

    # Category Certificate (SOP-VI to SOP-XI)
    category_certificate = models.FileField(
        upload_to='applications/documents/category/', 
        null=True, 
        blank=True, 
        verbose_name="Category Certificate (SOP-VI to SOP-XI)",
        help_text="SC/ST/BC/EWS/SBC/PwD/ESM/Others certificate in Govt. format"
    )

    # Haryana Domicile Certificate
    haryana_domicile_certificate = models.FileField(
        upload_to='applications/documents/domicile/', 
        null=True, 
        blank=True, 
        verbose_name="Haryana Domicile Certificate"
    )

    # NRI/Foreign Citizen Declaration (SOP-XII)
    nri_declaration = models.FileField(
        upload_to='applications/documents/nri/', 
        null=True, 
        blank=True, 
        verbose_name="NRI/Foreign Citizen Declaration (SOP-XII)"
    )

    # Migration Certificate
    migration_certificate = models.FileField(
        upload_to='applications/documents/migration/', 
        null=True, 
        blank=True, 
        verbose_name="Migration Certificate"
    )

    # ACADEMIC QUALIFICATIONS (JSON)
    academic_data = models.JSONField(default=dict, blank=True, help_text="Stores all academic qualifications as JSON")

    # EMPLOYMENT HISTORY (JSON)
    employment_history = models.JSONField(default=dict, blank=True, help_text="Stores all employment history as JSON")

    # FILES
    photo = models.ImageField(upload_to='applications/photos/', null=True, blank=True)

    signature = models.ImageField(upload_to='applications/signatures/', null=True, blank=True)

    # PRINT STATUS



    is_printed = models.BooleanField(default=False, help_text="Mark if application has been printed")



    printed_date = models.DateTimeField(null=True, blank=True)



    printed_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='printed_applications')







    class Meta:



        indexes = [



            models.Index(fields=["student", "status"]),



            models.Index(fields=["advertisement", "course"]),



            models.Index(fields=["application_no"]),



            models.Index(fields=["-created_at"]),



            models.Index(fields=["category"]),



            models.Index(fields=["is_printed"]),



        ]







    def lock(self):



        if not self.is_data_locked:



            self.is_data_locked = True



            self.save(update_fields=["is_data_locked", "updated_at"])







    def get_academic_qualifications(self):



        """Parse academic data JSON into readable format"""



        return self.academic_data.get('qualifications', [])







    def get_employment_history(self):



        """Parse employment history JSON into readable format"""



        return self.employment_history.get('employments', [])







    def mark_as_printed(self, user):



        """Mark application as printed"""



        self.is_printed = True



        self.printed_date = timezone.now()



        self.printed_by = user



        self.save()







    def __str__(self):



        return f"{self.application_no} - {self.full_name or self.student.username}"











class ApplicationFieldValue(TimeStampedModel):



    application = models.ForeignKey(



        AdmissionApplication,



        on_delete=models.CASCADE,



        related_name="field_values",



    )



    field = models.ForeignKey(



        AdvertisementField,



        on_delete=models.PROTECT,



        related_name="application_values",



    )



    field_snapshot = models.JSONField(default=dict)



    value_text = models.TextField(blank=True)



    value_file = models.FileField(upload_to=upload_path, null=True, blank=True)







    class Meta:



        constraints = [



            models.UniqueConstraint(



                fields=["application", "field"],



                name="uniq_application_field_value",



            )



        ]



        indexes = [



            models.Index(fields=["application", "field"]),



        ]







    def __str__(self):



        return f"{self.application.application_no}: {self.field.name}"











class ApplicationProfileSnapshot(TimeStampedModel):



    application = models.ForeignKey(



        AdmissionApplication,



        on_delete=models.CASCADE,



        related_name="profile_snapshots",



    )







    first_name = models.CharField(max_length=100, blank=True, default="")



    last_name = models.CharField(max_length=100, blank=True, default="")



    father_name = models.CharField(max_length=100, blank=True, default="")



    mother_name = models.CharField(max_length=100, blank=True, default="")



    dob = models.DateField(null=True, blank=True)



    gender = models.CharField(max_length=10, blank=True, default="")



    marital_status = models.CharField(max_length=20, blank=True, default="")



    nationality = models.CharField(max_length=50, blank=True, default="")



    aadhar_no = models.CharField(max_length=20, blank=True, default="")



    category = models.CharField(max_length=50, blank=True, default="")



    category_tick = models.CharField(max_length=20, blank=True, default="")



    category_other = models.CharField(max_length=50, blank=True, default="")



    address = models.TextField(blank=True, default="")



    corr_address_block = models.TextField(blank=True, default="")



    state = models.CharField(max_length=50, blank=True, default="")



    district = models.CharField(max_length=50, blank=True, default="")



    pincode = models.CharField(max_length=10, blank=True, default="")



    mobile_number = models.CharField(max_length=20, blank=True, default="")



    mobile_telephone = models.CharField(max_length=20, blank=True, default="")



    email = models.EmailField(blank=True, default="")



    email_correspondence = models.EmailField(blank=True, default="")



    specialization_area = models.CharField(max_length=200, blank=True, default="")



    proposed_supervisor = models.CharField(max_length=200, blank=True, default="")



    fellowship_validity = models.DateField(null=True, blank=True)



    fellowship_category = models.CharField(max_length=50, blank=True, default="")



    employed_status = models.CharField(max_length=10, blank=True, default="")



    emp_post_current = models.CharField(max_length=200, blank=True, default="")



    job_nature = models.CharField(max_length=20, blank=True, default="")



    date_of_joining = models.DateField(null=True, blank=True)



    service_period = models.CharField(max_length=50, blank=True, default="")



    organization_name_current = models.CharField(max_length=200, blank=True, default="")



    organization_address = models.TextField(blank=True, default="")



    org_telephone = models.CharField(max_length=20, blank=True, default="")



    org_email = models.EmailField(blank=True, default="")



    research_experience = models.TextField(blank=True, default="")



    publications = models.TextField(blank=True, default="")



    pursuing_other_course = models.CharField(max_length=10, blank=True, default="")



    other_institution = models.CharField(max_length=200, blank=True, default="")



    other_class = models.CharField(max_length=100, blank=True, default="")



    other_session = models.CharField(max_length=50, blank=True, default="")



    other_result = models.CharField(max_length=50, blank=True, default="")



    photo = models.ImageField(upload_to=upload_path, null=True, blank=True)



    signature = models.ImageField(upload_to=upload_path, null=True, blank=True)







    snapshot_created_at = models.DateTimeField(auto_now_add=True, db_index=True)







    class Meta:



        verbose_name = "Application Profile Snapshot"



        verbose_name_plural = "Application Profile Snapshots"







    def __str__(self):



        return f"Profile Snapshot: {self.application.application_no}"











class ApplicationEducationSnapshot(TimeStampedModel):



    application = models.ForeignKey(



        AdmissionApplication,



        on_delete=models.CASCADE,



        related_name="education_snapshots",



    )







    qualification = models.CharField(max_length=255, blank=True, default="")



    board_university = models.CharField(max_length=255, blank=True, default="")



    institution_name = models.CharField(max_length=255, blank=True, default="")



    passing_year = models.CharField(max_length=10, blank=True, default="")



    roll_number = models.CharField(max_length=50, blank=True, default="")



    percentage = models.CharField(max_length=20, blank=True, default="")



    cgpa = models.CharField(max_length=20, blank=True, default="")



    subjects = models.TextField(blank=True, default="")



    document_file = models.FileField(upload_to=upload_path, null=True, blank=True)







    snapshot_created_at = models.DateTimeField(auto_now_add=True, db_index=True)







    class Meta:



        verbose_name = "Application Education Snapshot"



        verbose_name_plural = "Application Education Snapshots"



        indexes = [



            models.Index(fields=["application", "snapshot_created_at"]),



        ]







    def __str__(self):



        return f"Education Snapshot: {self.application.application_no}"











class ApplicationExperienceSnapshot(TimeStampedModel):



    application = models.ForeignKey(



        AdmissionApplication,



        on_delete=models.CASCADE,



        related_name="experience_snapshots",



    )







    organization_name = models.CharField(max_length=255, blank=True, default="")



    designation = models.CharField(max_length=255, blank=True, default="")



    from_date = models.DateField(null=True, blank=True)



    to_date = models.DateField(null=True, blank=True)



    experience_type = models.CharField(max_length=100, blank=True, default="")



    remarks = models.TextField(blank=True, default="")



    document_file = models.FileField(upload_to=upload_path, null=True, blank=True)







    snapshot_created_at = models.DateTimeField(auto_now_add=True, db_index=True)







    class Meta:



        verbose_name = "Application Experience Snapshot"



        verbose_name_plural = "Application Experience Snapshots"



        indexes = [



            models.Index(fields=["application", "snapshot_created_at"]),



        ]







    def __str__(self):



        return f"Experience Snapshot: {self.application.application_no}"











# ---------------------------



# 5. Notice



# ---------------------------



class Notice(TimeStampedModel):



    """



    Notice/Announcement model for displaying important updates



    on the homepage.



    """



    title = models.CharField(



        max_length=255,



        db_index=True,



        verbose_name="Notice Title"



    )



    content = models.TextField(



        verbose_name="Notice Content",



        help_text="Full notice text"



    )



    attachment = models.FileField(



        upload_to=upload_path,



        null=True,



        blank=True,



        verbose_name="Attachment",



        help_text="Optional PDF, DOC, or image attachment"



    )



    priority = models.PositiveIntegerField(



        default=0,



        verbose_name="Priority",



        help_text="Lower number = displayed first on homepage"



    )







    class Meta:



        ordering = ["priority", "-created_at"]



        verbose_name = "Notice"



        verbose_name_plural = "Notices"



        indexes = [



            models.Index(fields=["priority", "is_active"]),



        ]







    def save(self, *args, **kwargs):



        """Log notice changes."""



        is_new = self.id is None



        super().save(*args, **kwargs)



        



        action = "created" if is_new else "updated"



        logger.info(f"Notice {action}: {self.title}")







    def __str__(self):



        return self.title











# ---------------------------



# 6. HomepageSlider



# ---------------------------



class HomepageSlider(TimeStampedModel):



    """



    Homepage slider/banner carousel model for showcasing



    featured content and images.



    """



    title = models.CharField(



        max_length=255,



        verbose_name="Slider Title",



        help_text="Main headline for the slider"



    )



    subtitle = models.CharField(



        max_length=255,



        blank=True,



        verbose_name="Subtitle",



        help_text="Supporting text below the title"



    )



    image = models.ImageField(



        upload_to=upload_path,



        verbose_name="Slider Image",



        help_text="Upload slider image (Recommended: 1920x600px)"



    )



    priority = models.PositiveIntegerField(



        default=0,



        verbose_name="Priority",



        help_text="Display order - lower number appears first"



    )







    class Meta:



        ordering = ["priority", "-created_at"]



        verbose_name = "Homepage Slider"



        verbose_name_plural = "Homepage Sliders"



        indexes = [



            models.Index(fields=["priority", "is_active"]),



        ]







    def save(self, *args, **kwargs):



        """Log slider changes."""



        is_new = self.id is None



        super().save(*args, **kwargs)



        



        action = "created" if is_new else "updated"



        logger.info(f"HomepageSlider {action}: {self.title}")







    def __str__(self):



        return f"{self.title} (Priority: {self.priority})"



