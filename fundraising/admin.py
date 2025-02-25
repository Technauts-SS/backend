from django.contrib import admin
from .models import DonationCampaign

@admin.register(DonationCampaign)
class DonationCampaignAdmin(admin.ModelAdmin):
    list_display = ("title", "creator_name", "category", "goal_amount")
    search_fields = ("title", "creator_name", "category")
    list_filter = ("category",)
