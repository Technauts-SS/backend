from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import DonationCampaign, Report

@receiver(post_save, sender=Report)
def handle_report_save(sender, instance, created, **kwargs):
    """
    Обробляє збереження скарги:
    - При створенні нової скарги
    - При зміні статусу на 'approved'
    """
    if instance.fundraiser and (created or instance.status == 'approved'):
        instance.fundraiser.handle_reports()

@receiver(post_save, sender=Report)
def handle_report_status_change(sender, instance, created, **kwargs):
    """Обробляє зміни статусу скарг"""
    if instance.status == 'approved' and instance.fundraiser:
        instance.fundraiser.handle_reports()

@receiver(pre_save, sender=DonationCampaign)
def handle_campaign_status_change(sender, instance, **kwargs):
    """Обробляє зміни статусу зборів"""
    if instance.pk:  # Якщо це не новий запис
        original = DonationCampaign.objects.get(pk=instance.pk)
        
        # Якщо статус змінився на 'active' з 'pending'
        if instance.status == 'active' and original.status == 'pending':
            instance.needs_moderation = False
@receiver(post_save, sender=Report)
def update_campaign_on_report_approval(sender, instance, created, **kwargs):
    """
    Automatically update campaign status when reports are approved
    """
    if instance.status == 'approved':
        instance.update_campaign_status()