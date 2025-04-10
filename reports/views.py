from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from fundraising.models import DonationCampaign
from .models import Report
from .serializers import ReportSerializer
from django.utils import timezone
from datetime import timedelta
from rest_framework.decorators import action
from django.db.models import Count
from users.permissions import IsModeratorOrAdmin
from django.db.models import Q
import logging
logger = logging.getLogger(__name__) 

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all().select_related('fundraiser', 'user')
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Якщо користувач є модератором або адміністратором – не фільтруємо по user
        if not (self.request.user.is_staff or self.request.user.role in ['moderator', 'admin']):
            queryset = queryset.filter(user=self.request.user)
        return queryset

    
    def create(self, request, *args, **kwargs):
        logger.info(f"Incoming report data: {request.data}")
        logger.info(f"From user: {request.user.id}")

        try:
            # Перевірка обов'язкових полів
            if 'fundraiser' not in request.data:
                return Response(
                    {"fundraiser": ["Це поле обов'язкове"]},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if 'reason' not in request.data or not request.data['reason'].strip():
                return Response(
                    {"reason": ["Будь ласка, вкажіть причину скарги"]},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Перевірка типу fundraiser
            try:
                fundraiser_id = int(request.data['fundraiser'])
            except (ValueError, TypeError):
                return Response(
                    {"fundraiser": ["ID кампанії має бути числом"]},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Перевірка існування кампанії
            if not DonationCampaign.objects.filter(id=fundraiser_id).exists():
                return Response(
                    {"fundraiser": [f"Кампанія з ID {fundraiser_id} не існує"]},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Перевірка на дублікати
            last_24h = timezone.now() - timedelta(hours=24)
            existing_report = Report.objects.filter(
                fundraiser_id=fundraiser_id,
                user=request.user,
                created_at__gte=last_24h
            ).first()

            if existing_report:
                created_at_local = timezone.localtime(existing_report.created_at)
                return Response(
                    {
                        "detail": "Ви вже створювали скаргу на цей збір за останні 24 години",
                        "existing_report_id": existing_report.id,
                        "created_at": created_at_local.isoformat(),
                        "next_available_time": (created_at_local + timedelta(hours=24)).isoformat()
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Створення звіту
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            logger.info(f"Report created: {serializer.data}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating report: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Внутрішня помилка сервера при створенні звіту"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
              
    @action(detail=False, methods=['get'])
    def stats(self, request):
        stats = Report.objects.values('status').annotate(count=Count('status'))
        result = {status: 0 for status in ['pending', 'approved', 'rejected']}
        for item in stats:
            result[item['status']] = item['count']
        return Response(result)
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        report = self.get_object()
        new_status = request.data.get('status')
        resolution_note = request.data.get('resolution_note', '')
        
        if new_status not in ['approved', 'rejected']:
            return Response(
                {"detail": "Невірний статус. Допустимі значення: 'approved' або 'rejected'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        report.status = new_status
        report.resolution_note = resolution_note
        report.processed_at = timezone.now()
        report.save()
        
        if new_status == 'approved':
            Report.check_campaign_reports(report.fundraiser.id)
        
        return Response(self.get_serializer(report).data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsModeratorOrAdmin])
    def for_moderation(self, request):
        try:
            # Get all reports for moderation
            queryset = Report.objects.all().select_related('fundraiser', 'user')
            
            # Get pending reports
            pending_reports = queryset.filter(status='pending').order_by('-created_at')
            
            # Base queryset for processed reports (before slicing)
            processed_base = queryset.filter(
                Q(status='approved') | Q(status='rejected')
            ).order_by('-processed_at')
            
            # Calculate stats using the unsliced queryset
            stats = {
                'pending': pending_reports.count(),
                'approved': queryset.filter(status='approved').count(),
                'rejected': queryset.filter(status='rejected').count()
            }
            
            # Only slice the queryset for the response data
            processed_reports = processed_base[:10]
            
            # Serialize the data
            serializer = self.get_serializer(pending_reports, many=True)
            processed_serializer = self.get_serializer(processed_reports, many=True)
            
            return Response({
                'pending': serializer.data,
                'recently_processed': processed_serializer.data,
                'stats': stats
            })
        except Exception as e:
            logger.error(f"Error in for_moderation: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Internal server error", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    def get_permissions(self):
        if self.action in ['for_moderation', 'update_status']:
            return [IsModeratorOrAdmin()]
        return super().get_permissions()
    @action(detail=False, methods=['get'])
    def check(self, request):
        fundraiser_id = request.query_params.get('fundraiser')
        if not fundraiser_id:
            return Response(
                {"detail": "Параметр fundraiser обов'язковий"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        last_24h = timezone.now() - timedelta(hours=24)
        existing = Report.objects.filter(
            fundraiser_id=fundraiser_id,
            user=request.user,
            created_at__gte=last_24h
        ).first()
        
        if existing:
            return Response({
                "exists": True,
                "created_at": existing.created_at,
                "next_available": existing.created_at + timedelta(hours=24)
            })
        
        return Response({"exists": False})
    # Add this to your ReportViewSet to handle campaign moderation
    @action(detail=True, methods=['patch'], permission_classes=[IsModeratorOrAdmin])
    def update_campaign_status(self, request, pk=None):
        campaign = DonationCampaign.objects.get(id=pk)
        action = request.data.get('action')  # 'approve' or 'reject'
        resolution_note = request.data.get('resolution_note', '')
        
        if action == 'approve':
            campaign.needs_moderation = False
            campaign.is_active = True
            campaign.moderation_status = 'approved'
        elif action == 'reject':
            campaign.needs_moderation = False
            campaign.is_active = False
            campaign.moderation_status = 'rejected'
        else:
            return Response(
                {"detail": "Invalid action. Use 'approve' or 'reject'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        campaign.moderation_notes = resolution_note
        campaign.save()
        
        return Response({
            "id": campaign.id,
            "status": "success",
            "moderation_status": campaign.moderation_status
        })