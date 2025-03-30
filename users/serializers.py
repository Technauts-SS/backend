from rest_framework import serializers
from .models import User
import re
import os

class UserSerializer(serializers.ModelSerializer):
    current_password = serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'phone_number',
            'password', 'current_password', 'new_password',
            'social_links', 'image', 'bio'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'id': {'read_only': True}
        }
    
    def validate_image(self, value):
        if value:
            # Максимальний розмір 2MB
            if value.size > 2 * 1024 * 1024:
                raise serializers.ValidationError("Розмір файлу не повинен перевищувати 2MB")
                
            # Дозволені розширення
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            ext = os.path.splitext(value.name)[1].lower()
            if ext not in valid_extensions:
                raise serializers.ValidationError(
                    "Непідтримуваний формат файлу. Підтримуються: JPG, JPEG, PNG, GIF"
                )
        return value
    
    def validate_phone_number(self, value):
        if not re.match(r'^\+?1?\d{10,14}$', value):
            raise serializers.ValidationError('Невірний формат телефону. Використовуйте +380XXXXXXXXX')
        return value
    
    def validate(self, data):
        # Перевірка паролів при оновленні
        if 'new_password' in data and 'current_password' not in data:
            raise serializers.ValidationError(
                {"current_password": "Для зміни пароля введіть поточний пароль"}
            )
        
        # Перевірка поточного пароля
        if 'current_password' in data and self.instance:
            if not self.instance.check_password(data['current_password']):
                raise serializers.ValidationError(
                    {"current_password": "Поточний пароль введено неправильно"}
                )
        
        return data
    
    def create(self, validated_data):
        # Видаляємо поля, які не належать до моделі User
        validated_data.pop('current_password', None)
        validated_data.pop('new_password', None)
        
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            **validated_data,
            password=password
        )
        
        return user
    
    def update(self, instance, validated_data):
        # Обробка зміни пароля
        if 'new_password' in validated_data:
            instance.set_password(validated_data['new_password'])
            validated_data.pop('new_password')
            validated_data.pop('current_password', None)
        
        # Видаляємо поля, які не потрібно оновлювати
        validated_data.pop('password', None)
        
        # Оновлення інших полів
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        instance.save()
        return instance