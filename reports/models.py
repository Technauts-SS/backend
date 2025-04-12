from django.db import models
from django.utils import timezone
from fundraising.models import DonationCampaign
from users.models import User

class Report(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На розгляді'),
        ('approved', 'Схвалено'),
        ('rejected', 'Відхилено')
    ]

    fundraiser = models.ForeignKey(
        DonationCampaign,
        on_delete=models.CASCADE,  # Changed from SET_NULL to CASCADE
        related_name='reports'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    reason = models.TextField()
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    resolution_note = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Звіт'
        verbose_name_plural = 'Звіти'

    def __str__(self):
        return f"Звіт #{self.id} ({self.status})"
    def save(self, *args, **kwargs):
        # Update processed_at when status changes from pending
        if self.pk and self.status != 'pending':
            original = Report.objects.get(pk=self.pk)
            if original.status == 'pending':
                self.processed_at = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Update campaign status if report is approved
        if self.status == 'approved':
            self.update_campaign_status()

    def update_campaign_status(self):
        """Update campaign status based on approved reports"""
        # Get fresh count of approved reports
        approved_count = Report.objects.filter(
            fundraiser=self.fundraiser,
            status='approved'
        ).count()
        
        # Check if we need to pause the campaign
        if approved_count >= 3:
            campaign = DonationCampaign.objects.get(id=self.fundraiser.id)
            if campaign.status == 'active':
                campaign.status = 'paused'
                campaign.save()
                return True
        return False
    @classmethod
    def check_campaign_reports(cls, campaign_id):
        from django.conf import settings
        from fundraising.models import DonationCampaign
        
        approved_count = cls.objects.filter(
            fundraiser_id=campaign_id, 
            status='approved'
        ).count()
        
        if approved_count >= getattr(settings, 'AUTO_PAUSE_REPORTS_LIMIT', 3):
            campaign = DonationCampaign.objects.get(id=campaign_id)
            if campaign.status == 'active':
                campaign.status = 'paused'
                campaign.save()
                return True
        return False
    
    def delete(self, *args, **kwargs):
        """Safe deletion that nullifies foreign keys first"""
        from django.db import transaction
        
        with transaction.atomic():
            # Update foreign keys to NULL without triggering full save
            Report.objects.filter(pk=self.pk).update(
                fundraiser=None,
                user=None
            )
            # Now proceed with the actual deletion
            super().delete(*args, **kwargs)