from django.db import models

# Create your models here.
class User(models.Model):
    full_name = models.CharField(max_length=200)  
    email = models.EmailField(unique=True)  
    phone_number = models.CharField(max_length=15) 
    social_links = models.URLField(blank=True, null=True) 
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True) 