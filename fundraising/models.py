from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
from django.conf import settings
import os
from django.db.models import Sum
import logging
from django.db import transaction

logger = logging.getLogger(__name__)

User = get_user_model()

class DonationCampaign(models.Model):
    CATEGORY_CHOICES = [
        ("health", "Здоров'я"),
        ("social", "Соціальна допомога"),
        ("education", "Освіта та наука"),
        ("ecology", "Екологія та тварини"),
        ("other", "Інше"),
    ]
    
    STATUS_CHOICES = [
        ("pending", "На розгляді"),
        ("active", "Активний"),
        ("paused", "Призупинений"),
        ("completed", "Завершений"),
        ("cancelled", "Скасований")
    ]
        
    title = models.CharField(max_length=200, verbose_name="Назва кампанії")
    description = models.TextField(verbose_name="Опис")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="other")
    location = models.CharField(max_length=100, blank=True, null=True)
    
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_campaigns',
        null=True
    )
    contact_info = models.CharField(max_length=200)
    
    image = models.ImageField(upload_to='campaign_images/', blank=True, null=True)
    goal_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    donation_link = models.URLField(blank=True, null=True)
    
    help_type = models.CharField(
        max_length=50,
        choices=[("money", "Фінансова допомога"), ("volunteer", "Волонтерська допомога"), ("both", "Обидва типи")],
        default="money"
    )
    
    evidence = models.TextField(blank=True, null=True)
    evidence_file = models.FileField(upload_to='evidence/', blank=True, null=True)
    evidence_link = models.URLField(blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    ends_at = models.DateTimeField(blank=True, null=True)
    needs_moderation = models.BooleanField(default=False)
    warnings_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
    
    def delete(self, *args, **kwargs):
        if self.image and os.path.isfile(self.image.path):
            os.remove(self.image.path)
        if self.evidence_file and os.path.isfile(self.evidence_file.path):
            os.remove(self.evidence_file.path)
        super().delete(*args, **kwargs)
    
    @property
    def creator_name(self):
        return getattr(self.creator, 'full_name', None) or getattr(self.creator, 'username', 'Невідомий')
    
    def progress_percentage(self):
        if self.goal_amount == 0:
            return 0
        return (self.current_amount / self.goal_amount) * 100
    
    def save(self, *args, **kwargs):
        # Визначаємо, чи це новий запис
        is_new = self._state.adding
        
        # Якщо це новий запис і цільова сума менше 10 000 грн
        if is_new and self.goal_amount < 10000:
            self.status = 'active'
        
        super().save(*args, **kwargs)
        
        # Оригінальна логіка для оновлення суми
        if is_new and self.status == 'success':
            self.campaign.current_amount = Donation.objects.filter(
                campaign=self.campaign, 
                status='success'
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            self.campaign.save()
            
    def handle_reports(self):
        try:
            reports_count = self.reports.filter(status='approved').count()
            if reports_count >= 3 and self.status == 'active':
                self.status = 'paused'
                self.save()
                return True
            return False
        except Exception as e:
            logger.error(f"Error handling reports: {str(e)}")
            return False

    def is_completed(self):
        return self.current_amount >= self.goal_amount
    
    def is_ended(self):
        return self.ends_at and self.ends_at <= timezone.now()
    
    def update_stats(self):
        try:
            with transaction.atomic():
                # Calculate total from all successful donations
                total = self.donations.filter(status='success').aggregate(
                    Sum('amount')
                )['amount__sum'] or 0
                
                # Update current amount
                self.current_amount = total
                self.save()
                
                # Check if campaign should be completed
                if self.current_amount >= self.goal_amount:
                    self.status = 'completed'
                    self.save()
        except Exception as e:
            logger.error(f"Error updating stats for campaign {self.id}: {str(e)}")
            raise
        
class Donation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'В очікуванні'),
        ('success', 'Успішно'),
        ('failed', 'Не вдалося'),
    ]
    
    campaign = models.ForeignKey(DonationCampaign, on_delete=models.CASCADE, related_name='donations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50, default='credit_card')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)

    def process_payment(self):
        """Обробка платежу з базовою валідацією"""
        try:
            # Базова перевірка - сума має бути додатньою
            if self.amount <= 0:
                self.status = 'failed'
                self.save()
                return False
            
            # Для тестування - приймаємо будь-який платіж
            self.status = 'success'
            self.save()
            
            # Оновлюємо кампанію
            self.campaign.current_amount = Donation.objects.filter(
                campaign=self.campaign, 
                status='success'
            ).aggregate(total=Sum('amount'))['total'] or 0
            self.campaign.save()
            
            return True
            
        except Exception as e:
            self.status = 'failed'
            self.save()
            return False
