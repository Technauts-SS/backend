from django.shortcuts import get_object_or_404
from rest_framework import generics, filters, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework import status
from .models import DonationCampaign, MockDonation
from .serializers import DonationCampaignSerializer, MockDonationSerializer
from rest_framework.decorators import action
from rest_framework.views import APIView  # Add this import at the top
from users.permissions import IsModeratorOrAdmin
from django.db.models import Q
from django.db import transaction

class CreateDonationCampaignView(generics.CreateAPIView):
    """Створення збору з підтримкою завантаження зображень."""
    queryset = DonationCampaign.objects.all()
    serializer_class = DonationCampaignSerializer
    parser_classes = [MultiPartParser, FormParser]
    renderer_classes = [JSONRenderer]
    permission_classes = [permissions.IsAuthenticated]  # Доступно тільки для авторизованих користувачів

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

class ListFundraisingsView(generics.ListAPIView):
    """Список зборів з можливістю пошуку та фільтрації."""
    serializer_class = DonationCampaignSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'category']
    ordering_fields = ['created_at', 'goal_amount', 'current_amount']
    ordering = ['-created_at']
    permission_classes = [permissions.AllowAny]  # Доступно для всіх

    def get_queryset(self):
        queryset = DonationCampaign.objects.all()
        
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
            
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset

class UserFundraisingsView(generics.ListAPIView):
    """Список зборів конкретного користувача."""
    serializer_class = DonationCampaignSerializer
    permission_classes = [permissions.IsAuthenticated]  # Тільки для авторизованих користувачів
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'goal_amount']
    ordering = ['-created_at']

    def get_queryset(self):
        return DonationCampaign.objects.filter(creator=self.request.user)

class RetrieveFundraisingView(generics.RetrieveAPIView):
    """Отримання деталей окремого збору."""
    queryset = DonationCampaign.objects.all()
    serializer_class = DonationCampaignSerializer
    lookup_field = "id"
    permission_classes = [permissions.AllowAny]  # Доступно для всіх

class UpdateFundraisingView(generics.UpdateAPIView):
    """Оновлення збору."""
    queryset = DonationCampaign.objects.all()
    serializer_class = DonationCampaignSerializer
    lookup_field = "id"
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated]  # Тільки для авторизованих користувачів

    def get_queryset(self):
        return DonationCampaign.objects.filter(creator=self.request.user)

class DeleteFundraisingView(generics.DestroyAPIView):
    """Видалення збору."""
    serializer_class = DonationCampaignSerializer
    lookup_field = "id"
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DonationCampaign.objects.filter(creator=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # First delete all related donations
        MockDonation.objects.filter(campaign=instance).delete()
        
        # Then delete the campaign
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            instance = self.get_object()
            MockDonation.objects.filter(campaign=instance).delete()
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
    
class CreateDonationView(generics.CreateAPIView):
    """Створення донату. Доступно для всіх."""
    queryset = MockDonation.objects.all()
    serializer_class = MockDonationSerializer
    permission_classes = [permissions.AllowAny]  # Доступно для всіх, без авторизації
    
    def perform_create(self, serializer):
        campaign = serializer.validated_data['campaign']
        user = self.request.user if self.request.user.is_authenticated else None  # Якщо користувач не авторизований, не прив'язувати його до донату
        serializer.save(user=user)


class CampaignDonationsListView(generics.ListAPIView):
    serializer_class = MockDonationSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        campaign_id = self.kwargs['campaign_id']
        return MockDonation.objects.filter(campaign_id=campaign_id).order_by('-created_at')
class ModerationCampaignView(APIView):
    permission_classes = [IsModeratorOrAdmin]

    def patch(self, request, pk):
        campaign = get_object_or_404(DonationCampaign, pk=pk)
        action = request.data.get('action')
        resolution_note = request.data.get('resolution_note', '')

        if action == 'approve':
            if campaign.status in ['pending', 'paused']:
                campaign.status = 'active'
                campaign.needs_moderation = False
                campaign.save()
                return Response({'status': 'approved' if campaign.status == 'pending' else 're-activated'})

        elif action == 'reject':
            if campaign.status in ['pending', 'paused']:
                campaign.status = 'cancelled'
                campaign.needs_moderation = False
                campaign.save()
                return Response({'status': 'rejected' if campaign.status == 'pending' else 'cancelled'})

        elif action == 'pause':
            if campaign.status == 'active':
                campaign.status = 'paused'
                campaign.save()
                return Response({'status': 'paused'})

        elif action == 'warn':
            campaign.warnings_count += 1
            campaign.needs_moderation = True
            if campaign.warnings_count >= 3:
                campaign.status = 'paused'
            campaign.save()
            return Response({
                'status': 'warning issued',
                'warnings_count': campaign.warnings_count,
                'campaign_status': campaign.status
            })

        return Response(
            {'error': 'Invalid action for current status'},
            status=status.HTTP_400_BAD_REQUEST
        )

class ModerationCampaignsListView(generics.ListAPIView):
    """Returns all fundraisers that need moderation."""
    queryset = DonationCampaign.objects.filter(
        Q(status='pending') | Q(needs_moderation=True)
    )  # Закрито дужки
    serializer_class = DonationCampaignSerializer
    permission_classes = [permissions.IsAuthenticated, IsModeratorOrAdmin]  # Додано закриваючу дужку
    
    @action(detail=False, methods=['get'])
    def count(self, request):
        """Return count of campaigns needing moderation"""
        count = self.get_queryset().count()
        return Response({'count': count})
    
class ModerationCampaignsCountView(APIView):
    """
    Returns the count of campaigns needing moderation
    """
    def get(self, request):
        count = DonationCampaign.objects.filter(needs_moderation=True).count()
        return Response({"count": count})

class RetrieveFundraisingView(generics.RetrieveAPIView):
    queryset = DonationCampaign.objects.all()
    serializer_class = DonationCampaignSerializer
    lookup_field = "id"
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        instance = super().get_object()
        instance.handle_reports()  # Перевіряємо скарги при кожному запиті
        return instance