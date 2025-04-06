from rest_framework import serializers
from .models import DonationCampaign, MockDonation
import re
from django.utils import timezone

class DonationCampaignSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)
    progress = serializers.SerializerMethodField()
    days_left = serializers.SerializerMethodField()
    creator_name = serializers.CharField(source='creator.full_name', read_only=True)
    creator_email = serializers.EmailField(source='creator.email', read_only=True)
    
    class Meta:
        model = DonationCampaign
        fields = '__all__'
        read_only_fields = [
            'created_at', 
            'updated_at', 
            'current_amount',
            'creator',
            'creator_name',
            'creator_email'
        ]

    def get_progress(self, obj):
        return obj.progress_percentage()
    
    def get_days_left(self, obj):
        if not obj.ends_at:
            return None
        delta = obj.ends_at - timezone.now()
        return max(0, delta.days)

    def validate(self, data):
        """Додаткові валідації для всього об'єкта."""
        # Перевіряємо, що хоча б одне поле з доказами заповнене
        if not any(data.get(field) for field in ['evidence', 'evidence_file', 'evidence_link']):
            raise serializers.ValidationError("Необхідно надати хоча б один доказ: текст, файл або посилання.")
        
        # Перевіряємо, що дата завершення в майбутньому
        if data.get('ends_at') and data['ends_at'] < timezone.now():
            raise serializers.ValidationError("Дата завершення кампанії повинна бути в майбутньому.")
        
        # Перевіряємо узгодженість типу допомоги і цільової суми
        if data.get('help_type') == "volunteer" and data.get('goal_amount', 0) > 0:
            raise serializers.ValidationError("Для волонтерської допомоги не потрібно вказувати цільову суму.")
            
        return data

    def create(self, validated_data):
        """Перевизначений метод create для автоматичного встановлення creator"""
        validated_data['creator'] = self.context['request'].user
        return super().create(validated_data)
    
class MockDonationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MockDonation
        fields = ['id', 'campaign', 'amount', 'status', 'mock_card_number', 'created_at']
        extra_kwargs = {
            'mock_card_number': {'write_only': True},
            'status': {'read_only': True},
        }
    
    def validate_mock_card_number(self, value):
        if not value.isdigit() or len(value) != 16:
            raise serializers.ValidationError("Номер картки повинен містити 16 цифр")
        return value
    
    def create(self, validated_data):
        donation = MockDonation.objects.create(**validated_data)
        donation.process_payment()
        return donation
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Сума донату повинна бути більше 0")
        return value