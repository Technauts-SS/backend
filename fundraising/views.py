from rest_framework import generics, filters, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework import status
from .models import DonationCampaign
from .serializers import DonationCampaignSerializer

class CreateDonationCampaignView(generics.CreateAPIView):
    """Створення збору з підтримкою завантаження зображень."""
    queryset = DonationCampaign.objects.all()
    serializer_class = DonationCampaignSerializer
    parser_classes = [MultiPartParser, FormParser]
    renderer_classes = [JSONRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

class ListFundraisingsView(generics.ListAPIView):
    """Список зборів з можливістю пошуку та фільтрації."""
    serializer_class = DonationCampaignSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'category']
    ordering_fields = ['created_at', 'goal_amount', 'current_amount']
    ordering = ['-created_at']
    permission_classes = [permissions.AllowAny]

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
    permission_classes = [permissions.IsAuthenticated]
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
    permission_classes = [permissions.AllowAny]

class UpdateFundraisingView(generics.UpdateAPIView):
    """Оновлення збору."""
    queryset = DonationCampaign.objects.all()
    serializer_class = DonationCampaignSerializer
    lookup_field = "id"
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated]

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
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)