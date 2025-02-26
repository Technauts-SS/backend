from rest_framework import serializers
from .models import DonationCampaign
import re
from django.utils import timezone


class DonationCampaignSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)
    progress = serializers.SerializerMethodField()
    days_left = serializers.SerializerMethodField()
    
    class Meta:
        model = DonationCampaign
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'current_amount']

    def get_progress(self, obj):
        return obj.progress_percentage()
    
    def get_days_left(self, obj):
        if not obj.ends_at:
            return None
        delta = obj.ends_at - timezone.now()
        return max(0, delta.days)

    def validate_contact_info(self, contact_info):
        if not contact_info:
            raise serializers.ValidationError('Контактна інформація є обов\'язковою.')
        return contact_info

    def validate_goal_amount(self, goal_amount):
        if goal_amount is not None and goal_amount <= 0:
            raise serializers.ValidationError('Цільова сума повинна бути більше нуля.')
        return goal_amount
    
    def validate_current_amount(self, current_amount):
        if current_amount is not None and current_amount < 0:
            raise serializers.ValidationError('Зібрана сума не може бути від\'ємною.')
        return current_amount

    def validate_donation_link(self, donation_link):
        if donation_link and not re.match(r'https?://', donation_link):
            raise serializers.ValidationError('Посилання має починатися з "http://" або "https://".')
        return donation_link

    def validate_evidence_file(self, evidence_file):
        """Перевіряє розмір і формат файлу."""
        if not evidence_file:
            return evidence_file
        
        valid_extensions = ['jpg', 'jpeg', 'png', 'pdf', 'docx']
        file_extension = evidence_file.name.split('.')[-1].lower()
        if file_extension not in valid_extensions:
            raise serializers.ValidationError("Недопустимий формат файлу. Дозволені формати: jpg, jpeg, png, pdf, docx.")

        max_size = 5 * 1024 * 1024  # 5 МБ
        if evidence_file.size > max_size:
            raise serializers.ValidationError("Файл занадто великий. Максимальний розмір: 5 МБ.")

        return evidence_file

    def validate_evidence_link(self, evidence_link):
        """Перевіряє, чи це правильне посилання."""
        if evidence_link and not re.match(r'https?://', evidence_link):
            raise serializers.ValidationError("Невірне посилання на доказ.")
        return evidence_link

    def validate_category(self, category):
        """Перевіряє, чи вибрана категорія є допустимою."""
        valid_categories = dict(DonationCampaign.CATEGORY_CHOICES).keys()
        if category not in valid_categories:
            return "other"  # Якщо категорія невідома, ставимо 'other'
        return category
    
    def validate_urgency(self, urgency):
        """Перевіряє правильність значення терміновості."""
        valid_urgencies = dict(DonationCampaign.URGENCY_CHOICES).keys()
        if urgency not in valid_urgencies:
            return "non-urgent"  # За замовчуванням - не терміново
        return urgency
    
    def validate_status(self, status):
        """Перевіряє правильність статусу кампанії."""
        valid_statuses = dict(DonationCampaign.STATUS_CHOICES).keys()
        if status not in valid_statuses:
            return "draft"  # За замовчуванням - чернетка
        return status
    
    def validate_help_type(self, help_type):
        """Перевіряє тип допомоги."""
        valid_types = ["money", "volunteer", "both"]
        if help_type not in valid_types:
            return "money"  # За замовчуванням - фінансова допомога
        return help_type

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