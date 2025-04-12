from django.urls import path
from .views import (
    CreateDonationCampaignView,
    CreateDonationView,
    ListFundraisingsView,
    ModerationCampaignsCountView,
    ModerationCampaignsListView,
    UpdateCampaignStatusView,
    UserFundraisingsView,
    RetrieveFundraisingView,
    UpdateFundraisingView,
    DeleteFundraisingView,
    CampaignDonationsListView  # Новий імпорт
)

urlpatterns = [
    path('fundraisers/', ListFundraisingsView.as_view(), name='fundraisers-list'),
    path('fundraisers/create/', CreateDonationCampaignView.as_view(), name='fundraiser-create'),
    path('fundraisers/my/', UserFundraisingsView.as_view(), name='user-fundraisers'),
    path('fundraisers/<int:pk>/', RetrieveFundraisingView.as_view(), name='fundraiser-detail'),
    path('fundraisers/<int:id>/update/', UpdateFundraisingView.as_view(), name='fundraiser-update'),
    path('fundraisers/<int:pk>/delete/', DeleteFundraisingView.as_view(), name='fundraiser-delete'),
    path('fundraisers/<int:campaign_id>/donations/', CampaignDonationsListView.as_view(), name='campaign-donations'),  # Новий маршрут
    path('donations/', CreateDonationView.as_view(), name='create-donation'),
    path("fundraisers/moderation/campaigns/", ModerationCampaignsListView.as_view(), name="moderation-campaigns"),
    path("fundraisers/moderation/campaigns/count/", ModerationCampaignsCountView.as_view(), name="moderation-campaigns-count"),
    path('fundraisers/<int:pk>/update_status/', UpdateCampaignStatusView.as_view(), name='update-campaign-status')
]