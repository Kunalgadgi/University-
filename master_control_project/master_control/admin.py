"""
Master Control Admin Configuration
Production-grade Django Admin customization with full features.
"""

from django.contrib import admin
from django.db.models import Count, Sum
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    PortalSettings, Course, FormConfiguration,
    Advertisement, Notice, HomepageSlider,
    AdvertisementCourse, AdvertisementField, AdvertisementFieldOption,
    AdmissionApplication, ApplicationFieldValue,
    ApplicationProfileSnapshot, ApplicationEducationSnapshot, ApplicationExperienceSnapshot
)


# ──────────────────────────────────────────────────────────────────────────────
# ADMIN ACTIONS
# ──────────────────────────────────────────────────────────────────────────────

@admin.action(description="Activate selected items")
def activate_selected(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description="Deactivate selected items")
def deactivate_selected(modeladmin, request, queryset):
    queryset.update(is_active=False)


# ──────────────────────────────────────────────────────────────────────────────
# BASE ADMIN CONFIG
# ──────────────────────────────────────────────────────────────────────────────

class BaseAdmin(admin.ModelAdmin):
    """Base admin configuration with common features."""
    actions = [activate_selected, deactivate_selected]
    list_filter = ("is_active",)
    date_hierarchy = "created_at"
    
    def get_list_display(self, request):
        """Dynamically add status indicator to list display."""
        base_fields = list(super().get_list_display(request))
        if 'status_indicator' not in base_fields:
            return base_fields + ['status_indicator']
        return base_fields
    
    def status_indicator(self, obj):
        """Visual status indicator for list view."""
        color = "#22c55e" if obj.is_active else "#ef4444"
        status = "Active" if obj.is_active else "Inactive"
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: 600;">{}</span>',
            color, status
        )
    status_indicator.short_description = "Status"


# ──────────────────────────────────────────────────────────────────────────────
# PORTAL SETTINGS ADMIN
# ──────────────────────────────────────────────────────────────────────────────

