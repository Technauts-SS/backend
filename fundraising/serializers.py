from rest_framework import serializers
from .models import DonationCampaign
import re


class DonationCampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = DonationCampaign
        fields = '__all__'

    def validate_contact_info(self, contact_info):
        if not contact_info:
            raise serializers.ValidationError('Контактна інформація є обов\'язковою.')
        return contact_info

    def validate_goal_amount(self, goal_amount):
        if goal_amount is not None and goal_amount < 0:
            raise serializers.ValidationError('Цільова сума не може бути від\'ємною.')
        return goal_amount

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

    def validate(self, data):
        """Гарантує, що хоча б одне поле з доказами заповнене."""
        if not any(data.get(field) for field in ['evidence', 'evidence_file', 'evidence_link']):
            raise serializers.ValidationError("Необхідно надати хоча б один доказ: текст, файл або посилання.")
        return data


    def validate_social_links(self, social_links):
        if not social_links:
            return social_links  # Якщо поле пусте, просто повертаємо його
        
        if not re.match(r'https?://', social_links):
            raise serializers.ValidationError("Невірне посилання на соціальну мережу.")
        
        return social_links
