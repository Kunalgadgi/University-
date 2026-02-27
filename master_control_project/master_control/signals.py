"""
Master Control Signals - Django Signals for model events
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import logging

from .models import (
    PortalSettings, Course, FormConfiguration,
    Advertisement, Notice, HomepageSlider
)

logger = logging.getLogger('master_control')


@receiver(post_save, sender=PortalSettings)
def log_portal_settings_change(sender, instance, created, **kwargs):
    """Log portal settings changes."""
    action = "created" if created else "updated"
    logger.info(f"PortalSettings {action}: {instance.portal_name}")


@receiver(post_save, sender=Course)
def log_course_change(sender, instance, created, **kwargs):
    """Log course changes."""
    action = "created" if created else "updated"
    logger.info(f"Course {action}: {instance.course_name}")


@receiver(post_save, sender=FormConfiguration)
def log_form_config_change(sender, instance, created, **kwargs):
    """Log form configuration changes."""
    action = "created" if created else "updated"
    status = "OPEN" if instance.is_form_open else "CLOSED"
    logger.info(f"FormConfig {action}: {instance.course.course_name} - Status: {status}")


@receiver(post_save, sender=Advertisement)
def log_advertisement_change(sender, instance, created, **kwargs):
    """Log advertisement changes."""
    action = "created" if created else "updated"
    logger.info(f"Advertisement {action}: {instance.title} (Type: {instance.display_type})")


@receiver(post_save, sender=Notice)
def log_notice_change(sender, instance, created, **kwargs):
    """Log notice changes."""
    action = "created" if created else "updated"
    logger.info(f"Notice {action}: {instance.title}")


@receiver(post_save, sender=HomepageSlider)
def log_slider_change(sender, instance, created, **kwargs):
    """Log slider changes."""
    action = "created" if created else "updated"
    logger.info(f"HomepageSlider {action}: {instance.title}")
