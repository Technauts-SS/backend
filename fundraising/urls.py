from django.urls import path
from .views import (
    CreateDonationCampaignView,
    ListFundraisingsView,
    RetrieveFundraisingView,
    UpdateFundraisingView,
    DeleteFundraisingView
)

urlpatterns = [
    path("fundraisers/", ListFundraisingsView.as_view(), name="list_fundraisings"),  # `GET` отримує список зборів
    path("fundraisers/create/", CreateDonationCampaignView.as_view(), name="create_donation_campaign"),# `POST` створює збір
    path("fundraisers/<int:id>/", RetrieveFundraisingView.as_view(), name="get_fundraising"),
    path("fundraisers/<int:id>/update/", UpdateFundraisingView.as_view(), name="update_fundraising"),
    path("fundraisers/<int:id>/delete/", DeleteFundraisingView.as_view(), name="delete_fundraising"),
]
