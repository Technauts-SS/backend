from django.contrib import admin
from .models import DonationCampaign

@admin.register(DonationCampaign)
class DonationCampaignAdmin(admin.ModelAdmin):
    list_display = ("title", "creator_name", "category", "goal_amount", "status", "created_at")
    search_fields = ("title", "creator_name", "category", "status")
    list_filter = ("category", "status")
    list_per_page = 20  # Display 20 campaigns per page (adjust as needed)

    def goal_amount(self, obj):
        return f"${obj.goal_amount:,.2f}"  # Formats the goal amount as currency
    goal_amount.short_description = "Goal Amount"  # Set a more readable column name
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            actions['delete_selected'] = (
                self.delete_selected_action,
                'delete_selected',
                "Видалити обрані кампанії"
            )
        return actions
    
    def delete_selected_action(self, modeladmin, request, queryset):
        for obj in queryset:
            obj.delete()
        self.message_user(request, f"Видалено {queryset.count()} кампаній")
    
    def delete_model(self, request, obj):
        try:
            obj.delete()
            self.message_user(request, "Кампанію успішно видалено")
        except Exception as e:
            self.message_user(request, f"Помилка: {str(e)}", level='ERROR')