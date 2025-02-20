from django.shortcuts import render
from .models import User
from .models import DonationCampaign
from django.http import JsonResponse

# Create your views here.
def create_fundraising():
    pass

def get_fundraising():
    pass
    
def update_fundraising():
    pass

def delete_fundraising():
    pass

def get_list_fundraisings():
    pass



def campaign_list(request):
    return JsonResponse({"message": "Список зборів ще не реалізований"})