from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from fundraising.models import DonationCampaign
from .models import Report
from .serializers import ReportSerializer
from django.utils import timezone
from datetime import timedelta
from rest_framework.decorators import action
from django.db.models import Count, Q
from users.permissions import IsModeratorOrAdmin
import logging
from django.db import transaction 
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all().select_related('fundraiser', 'user')
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if not (self.request.user.is_staff or self.request.user.role in ['moderator', 'admin']):
            queryset = queryset.filter(user=self.request.user)
        return queryset
    
    def create(self, request, *args, **kwargs):
        logger.info(f"Incoming report data: {request.data}")
        logger.info(f"From user: {request.user.id}")

        try:
            # Валідація вхідних даних
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

            try:
                fundraiser_id = int(request.data['fundraiser'])
            except (ValueError, TypeError):
                return Response(
                    {"fundraiser": ["ID кампанії має бути числом"]},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not DonationCampaign.objects.filter(id=fundraiser_id).exists():
                return Response(
                    {"fundraiser": [f"Кампанія з ID {fundraiser_id} не існує"]},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Перевірка на дублікати за останні 24 години
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

            # Створення скарги
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            report = serializer.save(user=request.user)
            
            # Обробка скарги після створення
            self.process_new_report(report)
            
            logger.info(f"Report created: {serializer.data}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating report: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Внутрішня помилка сервера при створенні звіту"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def process_new_report(self, report):
        """Обробляє нову скаргу та виконує необхідні дії"""
        # Отримуємо кількість схвалених скарг на цей збір
        approved_reports_count = Report.objects.filter(
            fundraiser=report.fundraiser,
            status='approved'
        ).count()
        
        # Якщо скарг 3 або більше - призупиняємо збір
        if approved_reports_count >= 3:
            report.fundraiser.status = 'paused'
            report.fundraiser.save()
            logger.info(f"Campaign {report.fundraiser.id} paused due to 3+ approved reports")
        else:
            # Якщо скарг менше 3 - лише повідомляємо модератора
            self.notify_moderators(report)
    
    def notify_moderators(self, report):
        """Надсилає сповіщення модераторам про нову скаргу"""
        # Тут можна реалізувати відправку email, повідомлення в чат тощо
        logger.info(f"New report #{report.id} for campaign {report.fundraiser.id}. Notifying moderators")
        # Приклад відправки email:
        # send_mail_to_moderators(report)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        stats = Report.objects.values('status').annotate(count=Count('status'))
        result = {status: 0 for status in ['pending', 'approved', 'rejected']}
        for item in stats:
            result[item['status']] = item['count']
        return Response(result)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsModeratorOrAdmin])
    def update_status(self, request, pk=None):
        report = self.get_object()
        new_status = request.data.get('status')
        resolution_note = request.data.get('resolution_note', '')
        
        if new_status not in ['approved', 'rejected']:
            return Response(
                {"detail": "Invalid status. Use 'approved' or 'rejected'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Update report status
                report.status = new_status
                report.resolution_note = resolution_note
                report.processed_at = timezone.now()
                report.save()
                
                # If approved, check campaign status
                if new_status == 'approved':
                    report.update_campaign_status()
                
                return Response({
                    "status": "success",
                    "report_status": report.status,
                    "campaign_status": report.fundraiser.status
                })
                
        except Exception as e:
            logger.error(f"Error updating report status: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    def check_campaign_status(self, campaign):
        """Перевіряє кількість скарг та призупиняє збір при необхідності"""
        approved_reports_count = Report.objects.filter(
            fundraiser=campaign,
            status='approved'
        ).count()
        
        if approved_reports_count >= 3 and campaign.status == 'active':
            campaign.status = 'paused'
            campaign.save()
            logger.info(f"Campaign {campaign.id} paused due to 3+ approved reports")
    
    @action(detail=False, methods=['get'], permission_classes=[IsModeratorOrAdmin])
    def for_moderation(self, request):
        try:
            queryset = Report.objects.all().select_related('fundraiser', 'user')
            
            pending_reports = queryset.filter(status='pending').order_by('-created_at')
            processed_reports = queryset.filter(
                Q(status='approved') | Q(status='rejected')
            ).order_by('-processed_at')[:10]
            
            stats = {
                'pending': pending_reports.count(),
                'approved': queryset.filter(status='approved').count(),
                'rejected': queryset.filter(status='rejected').count()
            }
            
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
        if self.action in ['for_moderation', 'update_status', 'update_campaign_status']:
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
    
    @action(detail=True, methods=['patch'], permission_classes=[IsModeratorOrAdmin])
    def update_campaign_status(self, request, pk=None):
        try:
            campaign = DonationCampaign.objects.get(id=pk)
            action = request.data.get('action')  # 'approve' or 'reject'
            resolution_note = request.data.get('resolution_note', '')
            
            if action == 'approve':
                campaign.needs_moderation = False
                campaign.status = 'active'
            elif action == 'reject':
                campaign.needs_moderation = False
                campaign.status = 'cancelled'
            else:
                return Response(
                    {"detail": "Invalid action. Use 'approve' or 'reject'"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            campaign.save()
            
            return Response({
                "id": campaign.id,
                "status": "success",
                "campaign_status": campaign.status
            })
        except DonationCampaign.DoesNotExist:
            return Response(
                {"detail": "Campaign not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error updating campaign status: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )                               
    
    @action(detail=False, methods=['get'], url_path='count')
    def count_reports(self, request):
        fundraiser_id = request.query_params.get('fundraiser')
        if not fundraiser_id:
            return Response({"detail": "Fundraiser ID is required"}, status=400)

        count = Report.objects.filter(fundraiser_id=fundraiser_id).count()
        return Response({"count": count})
    
    def perform_create(self, serializer):
        report = serializer.save(user=self.request.user)
        report.fundraiser.handle_reports()

class ReportPublicCountView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        fundraiser_id = request.query_params.get('fundraiser')
        if not fundraiser_id:
            return Response(
                {"error": "Fundraiser ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        count = Report.get_public_count(fundraiser_id)
        return Response({"count": count})
