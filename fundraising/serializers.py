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
            'progress'
        ]

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
            if not data.get('image') and instance.category:
                data['image'] = self.get_default_image(instance.category)
            return data
        except Exception as e:
            logger.error(f"Serialization error: {str(e)}")
            raise serializers.ValidationError("Помилка серіалізації даних")

    def get_default_image(self, category):
        category_map = {
            "health": "/static/defaults/health.png",
            "social": "/static/defaults/social.png",
            "education": "/static/defaults/education.png",
            "ecology": "/static/defaults/ecology.png",
            "other": "/static/defaults/other.png"
        }
        return category_map.get(category, "/static/defaults/other.png")


class DonationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donation
        fields = ['id', 'campaign', 'amount', 'status', 'created_at']
        extra_kwargs = {
            'status': {'read_only': True},
        }
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Сума має бути більше 0")
        return value
    
    def create(self, validated_data):
        donation = Donation.objects.create(**validated_data)
        donation.process_payment()
        return donation