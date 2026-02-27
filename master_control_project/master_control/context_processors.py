"""
Master Control Context Processors
Global portal data injection for all templates
"""

from django.utils import timezone
from django.db import OperationalError
from .models import Course, Advertisement, Notice, PortalSettings


def global_portal_data(request):
    """
    Context processor to inject global portal data into all templates.
    Provides:
    - Active courses (for admission forms)
    - Currently active advertisements
    - Active notices
    - Portal maintenance mode status
    - Current academic year
    - Portal settings
    """
    today = timezone.now().date()
    
    # Handle case when database tables don't exist yet (migrations not run)
    try:
        # Get portal settings (singleton)
        settings_obj = PortalSettings.objects.first()
        
        # Active courses for admission
        active_courses = Course.objects.filter(
            is_active=True
        ).order_by("display_priority", "course_name")
        
        # Currently active advertisements (date-based + is_active)
        active_ads = Advertisement.objects.filter(
            is_active=True,
            start_date__lte=today,
            end_date__gte=today
        ).order_by("priority")
        
        # Active notices
        active_notices = Notice.objects.filter(
            is_active=True
        ).order_by("priority", "-created_at")
        
    except OperationalError:
        # Database tables don't exist yet - return empty defaults
        settings_obj = None
        active_courses = []
        active_ads = []
        active_notices = []
    
    # Context data
    context = {
        "active_courses": active_courses,
        "active_ads": active_ads,
        "active_notices": active_notices,
        "portal_settings": settings_obj,
        "maintenance_mode": settings_obj.maintenance_mode if settings_obj else False,
        "portal_active": settings_obj.is_portal_active if settings_obj else False,
        "current_academic_year": settings_obj.current_academic_year if settings_obj else "",
        "portal_name": settings_obj.portal_name if settings_obj else "University Portal",
        "contact_email": settings_obj.contact_email if settings_obj else "",
        "support_phone": settings_obj.support_phone if settings_obj else "",
        "today": today,
    }
    
    return context
