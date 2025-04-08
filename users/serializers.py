from rest_framework import serializers
from django.core.validators import validate_email
from django.contrib.auth import get_user_model
import re

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        help_text=(
            "Пароль має відповідати наступним вимогам:\n"
            " Мінімум 8 символів\n"
            " Хоча б одна велика літера (A-Z)\n"
            " Хоча б одна мала літера (a-z)\n"
            " Хоча б одна цифра (0-9)\n"
            " Хоча б один спецсимвол ($!%<>?,)"
        )
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        help_text="Повторіть пароль для підтвердження."
    )
    password = serializers.CharField(write_only=True, required=True, style={"input_type": "password"})
    confirm_password = serializers.CharField(write_only=True, required=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ["id", "full_name", "email", "phone_number", "social_links", "avatar", "is_active", "password", "confirm_password"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_phone_number(self, phone_number):
        """Перевірка формату телефону"""
        if not phone_number:
            raise serializers.ValidationError("Номер телефону є обов'язковим.")
        
        pattern = r"^\+?[1-9]\d{7,14}$"
        if not re.match(pattern, phone_number):
            raise serializers.ValidationError("Невірний формат телефону. Використовуйте міжнародний формат, наприклад, +380123456789.")

        return phone_number

    def validate_email(self, email):
        """Перевірка електронної пошти"""
        if not email:
            raise serializers.ValidationError("Електронна пошта є обов'язковою.")

        try:
            validate_email(email)
        except:
            raise serializers.ValidationError("Невірний формат електронної пошти.")

        return email

    def validate_social_links(self, social_links):
        """Перевірка посилань на соцмережі"""
        if social_links and not re.match(r"https?://", social_links):
            raise serializers.ValidationError("Невірне посилання на соціальну мережу.")

        return social_links

    def validate_avatar(self, avatar):
        """Перевірка формату та розміру аватара"""
        if avatar:
            valid_extensions = ["jpg", "jpeg", "png"]
            file_name_parts = avatar.name.split(".")
            
            if len(file_name_parts) < 2 or file_name_parts[-1].lower() not in valid_extensions:
                raise serializers.ValidationError("Недопустимий формат аватара. Дозволені формати: jpg, jpeg, png.")

            max_size = 2 * 1024 * 1024  # 2 МБ
            if avatar.size > max_size:
                raise serializers.ValidationError("Файл занадто великий. Максимальний розмір: 2 МБ.")

        return avatar
    def validate(self, data):
        """Перевірка пароля та його підтвердження"""
        password = data.get("password")
        confirm_password = data.get("confirm_password")

        
        errors = []
        if len(password) < 8:
            errors.append("Мінімальна довжина - 8 символів.")
        if not re.search(r"[a-z]", password):
            errors.append("Має містити хоча б одну малу літеру (a-z).")
        if not re.search(r"[A-Z]", password):
            errors.append("Має містити хоча б одну велику літеру (A-Z).")
        if not re.search(r"\d", password):
            errors.append("Має містити хоча б одну цифру (0-9).")
        if not re.search(r"[^\w\s]", password):
            errors.append("Має містити хоча б один спецсимвол [^\w\s].")

        
        if errors:
            raise serializers.ValidationError({"password": " ".join(errors)})

        if password != confirm_password:
            raise serializers.ValidationError({"confirm_password": "Паролі не співпадають!"})

        return data
    '''
    def validate(self, data):
        """Перевірка, чи паролі збігаються"""
        passwrd = data.get("password")
        if(len(passwrd) < 8):
            raise serializers.ValidationError({"password": "Пароль повинен містити не менше 8 символів"})
        if data.get("password") != data.get("confirm_password"):
            raise serializers.ValidationError({"confirm_password": "Паролі не співпадають!"})

        return data
    '''
    def create(self, validated_data):
        """Створення користувача з хешуванням пароля"""
        validated_data.pop("confirm_password") 
        password = validated_data.pop("password")  
        user = User(**validated_data)  
        user.set_password(password) 
        user.save()
        return user