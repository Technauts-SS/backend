from rest_framework import serializers
from .models import User
import re

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'phone_number', 'password', 'social_links']
        extra_kwargs = {
            'password': {'write_only': True},
            'id': {'read_only': True}
        }

    def create(self, validated_data):
        # Використовуємо create_user для обробки хешування пароля
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data.get('full_name', ''),
            phone_number=validated_data['phone_number'],
            social_links=validated_data.get('social_links', '')
        )
        return user

    def validate_phone_number(self, value):
        # Базова валідація номера телефону
        if not re.match(r'^\+?1?\d{10,14}$', value):
            raise serializers.ValidationError('Невірний формат номера телефону')
        return value
