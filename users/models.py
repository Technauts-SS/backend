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
        extra_fields.setdefault('role', User.Role.ADMIN)
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    class Role(models.TextChoices):
        USER = 'user', 'Regular User'
        MODERATOR = 'moderator', 'Moderator'
        ADMIN = 'admin', 'Admin'

    full_name = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=20, unique=True)
    social_links = models.URLField(blank=True, null=True)
    image = models.ImageField(
        upload_to='profile_images/',
        blank=True,
        null=True,
        max_length=255
    )
    bio = models.TextField(blank=True, null=True)
    email = models.EmailField(unique=True)
    username = None
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER
    )
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'phone_number']
    
    objects = UserManager()
    
    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        # Обробка зображення
        if self.pk and self.image:
            try:
                old_user = User.objects.get(pk=self.pk)
                if old_user.image and old_user.image != self.image:
                    old_user.image.delete(save=False)
            except User.DoesNotExist:
                pass
        
        # Викликаємо оригінальний save
        super().save(*args, **kwargs)
        
        # Оновлюємо кешовані властивості
        if hasattr(self, '_is_admin'):
            del self._is_admin
        if hasattr(self, '_is_moderator'):
            del self._is_moderator
        
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser
    
    @property
    def is_moderator(self):
        return self.role == self.Role.MODERATOR or self.is_admin