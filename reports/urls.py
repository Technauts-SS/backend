from django.urls import path
from .views import ReportViewSet, ReportPublicCountView  # Додаємо новий View
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'', ReportViewSet, basename='report')

urlpatterns = [
    path('reports/<int:pk>/update_status/', 
        ReportViewSet.as_view({'patch': 'update_status'}), 
        name='report-update-status'),
    path('reports/public_count/', 
        ReportPublicCountView.as_view(), 
        name='reports-public-count'),
] + router.urls