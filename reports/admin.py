from django.contrib import admin
from django.contrib import messages
from django.db import transaction
from .models import Report

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'fundraiser', 'user', 'status', 'created_at', 'processed_at')
    list_filter = ('status', 'created_at', 'processed_at')
    search_fields = ('user__username', 'fundraiser__title', 'reason')
    readonly_fields = ('created_at', 'processed_at', 'fundraiser', 'user', 'reason', 'status', 'resolution_note')
    ordering = ('-created_at',)
    
    actions = ['custom_delete_selected']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return True
    
    def custom_delete_selected(self, request, queryset):
        """
        Кастомна дія для безпечного видалення обраних звітів
        """
        deleted_count = 0
        errors = []
        
        for obj in queryset:
            try:
                with transaction.atomic():
                    # Спочатку обнуляємо зовнішні ключі
                    Report.objects.filter(pk=obj.pk).update(
                        fundraiser=None,
                        user=None
                    )
                    # Тепер можемо безпечно видалити
                    obj.delete()
                deleted_count += 1
            except Exception as e:
                errors.append(f"Звіт #{obj.id}: {str(e)}")
        
        if deleted_count:
            self.message_user(
                request,
                f"Успішно видалено {deleted_count} звітів",
                level=messages.SUCCESS
            )
        
        if errors:
            self.message_user(
                request,
                "Помилки при видаленні: " + "; ".join(errors),
                level=messages.ERROR
            )
    
    custom_delete_selected.short_description = "Видалити обрані звіти"
    
    def delete_model(self, request, obj):
        """
        Обробка видалення одного об'єкта
        """
        try:
            with transaction.atomic():
                # Спочатку обнуляємо зовнішні ключі
                Report.objects.filter(pk=obj.pk).update(
                    fundraiser=None,
                    user=None
                )
                # Тепер можемо безпечно видалити
                super(Report, obj).delete()
            
            self.message_user(
                request,
                "Звіт успішно видалено",
                level=messages.SUCCESS
            )
        except Exception as e:
            self.message_user(
                request,
                f"Помилка видалення: {str(e)}",
                level=messages.ERROR
            )
            raise