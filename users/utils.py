import random
import string
from django.core.mail import send_mail

def generate_confirmation_code():
    """Генерує випадковий код підтвердження"""
    return ''.join(random.choices(string.digits, k=6))  # 6-значний код

def send_confirmation_email(user_email, code):
    """Надсилає код підтвердження на пошту користувача"""
    subject = "Код підтвердження реєстрації"
    message = f"Ваш код підтвердження для реєстрації: {code}. Він діє 15 хвилин."
    send_mail(subject, message, 'no-reply@yourdomain.com', [user_email])