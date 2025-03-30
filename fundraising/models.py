from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
from django.conf import settings

class DonationCampaign(models.Model):
    permission_classes = [AllowAny]

    CATEGORY_CHOICES = [
        ("health", "Здоров'я"),
        ("social", "Соціальна допомога"),
        ("education", "Освіта та наука"),
        ("ecology", "Екологія та тварини"),
        ("other", "Інше"),
    ]
    
    STATUS_CHOICES = [
        ("draft", "Чернетка"),
        ("active", "Активна"),
        ("paused", "Призупинена"),
        ("completed", "Завершена"),
        ("cancelled", "Скасована"),
    ]
    
    # Основна інформація
    title = models.CharField(max_length=200, verbose_name="Назва кампанії")
    creator_name = models.CharField(max_length=100, verbose_name="Ім'я організатора")
    contact_info = models.CharField(max_length=200, verbose_name="Контактна інформація")
    description = models.TextField(verbose_name="Опис")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="other", verbose_name="Категорія")
    location = models.CharField(max_length=100, blank=True, null=True, verbose_name="Місцезнаходження")
    
    # Медіа та файли
    image = models.ImageField(upload_to='campaign_images/', blank=True, null=True, verbose_name="Зображення")
    
    # Фінансова інформація
    goal_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цільова сума")
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Зібрана сума")
    donation_link = models.URLField(blank=True, null=True, verbose_name="Посилання для пожертв")
    help_type = models.CharField(max_length=50, choices=[("money", "Фінансова допомога"), 
                                                         ("volunteer", "Волонтерська допомога"),
                                                         ("both", "Обидва типи")], default="money", verbose_name="Тип допомоги")
    
    # Підтвердження
    evidence = models.TextField(blank=True, null=True, verbose_name="Опис підтвердження")
    evidence_file = models.FileField(upload_to='evidence/', blank=True, null=True, verbose_name="Файл підтвердження")
    evidence_link = models.URLField(blank=True, null=True, verbose_name="Посилання на підтвердження")
    

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft", verbose_name="Статус")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Дата створення")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата оновлення")
    ends_at = models.DateTimeField(blank=True, null=True, verbose_name="Дата завершення")
    
    class Meta:
        verbose_name = "Кампанія збору коштів"
        verbose_name_plural = "Кампанії збору коштів"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def progress_percentage(self):
        if self.goal_amount == 0:
            return 0
        return int((self.current_amount / self.goal_amount) * 100)
    
    def is_completed(self):
        return self.current_amount >= self.goal_amount
    
    def is_ended(self):
        """Перевірка, чи кампанія завершена по даті."""
        if self.ends_at and self.ends_at <= timezone.now():
            return True
        return False

    def update_status(self):
        """Оновлення статусу кампанії на основі її цілей та дати завершення."""
        if self.is_completed():
            self.status = 'completed'
        elif self.is_ended():
            self.status = 'completed'
        elif self.status != 'paused':
            self.status = 'active'
        self.save()
