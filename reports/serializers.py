from rest_framework import serializers
from .models import Report
from fundraising.models import DonationCampaign
from django.contrib.auth import get_user_model

User = get_user_model()
class ReportSerializer(serializers.ModelSerializer):
    fundraiser = serializers.PrimaryKeyRelatedField(
        queryset=DonationCampaign.objects.all(),
        error_messages={
            'does_not_exist': 'Кампанія з ID {pk_value} не існує',
            'incorrect_type': 'ID кампанії має бути числом'
        }
    )

    class Meta:
        model = Report
        fields = ['id', 'fundraiser', 'reason', 'status', 'created_at']
        extra_kwargs = {
            'reason': {
                'error_messages': {
                    'blank': "Причина скарги не може бути пустою"
                }
            }
        }

    def validate(self, data):
        if 'reason' not in data or not data['reason'].strip():
            raise serializers.ValidationError({
                'reason': ["Будь ласка, вкажіть причину скарги"]
            }, code='required')
        return data