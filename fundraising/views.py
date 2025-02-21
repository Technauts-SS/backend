from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from .models import DonationCampaign
from .serializers import DonationCampaignSerializer
from rest_framework import generics
from rest_framework.renderers import JSONRenderer

class CreateDonationCampaignView(generics.CreateAPIView):
    queryset = DonationCampaign.objects.all()
    serializer_class = DonationCampaignSerializer
    renderer_classes = [JSONRenderer]

class ListFundraisingsView(generics.ListAPIView):
    queryset = DonationCampaign.objects.all()
    serializer_class = DonationCampaignSerializer

class RetrieveFundraisingView(generics.RetrieveAPIView):
    queryset = DonationCampaign.objects.all()
    serializer_class = DonationCampaignSerializer
    lookup_field = "id"  

class UpdateFundraisingView(generics.UpdateAPIView):
    queryset = DonationCampaign.objects.all()
    serializer_class = DonationCampaignSerializer
    lookup_field = "id"

class DeleteFundraisingView(generics.DestroyAPIView):
    queryset = DonationCampaign.objects.all()
    serializer_class = DonationCampaignSerializer
    lookup_field = "id"

def campaign_list(request):
    return JsonResponse({"message": "Список зборів ще не реалізований"})
