"""
Master Control Views - Admin-only secured views
Dashboard with department-wise visual reports and analytics
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.contrib import messages
from django.forms import ModelForm
import json
from .models import (
    PortalSettings, Course, FormConfiguration,
    Advertisement, Notice, HomepageSlider
)


@staff_member_required
def dashboard(request):
    """
    Main admin dashboard with department-wise visual reports.
    Includes charts, statistics, and analytics cards.
    """
    today = timezone.now().date()
    
    # ─────────────────────────────────────────────────────────────────────────
    # DEPARTMENT-WISE ANALYTICS
    # ─────────────────────────────────────────────────────────────────────────
    department_data = (
        Course.objects.filter(is_active=True)
        .values("department_name")
        .annotate(
            total_courses=Count("id"),
            total_seats=Sum("total_seats"),
            active_forms=Count(
                "form_configs",
                filter=Q(form_configs__is_form_open=True, form_configs__is_active=True)
            )
        )
        .order_by("department_name")
    )
    
    # Prepare chart data
    labels = [item["department_name"] for item in department_data]
    course_counts = [item["total_courses"] for item in department_data]
    seat_counts = [item["total_seats"] for item in department_data]
    
    # ─────────────────────────────────────────────────────────────────────────
    # OVERALL STATISTICS
    # ─────────────────────────────────────────────────────────────────────────
    stats = {
        # Course statistics
        "total_courses": Course.objects.count(),
        "active_courses": Course.objects.filter(is_active=True).count(),
        "total_seats": Course.objects.aggregate(total=Sum("total_seats"))["total"] or 0,
        
        # Form configuration statistics
        "total_forms": FormConfiguration.objects.count(),
        "open_forms": FormConfiguration.objects.filter(
            is_form_open=True, is_active=True
        ).count(),
        "payment_required_forms": FormConfiguration.objects.filter(
            is_payment_required=True, is_active=True
        ).count(),
        
        # Advertisement statistics
        "total_ads": Advertisement.objects.count(),
        "active_ads": Advertisement.objects.filter(
            is_active=True,
            start_date__lte=today,
            end_date__gte=today
        ).count(),
        "banner_ads": Advertisement.objects.filter(
            display_type="banner", is_active=True
        ).count(),
        "sidebar_ads": Advertisement.objects.filter(
            display_type="sidebar", is_active=True
        ).count(),
        
        # Notice statistics
        "total_notices": Notice.objects.count(),
        "active_notices": Notice.objects.filter(is_active=True).count(),
        
        # Slider statistics
        "total_sliders": HomepageSlider.objects.count(),
        "active_sliders": HomepageSlider.objects.filter(is_active=True).count(),
        
        # Portal status
        "portal_active": PortalSettings.objects.filter(
            is_portal_active=True, maintenance_mode=False
        ).exists(),
    }
    
    # ─────────────────────────────────────────────────────────────────────────
    # RECENT ACTIVITY (Last 5 items of each type)
    # ─────────────────────────────────────────────────────────────────────────
    recent_activity = {
        "recent_courses": Course.objects.order_by("-created_at")[:5],
        "recent_ads": Advertisement.objects.order_by("-created_at")[:5],
        "recent_notices": Notice.objects.order_by("-created_at")[:5],
    }
    
    # ─────────────────────────────────────────────────────────────────────────
    # FORM STATUS BREAKDOWN
    # ─────────────────────────────────────────────────────────────────────────
    form_status = {
        "open": FormConfiguration.objects.filter(is_form_open=True, is_active=True).count(),
        "closed": FormConfiguration.objects.filter(is_form_open=False, is_active=True).count(),
        "total_fee": FormConfiguration.objects.filter(
            is_active=True
        ).aggregate(total=Sum("application_fee"))["total"] or 0,
    }
    
    context = {
        "title": "Admin Dashboard",
        "labels": json.dumps(labels),
        "course_counts": json.dumps(course_counts),
        "seat_counts": json.dumps(seat_counts),
        "department_data": department_data,
        "stats": stats,
        "recent_activity": recent_activity,
        "form_status": form_status,
        "today": today,
    }
    
    return render(request, "master_control/dashboard.html", context)


@staff_member_required
def department_report(request):
    """
    Detailed department-wise report with comprehensive analytics.
    """
    departments = (
        Course.objects.filter(is_active=True)
        .values("department_name")
        .annotate(
            course_count=Count("id"),
            total_seats=Sum("total_seats"),
            avg_seats=Sum("total_seats") / Count("id"),
            open_forms=Count(
                "form_configs",
                filter=Q(form_configs__is_form_open=True, form_configs__is_active=True)
            ),
            total_fee=Sum(
                "form_configs__application_fee",
                filter=Q(form_configs__is_active=True)
            )
        )
        .order_by("-course_count")
    )
    
    context = {
        "title": "Department Report",
        "departments": departments,
    }
    
    return render(request, "master_control/department_report.html", context)


@staff_member_required
def system_health(request):
    """
    System health check and configuration overview.
    """
    settings = PortalSettings.objects.first()
    today = timezone.now().date()
    
    health_checks = {
        "portal_configured": PortalSettings.objects.exists(),
        "portal_active": settings.is_portal_active if settings else False,
        "maintenance_mode": settings.maintenance_mode if settings else False,
        "application_period_active": False,
        "courses_configured": Course.objects.filter(is_active=True).exists(),
        "forms_configured": FormConfiguration.objects.filter(is_active=True).exists(),
        "ads_configured": Advertisement.objects.filter(
            is_active=True, start_date__lte=today, end_date__gte=today
        ).exists(),
        "notices_active": Notice.objects.filter(is_active=True).exists(),
    }
    
    # Check application period
    if settings and settings.application_start_date and settings.application_end_date:
        health_checks["application_period_active"] = (
            settings.application_start_date <= today <= settings.application_end_date
        )
    
    context = {
        "title": "System Health",
        "health_checks": health_checks,
        "settings": settings,
    }
    
    return render(request, "master_control/system_health.html", context)


# ────────────────────────────────────────────────────────────────────────────────
# CUSTOM FORM CLASSES
# ────────────────────────────────────────────────────────────────────────────────

class CourseForm(ModelForm):
    """Custom form for Course model."""
    class Meta:
        model = Course
        fields = [
            'course_name', 'department_name', 'degree_type', 
            'duration_years', 'total_seats',
            'display_priority', 'is_active'
        ]


class AdvertisementForm(ModelForm):
    """Custom form for Advertisement model."""
    class Meta:
        model = Advertisement
        fields = [
            'title', 'description', 'file', 'redirect_url',
            'display_type', 'priority', 'start_date', 'end_date', 'is_active'
        ]


class NoticeForm(ModelForm):
    """Custom form for Notice model."""
    class Meta:
        model = Notice
        fields = [
            'title', 'content', 'attachment', 'priority', 'is_active'
        ]


# ────────────────────────────────────────────────────────────────────────────────
# CUSTOM FORM VIEWS
# ────────────────────────────────────────────────────────────────────────────────

@staff_member_required
def add_course(request):
    """Custom view for adding a new course."""
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'Course "{course.course_name}" has been added successfully!')
            return redirect('master_control:dashboard')
    else:
        form = CourseForm()
    
    context = {
        'title': 'Add New Course',
        'form': form,
        'form_type': 'course'
    }
    return render(request, 'master_control/course_form.html', context)


@staff_member_required
def add_advertisement(request):
    """Custom view for adding a new advertisement."""
    if request.method == 'POST':
        form = AdvertisementForm(request.POST, request.FILES)
        if form.is_valid():
            ad = form.save()
            messages.success(request, f'Advertisement "{ad.title}" has been added successfully!')
            return redirect('master_control:dashboard')
    else:
        form = AdvertisementForm()
    
    context = {
        'title': 'Add New Advertisement',
        'form': form,
        'form_type': 'advertisement'
    }
    return render(request, 'master_control/advertisement_form.html', context)


@staff_member_required
def add_notice(request):
    """Custom view for adding a new notice."""
    if request.method == 'POST':
        form = NoticeForm(request.POST, request.FILES)
        if form.is_valid():
            notice = form.save()
            messages.success(request, f'Notice "{notice.title}" has been added successfully!')
            return redirect('master_control:dashboard')
    else:
        form = NoticeForm()
    
    context = {
        'title': 'Add New Notice',
        'form': form,
        'form_type': 'notice'
    }
    return render(request, 'master_control/notice_form.html', context)
