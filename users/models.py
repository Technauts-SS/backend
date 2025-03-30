from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    full_name = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=20, unique=True)
    social_links = models.URLField(blank=True, null=True)
    
    # Poverride email to be used for authentication
    email = models.EmailField(unique=True)

    # Remove username field
    username = None  # Remove the username field

    USERNAME_FIELD = 'email'  # Set email as the username field
    REQUIRED_FIELDS = ['full_name', 'phone_number']  # Exclude email from required fields

    def __str__(self):
        return self.email
