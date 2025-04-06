from django.urls import path
from .views import (
    CreateDonationCampaignView,
    CreateDonationView,
    ListFundraisingsView,
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
    path('fundraisers/<int:id>/', RetrieveFundraisingView.as_view(), name='fundraiser-detail'),
    path('fundraisers/<int:id>/update/', UpdateFundraisingView.as_view(), name='fundraiser-update'),
    path('fundraisers/<int:id>/delete/', DeleteFundraisingView.as_view(), name='fundraiser-delete'),
    path('fundraisers/<int:campaign_id>/donations/', CampaignDonationsListView.as_view(), name='campaign-donations'),  # Новий маршрут
    path('donate/', CreateDonationView.as_view(), name='create-donation')
]