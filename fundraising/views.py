from rest_framework import generics, filters
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.renderers import JSONRenderer
from django.http import JsonResponse
from .models import DonationCampaign
from .serializers import DonationCampaignSerializer

class CreateDonationCampaignView(generics.CreateAPIView):
    """Створення збору з підтримкою завантаження зображень."""
    queryset = DonationCampaign.objects.all()
    serializer_class = DonationCampaignSerializer
    parser_classes = [MultiPartParser, FormParser]
    renderer_classes = [JSONRenderer]

class ListFundraisingsView(generics.ListAPIView):
    """Список зборів з можливістю пошуку за категорією, назвою та описом."""
    queryset = DonationCampaign.objects.all()
    serializer_class = DonationCampaignSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['category', 'title', 'description']

class RetrieveFundraisingView(generics.RetrieveAPIView):
    """Отримання деталей окремого збору."""
    queryset = DonationCampaign.objects.all()
    serializer_class = DonationCampaignSerializer
    lookup_field = "id"

class UpdateFundraisingView(generics.UpdateAPIView):
    """Оновлення збору з можливістю оновлення зображення."""
    queryset = DonationCampaign.objects.all()
    serializer_class = DonationCampaignSerializer
    lookup_field = "id"
    parser_classes = [MultiPartParser, FormParser]

class DeleteFundraisingView(generics.DestroyAPIView):
    """Видалення збору."""
    queryset = DonationCampaign.objects.all()
    serializer_class = DonationCampaignSerializer
    lookup_field = "id"

def campaign_list(request):
    """Заглушка для списку зборів."""
    return JsonResponse({"message": "Список зборів ще не реалізований"})
