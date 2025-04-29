from django.shortcuts import get_object_or_404
from rest_framework import generics, filters, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from .models import DonationCampaign, Donation
from .serializers import DonationCampaignSerializer, DonationSerializer
from rest_framework.decorators import action
from rest_framework.views import APIView
from users.permissions import IsModeratorOrAdmin
from django.db.models import Q
from django.db import transaction
import logging
from django.http import Http404

logger = logging.getLogger(__name__)

class CreateDonationCampaignView(generics.CreateAPIView):
    queryset = DonationCampaign.objects.all()
    serializer_class = DonationCampaignSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

# views.py
class ListFundraisingsView(generics.ListAPIView):
    serializer_class = DonationCampaignSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'category']
    ordering_fields = ['created_at', 'goal_amount', 'current_amount']
    ordering = ['-created_at']
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = DonationCampaign.objects.all() 
        category = self.request.query_params.get('category')
        status = self.request.query_params.get('status')
        
        if category:
            queryset = queryset.filter(category=category)
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset

class UserFundraisingsView(generics.ListAPIView):
    serializer_class = DonationCampaignSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'goal_amount']
    ordering = ['-created_at']

    def get_queryset(self):
        return DonationCampaign.objects.filter(creator=self.request.user)

class RetrieveFundraisingView(generics.RetrieveAPIView):
    queryset = DonationCampaign.objects.all()
    serializer_class = DonationCampaignSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        try:
            instance = super().get_object()
            try:
                if instance.handle_reports():
                    logger.info(f"Campaign {instance.id} paused due to reports")
            except Exception as e:
                logger.error(f"Error in handle_reports: {str(e)}")
                # Продовжуємо виконання, не зупиняємося через помилку
            
            try:
                if instance.is_completed() or instance.is_ended():
                    instance.status = 'completed'
                    instance.save()
            except Exception as e:
                logger.error(f"Error checking completion status: {str(e)}")
                # Продовжуємо виконання, не зупиняємося через помилку
                
            return instance
        except DonationCampaign.DoesNotExist:
            logger.error(f"Campaign {self.kwargs.get('pk')} not found")
            raise Http404("Кампанія не знайдена")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            # Замість передачі помилки далі, повертаємо структуровану відповідь
            from rest_framework.exceptions import APIException
            raise APIException(detail="Помилка при отриманні деталей кампанії")

class UpdateFundraisingView(generics.UpdateAPIView):
    queryset = DonationCampaign.objects.all()
    serializer_class = DonationCampaignSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DonationCampaign.objects.filter(creator=self.request.user)

class DeleteFundraisingView(generics.DestroyAPIView):
    serializer_class = DonationCampaignSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DonationCampaign.objects.filter(creator=self.request.user)

    def destroy(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                instance = self.get_object()

                # Логування перед видаленням
                logger.info(f"Deleting campaign {instance.id} by user {request.user}")

                # Видаляємо всі донати, пов’язані з кампанією
                Donation.objects.filter(campaign=instance).delete()

                # Видаляємо саму кампанію (разом із файлами)
                self.perform_destroy(instance)

            return Response(status=status.HTTP_204_NO_CONTENT)

        except DonationCampaign.DoesNotExist:
            logger.warning(f"Attempt to delete non-existing campaign by user {request.user}")
            return Response({"detail": "Кампанія не знайдена."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Unexpected error while deleting campaign: {str(e)}")
            return Response({"detail": "Сталася помилка при видаленні кампанії."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateDonationView(generics.CreateAPIView):
    queryset = Donation.objects.all()
    serializer_class = DonationSerializer
    permission_classes = [permissions.AllowAny]
    
    def perform_create(self, serializer):
        with transaction.atomic():
            campaign = serializer.validated_data['campaign']
            user = self.request.user if self.request.user.is_authenticated else None
            donation = serializer.save(user=user)
            
            # Process payment
            donation.process_payment()
            
            # Update campaign stats
            campaign.update_stats()

class CampaignDonationsListView(generics.ListAPIView):
    serializer_class = DonationSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['amount', 'created_at']  # або інші поля, які є у Donation
    ordering = ['-created_at']

    def get_queryset(self):
        campaign = get_object_or_404(DonationCampaign, pk=self.kwargs['campaign_id'])
        if campaign.status in ['paused', 'cancelled']:
            return Donation.objects.none()
        return Donation.objects.filter(campaign=campaign).order_by('-created_at')

class ModerationCampaignsListView(generics.ListAPIView):
    queryset = DonationCampaign.objects.filter(
        Q(status='pending') | Q(needs_moderation=True))
    serializer_class = DonationCampaignSerializer
    permission_classes = [permissions.IsAuthenticated, IsModeratorOrAdmin]
    
    @action(detail=False, methods=['get'])
    def count(self, request):
        count = self.get_queryset().count()
        return Response({'count': count})

class ModerationCampaignsCountView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsModeratorOrAdmin]

    def get(self, request):
        count = DonationCampaign.objects.filter(needs_moderation=True).count()
        return Response({"count": count})

class UpdateCampaignStatusView(generics.UpdateAPIView):
    queryset = DonationCampaign.objects.all()
    serializer_class = DonationCampaignSerializer
    permission_classes = [IsModeratorOrAdmin]

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in ['active', 'paused', 'cancelled']:
            return Response(
                {"error": "Invalid status"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        instance.status = new_status
        instance.save()
        
        # Якщо статус змінює модератор, позначаємо що модерація пройдена
        if new_status in ['active', 'cancelled']:
            instance.needs_moderation = False
            instance.save()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)