from rest_framework import serializers
from .models import User
import re
from django.core.validators import validate_email
     

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

    def validate_phone_number(self, phone_number):
        if not phone_number:
            raise serializers.ValidationError('Номер телефону є обов\'язковим.')

        pattern = r'^\+?[1-9]\d{7,14}$'  # Глобальний міжнародний формат
        if not re.match(pattern, phone_number):
            raise serializers.ValidationError('Невірний формат телефону. Використовуйте міжнародний формат, наприклад, +380123456789.')

        return phone_number


    def validate_email(self, email):
        if not email:
            raise serializers.ValidationError("Електронна пошта є обов'язковою.")
        
        try:
            validate_email(email)
        except:
            raise serializers.ValidationError("Невірний формат електронної пошти.")
        
        return email

    def validate_social_links(self, social_links):
        if not social_links:
            return social_links
        
        if not re.match(r'https?://', social_links):
            raise serializers.ValidationError("Невірне посилання на соціальну мережу.")
        
        return social_links

    def validate_avatar(self, avatar):
        if avatar:
            valid_extensions = ['jpg', 'jpeg', 'png']
            file_extension = avatar.name.split('.')[-1].lower()
            
            if file_extension not in valid_extensions:
                raise serializers.ValidationError("Недопустимий формат аватара. Дозволені формати: jpg, jpeg, png.")
            
            max_size = 2 * 1024 * 1024  # 2 МБ
            if avatar.size > max_size:
                raise serializers.ValidationError("Файл занадто великий. Максимальний розмір: 2 МБ.")
        
        return avatar
