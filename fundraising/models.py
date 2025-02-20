from django.db import models

# Create your models here.
class DonationCampaign(models.Model):
    title = models.CharField(max_length=200)  
    creator_name = models.CharField(max_length=100)  
    contact_info = models.CharField(max_length=200)  
    description = models.TextField() 
    goal_amount = models.DecimalField(max_digits=10, decimal_places=2)  
    donation_link = models.URLField(blank=True, null=True)  

    # Докази: або текстовий опис, або файл, або посилання
    evidence = models.TextField(blank=True, null=True) 
    evidence_file = models.FileField(upload_to='evidence/', blank=True, null=True)
    evidence_link = models.URLField(blank=True, null=True)