@admin.register(PortalSettings)
class PortalSettingsAdmin(admin.ModelAdmin):
    """
    Singleton configuration admin.
    Prevents multiple entries and provides full portal control.
    """
    list_display = (
        "portal_name", "current_academic_year", "is_portal_active",
        "maintenance_mode", "application_start_date", "application_end_date"
    )
    list_filter = ("is_portal_active", "maintenance_mode")
    fieldsets = (
        ("Portal Identity", {
            "fields": ("portal_name", "current_academic_year"),
            "description": "Main portal identification settings"
        }),
        ("Portal Status", {
            "fields": ("is_portal_active", "maintenance_mode"),
            "description": "Control portal accessibility and maintenance mode",
            "classes": ("wide",)
        }),
        ("Application Period", {
            "fields": ("application_start_date", "application_end_date"),
            "description": "Define when applications are accepted"
        }),
        ("Contact Information", {
            "fields": ("contact_email", "support_phone"),
            "description": "Public contact details displayed on portal"
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent creating multiple PortalSettings instances."""
        return not PortalSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of portal settings."""
        return False


# ──────────────────────────────────────────────────────────────────────────────
# COURSE ADMIN
# ──────────────────────────────────────────────────────────────────────────────

@admin.register(Course)
class CourseAdmin(BaseAdmin):
    """
    Course management with department aggregation.
    """
    list_display = (
        "course_name", "department_name", "degree_type",
        "duration_years", "total_seats", "display_priority"
    )
    list_filter = ("is_active", "degree_type", "department_name")
    search_fields = ("course_name", "department_name", "degree_type")
    ordering = ("display_priority", "course_name")
    
    fieldsets = (
        ("Course Information", {
            "fields": ("course_name", "department_name", "degree_type")
        }),
        ("Program Details", {
            "fields": ("duration_years", "total_seats", "display_priority")
        }),
        ("Status", {
            "fields": ("is_active",),
            "classes": ("collapse",)
        }),
    )
    
    def get_queryset(self, request):
        """Add department aggregation statistics."""
        qs = super().get_queryset(request)
        return qs


# ──────────────────────────────────────────────────────────────────────────────
# FORM CONFIGURATION ADMIN
# ──────────────────────────────────────────────────────────────────────────────

@admin.register(FormConfiguration)
class FormConfigurationAdmin(BaseAdmin):
    """
    Form availability and payment configuration per course.
    """
    list_display = (
        "course", "is_form_open", "is_payment_required",
        "application_fee", "max_applications_allowed", "date_range"
    )
    list_filter = ("is_form_open", "is_payment_required", "is_active")
    search_fields = ("course__course_name", "course__department_name")
    ordering = ("-created_at",)
    
    def date_range(self, obj):
        """Display form date range."""
        if obj.form_start_date and obj.form_end_date:
            return f"{obj.form_start_date} to {obj.form_end_date}"
        return "No dates set"
    date_range.short_description = "Form Period"
    
    fieldsets = (
        ("Course Selection", {
            "fields": ("course",)
        }),
        ("Form Availability", {
            "fields": ("is_form_open", "form_start_date", "form_end_date")
        }),
        ("Payment Configuration", {
            "fields": ("is_payment_required", "application_fee")
        }),
        ("Application Limits", {
            "fields": ("max_applications_allowed",)
        }),
        ("Status", {
            "fields": ("is_active",),
            "classes": ("collapse",)
        }),
    )


# ──────────────────────────────────────────────────────────────────────────────
# ADVERTISEMENT ADMIN
# ──────────────────────────────────────────────────────────────────────────────

@admin.register(Advertisement)
class AdvertisementAdmin(BaseAdmin):
    """
    Advertisement/Banner management with priority handling.
    """
    list_display = (
        "title", "display_type", "priority", "campaign_period",
        "redirect_url", "is_currently_active"
    )
    list_filter = ("is_active", "display_type", "start_date")
    search_fields = ("title", "description")
    ordering = ("priority", "-created_at")
    date_hierarchy = "start_date"
    
    def campaign_period(self, obj):
        """Display campaign duration."""
        return f"{obj.start_date} to {obj.end_date}"
    campaign_period.short_description = "Campaign Period"
    
    def is_currently_active(self, obj):
        """Check if advertisement is currently active based on dates."""
        active = obj.is_currently_active()
        color = "#22c55e" if active else "#94a3b8"
        status = "Running" if active else "Not Running"
        return format_html(
            '<span style="color: {}; font-weight: 600;">{}</span>',
            color, status
        )
    is_currently_active.short_description = "Currently Active"
    
    fieldsets = (
        ("Advertisement Content", {
            "fields": ("title", "description", "file")
        }),
        ("Display Configuration", {
            "fields": ("display_type", "priority", "redirect_url")
        }),
        ("Campaign Period", {
            "fields": ("start_date", "end_date"),
            "description": "Advertisement will only display between these dates"
        }),
        ("Status", {
            "fields": ("is_active",),
            "classes": ("collapse",)
        }),
    )


class AdvertisementFieldOptionInline(admin.TabularInline):
    model = AdvertisementFieldOption
    extra = 0
    fields = ("value", "label", "display_order", "is_active")
    ordering = ("display_order", "id")


@admin.register(AdvertisementCourse)
class AdvertisementCourseAdmin(BaseAdmin):
    list_display = ("advertisement", "course", "total_seats", "application_fee")
    search_fields = ("advertisement__title", "course__course_name")
    list_filter = ("is_active",)
    ordering = ("-created_at",)


@admin.register(AdvertisementField)
class AdvertisementFieldAdmin(BaseAdmin):
    list_display = (
        "advertisement",
        "course",
        "label",
        "name",
        "field_type",
        "is_required",
        "display_order",
    )
    search_fields = ("advertisement__title", "label", "name")
    list_filter = ("field_type", "is_required", "is_active")
    ordering = ("advertisement", "course", "display_order", "id")
    inlines = [AdvertisementFieldOptionInline]


@admin.action(description="Print selected applications")
def print_applications(modeladmin, request, queryset):
    """Print selected applications"""
    from django.http import HttpResponseRedirect
    
    if queryset.count() == 1:
        # Single application - redirect to print view
        app = queryset.first()
        return HttpResponseRedirect(f"/application_preview/?app={app.id}")
    else:
        # Multiple applications - show message
        modeladmin.message_user(request, "Please select only one application to print.", level='warning')


@admin.register(AdmissionApplication)
class AdmissionApplicationAdmin(BaseAdmin):
    list_display = (
        "application_no",
        "student",
        "advertisement",
        "course",
        "status",
        "is_data_locked",
        "print_status",
        "created_at",
        "print_button",
    )
    search_fields = ("application_no", "student__username", "student__email")
    list_filter = ("status", "is_data_locked", "is_active", "is_printed")
    ordering = ("-created_at",)
    actions = [activate_selected, deactivate_selected, print_applications]
    
    def print_status(self, obj):
        """Show print status with indicator."""
        if obj.is_printed:
            return format_html(
                '<span style="color: #22c55e; font-weight: 600;">'
                '<i class="fas fa-check-circle"></i> Printed<br>'
                '<small>{}</small></span>',
                obj.printed_date.strftime("%d %b %Y") if obj.printed_date else ""
            )
        return format_html(
            '<span style="color: #ef4444; font-weight: 600;">'
            '<i class="fas fa-times-circle"></i> Not Printed</span>'
        )
    print_status.short_description = "Print Status"
    
    def print_button(self, obj):
        """Add print button for each application."""
        return format_html(
            '<a href="/print_application/?app={}" target="_blank" '
            'style="background: #3b82f6; color: white; padding: 4px 8px; '
            'border-radius: 4px; text-decoration: none; font-size: 12px;">'
            '<i class="fas fa-print"></i> Print</a>',
            obj.id
        )
    print_button.short_description = "Print"
    print_button.allow_tags = True


@admin.register(ApplicationFieldValue)
class ApplicationFieldValueAdmin(BaseAdmin):
    list_display = ("application", "field", "created_at")
    search_fields = ("application__application_no", "field__name", "field__label")
    list_filter = ("is_active",)
    ordering = ("-created_at",)


@admin.register(ApplicationProfileSnapshot)
class ApplicationProfileSnapshotAdmin(BaseAdmin):
    list_display = ("application", "first_name", "last_name", "snapshot_created_at")
    search_fields = ("application__application_no", "first_name", "last_name")
    ordering = ("-snapshot_created_at",)


@admin.register(ApplicationEducationSnapshot)
class ApplicationEducationSnapshotAdmin(BaseAdmin):
    list_display = ("application", "qualification", "passing_year", "snapshot_created_at")
    search_fields = ("application__application_no", "qualification", "institution_name")
    ordering = ("-snapshot_created_at",)


@admin.register(ApplicationExperienceSnapshot)
class ApplicationExperienceSnapshotAdmin(BaseAdmin):
    list_display = ("application", "organization_name", "designation", "snapshot_created_at")
    search_fields = ("application__application_no", "organization_name", "designation")
    ordering = ("-snapshot_created_at",)


# ──────────────────────────────────────────────────────────────────────────────
# NOTICE ADMIN
# ──────────────────────────────────────────────────────────────────────────────

@admin.register(Notice)
class NoticeAdmin(BaseAdmin):
    """
    Notice/Announcement management.
    """
    list_display = (
        "title", "priority", "has_attachment", "created_at_display"
    )
    list_filter = ("is_active",)
    search_fields = ("title", "content")
    ordering = ("priority", "-created_at")
    
    def has_attachment(self, obj):
        """Indicate if notice has an attachment."""
        if obj.attachment:
            return format_html(
                '<span style="color: #3b82f6;"><i class="fas fa-paperclip"></i> Yes</span>'
            )
        return format_html('<span style="color: #94a3b8;">No</span>')
    has_attachment.short_description = "Attachment"
    
    def created_at_display(self, obj):
        """Formatted creation date."""
        return obj.created_at.strftime("%d %b %Y, %I:%M %p")
    created_at_display.short_description = "Created"
    
    fieldsets = (
        ("Notice Content", {
            "fields": ("title", "content")
        }),
        ("Attachment (Optional)", {
            "fields": ("attachment",),
            "classes": ("collapse",)
        }),
        ("Display Settings", {
            "fields": ("priority", "is_active")
        }),
    )


# ──────────────────────────────────────────────────────────────────────────────
# HOMEPAGE SLIDER ADMIN
# ──────────────────────────────────────────────────────────────────────────────

@admin.register(HomepageSlider)
class HomepageSliderAdmin(BaseAdmin):
    """
    Homepage carousel/slider management.
    """
    list_display = (
        "title", "subtitle", "priority", "preview_image"
    )
    list_filter = ("is_active",)
    search_fields = ("title", "subtitle")
    ordering = ("priority", "-created_at")
    
    def preview_image(self, obj):
        """Show thumbnail preview in admin list."""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; border-radius: 4px;" />',
                obj.image.url
            )
        return format_html('<span style="color: #94a3b8;">No Image</span>')
    preview_image.short_description = "Preview"
    
    fieldsets = (
        ("Slider Content", {
            "fields": ("title", "subtitle", "image")
        }),
        ("Display Settings", {
            "fields": ("priority", "is_active")
        }),
    )


# ──────────────────────────────────────────────────────────────────────────────
# ADMIN SITE CUSTOMIZATION
# ──────────────────────────────────────────────────────────────────────────────

admin.site.site_header = "University Master Control"
admin.site.site_title = "Master Control Admin"
admin.site.index_title = "University Admission Portal Administration"
