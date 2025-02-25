from django.db import models

class DonationCampaign(models.Model):
    CATEGORY_CHOICES = [
        ("health", "Здоров'я"),
        ("social", "Соціальна допомога"),
        ("education", "Освіта та наука"),
        ("ecology", "Екологія та тварини"),
        ("other", "Інше"),
    ]
    
    title = models.CharField(max_length=200)
    creator_name = models.CharField(max_length=100)
    contact_info = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="other")
    image = models.ImageField(upload_to='campaign_images/', blank=True, null=True)
    goal_amount = models.DecimalField(max_digits=10, decimal_places=2)
    donation_link = models.URLField(blank=True, null=True)
    evidence = models.TextField(blank=True, null=True)
    evidence_file = models.FileField(upload_to='evidence/', blank=True, null=True)
    evidence_link = models.URLField(blank=True, null=True)

