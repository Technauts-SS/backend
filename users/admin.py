from django.contrib import admin
from django.db import transaction
from .models import User

class CustomUserAdmin(admin.ModelAdmin):
    model = User
    ordering = ['email']
    list_display = ['email', 'full_name', 'phone_number']
    search_fields = ['email', 'full_name', 'phone_number']
    actions = ['delete_selected_users']  # Наша кастомна дія
    
    def delete_selected_users(self, request, queryset):
        # Отримуємо всі моделі, які посилаються на User
        related_models = []
        for field in User._meta.get_fields():
            if field.one_to_many or field.one_to_one:
                related_models.append(field.related_model)
        
        # Видаляємо пов'язані об'єкти
        with transaction.atomic():
            for user in queryset:
                for related_model in related_models:
                    if related_model:  # Ігноруємо None (якщо є)
                        # Знаходимо всі пов'язані об'єкти
                        related_name = None
                        for f in user._meta.get_fields():
                            if f.related_model == related_model:
                                related_name = f.get_accessor_name()
                                break
                        
                        if related_name:
                            related_objects = getattr(user, related_name).all()
                            related_objects.delete()
                
                # Видаляємо самого користувача
                user.delete()
        
        self.message_user(request, f"Успішно видалено {queryset.count()} користувачів та всі пов'язані об'єкти.")
    
    delete_selected_users.short_description = "Видалити обрані користувачі (разом із залежностями)"

admin.site.register(User, CustomUserAdmin)