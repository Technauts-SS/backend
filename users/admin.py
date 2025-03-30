from django.contrib import admin
from .models import User

class CustomUserAdmin(admin.ModelAdmin):
    model = User
    ordering = ['email']  # Change this to 'email' instead of 'username'
    list_display = ['email', 'full_name', 'phone_number']
    search_fields = ['email', 'full_name', 'phone_number']
    
admin.site.register(User, CustomUserAdmin)
