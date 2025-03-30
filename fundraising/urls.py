from django.urls import path
from .views import (
    CreateDonationCampaignView,
    ListFundraisingsView,
    UserFundraisingsView,
    RetrieveFundraisingView,
    UpdateFundraisingView,
    DeleteFundraisingView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('fundraisers/', ListFundraisingsView.as_view(), name='fundraisers-list'),
    path('fundraisers/create/', CreateDonationCampaignView.as_view(), name='fundraiser-create'),
    path('fundraisers/my/', UserFundraisingsView.as_view(), name='user-fundraisers'),
    path('fundraisers/<int:id>/', RetrieveFundraisingView.as_view(), name='fundraiser-detail'),
    path('fundraisers/<int:id>/update/', UpdateFundraisingView.as_view(), name='fundraiser-update'),
    path('fundraisers/<int:id>/delete/', DeleteFundraisingView.as_view(), name='fundraiser-delete'),
    
    # JWT Authentication
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]