from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    full_name = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=20, unique=True)
    social_links = models.URLField(blank=True, null=True)
    image = models.ImageField(
        upload_to='profile_images/',
        blank=True,
        null=True,
        max_length=255
    )
    bio = models.TextField(blank=True, null=True)  # Додане поле біо
    
    email = models.EmailField(unique=True)
    username = None
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'phone_number']
    
    objects = UserManager()
    
    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        # Виправлено з profile_image на image
        if self.pk and self.image:
            try:
                old_user = User.objects.get(pk=self.pk)
                if old_user.image and old_user.image != self.image:
                    old_user.image.delete(save=False)
            except User.DoesNotExist:
                pass
        super().save(*args, **kwargs)