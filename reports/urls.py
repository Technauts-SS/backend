from django.urls import path
from .views import ReportViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'', ReportViewSet, basename='report')

urlpatterns = [
    path('reports/<int:pk>/update_status/', 
        ReportViewSet.as_view({'patch': 'update_status'}), 
        name='report-update-status'),
] + router.urls