from rest_framework import serializers
from .models import DonationCampaign, Donation
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class DonationCampaignSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)
    progress = serializers.SerializerMethodField()
    days_left = serializers.SerializerMethodField()
    creator_name = serializers.SerializerMethodField()
    creator_email = serializers.SerializerMethodField()
    approved_reports_count = serializers.SerializerMethodField()
    city_display = serializers.SerializerMethodField()
    
    class Meta:
        model = DonationCampaign
        fields = '__all__'
        read_only_fields = [
            'created_at', 
            'updated_at', 
            'current_amount',
            'creator',
            'creator_name',
            'creator_email',
            'approved_reports_count',
            'progress',
            'city_display'
        ]
        extra_kwargs = {
            'city': {'write_only': True}  # Приховуємо city, оскільки використовуємо city_display
        }

    def get_progress(self, obj):
        return obj.progress_percentage()
    
    def get_days_left(self, obj):
        if not obj.ends_at:
            return None
        delta = obj.ends_at - timezone.now()
        return max(0, delta.days)
    
    def get_creator_name(self, obj):
        return obj.creator_name
    
    def get_creator_email(self, obj):
        return obj.creator.email if obj.creator else None
    
    def get_approved_reports_count(self, obj):
        return obj.reports.filter(status='approved').count()
    
    def get_city_display(self, obj):
        """Повертає читабельну назву міста замість коду"""
        return obj.get_city_display()

    def validate(self, data):
        if not any(data.get(field) for field in ['evidence', 'evidence_file', 'evidence_link']):
            raise serializers.ValidationError("Необхідно надати хоча б один доказ")
        
        if data.get('ends_at') and data['ends_at'] < timezone.now():
            raise serializers.ValidationError("Дата завершення має бути в майбутньому")
        
        if data.get('help_type') == "volunteer" and data.get('goal_amount', 0) > 0:
            raise serializers.ValidationError("Для волонтерської допомоги не вказуйте цільову суму")
            
        return data

    def create(self, validated_data):
        # Встановлюємо статус залежно від суми
        if validated_data.get('goal_amount', 0) < 10000:
            validated_data['status'] = 'active'
        else:
            validated_data['status'] = 'pending'
            
        validated_data['creator'] = self.context['request'].user
        return super().create(validated_data)
    
    def to_representation(self, instance):
        try:
            data = super().to_representation(instance)
            
            # Додаємо URL повної версії зображення, якщо воно є
            if data.get('image'):
                request = self.context.get('request')
                if request is not None:
                    data['image'] = request.build_absolute_uri(data['image'])
            
            # Додаємо дефолтне зображення, якщо основне відсутнє
            if not data.get('image') and instance.category:
                data['image'] = self.get_default_image(instance.category)
            
            return data
        except Exception as e:
            logger.error(f"Serialization error: {str(e)}")
            raise serializers.ValidationError("Помилка серіалізації даних")

    def get_default_image(self, category):
        request = self.context.get('request')
        base_url = request.build_absolute_uri('/') if request else ''
        
        category_map = {
            "health": f"{base_url}static/defaults/health.png",
            "social": f"{base_url}static/defaults/social.png",
            "education": f"{base_url}static/defaults/education.png",
            "ecology": f"{base_url}static/defaults/ecology.png",
            "other": f"{base_url}static/defaults/other.png"
        }
        return category_map.get(category, f"{base_url}static/defaults/other.png")


class DonationSerializer(serializers.ModelSerializer):
    mock_card_number = serializers.CharField(write_only=True, required=False)
    name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    anonymous = serializers.BooleanField(required=False, default=True)
    message = serializers.CharField(required=False, allow_blank=True)
    campaign_title = serializers.SerializerMethodField()
    
    class Meta:
        model = Donation
        fields = [
            'id', 
            'campaign', 
            'campaign_title',
            'amount', 
            'status', 
            'created_at', 
            'mock_card_number', 
            'name', 
            'email', 
            'phone', 
            'anonymous', 
            'message',
            'payment_method'
        ]
        extra_kwargs = {
            'status': {'read_only': True},
            'payment_method': {'required': False, 'default': 'credit_card'}
        }
    
    def get_campaign_title(self, obj):
        return obj.campaign.title if obj.campaign else None
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Сума має бути більше 0")
        return value
    
    def create(self, validated_data):
        # Extract fields that aren't part of the Donation model
        mock_card_number = validated_data.pop('mock_card_number', None)
        
        # Remove extra fields that aren't in the model
        validated_data.pop('name', None)
        validated_data.pop('email', None)
        validated_data.pop('phone', None)
        validated_data.pop('anonymous', None)
        validated_data.pop('message', None)
        
        # Set user if authenticated
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        
        # Create the donation
        donation = Donation.objects.create(
            **validated_data,
            transaction_id=mock_card_number
        )
        
        return donation