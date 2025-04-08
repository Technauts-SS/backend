from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import User, ConfirmationCode
from .serializers import UserSerializer
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth.hashers import check_password
from rest_framework.exceptions import PermissionDenied
from .utils import generate_confirmation_code, send_confirmation_email


@api_view(['POST'])
def login_user(request):
    """
    Логін користувача за допомогою емейлу та пароля.
    """
    email = request.data.get("email")
    password = request.data.get("password")
    
    if not email or not password:
        return Response({"error": "Будь ласка, надайте емейл та пароль."}, status=status.HTTP_400_BAD_REQUEST)

   
    user = authenticate(request, username=email, password=password)
    
    if user is not None:
       
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        
        serializer = UserSerializer(user)
        
        return Response({
            "message": "Успішний вхід!",
            "access_token": str(access_token),
            "user": serializer.data
        }, status=status.HTTP_200_OK)
    
    return Response({"error": "Неправильний емейл або пароль."}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def  update_password(request):
    """
    Забули пароль? Змінити пароль
    """

    permission_classes = [IsAuthenticated]
    user = request.user  
    new_password = request.data.get("password")
    confirm_password = request.data.get("confirm_password")

    if new_password != confirm_password:
        return Response({"error": "Паролі не співпадають"}, status=status.HTTP_400_BAD_REQUEST)

    
    user.set_password(new_password)
    user.save()

    return Response({"message": "Пароль успішно змінено"}, status=status.HTTP_200_OK)
"""
@api_view(['POST'])
def register_user(request):
    
    #Реєстрація нового користувача.
    #Генерація коду підтвердження та його надсилання.
    
    email = request.data.get('email')
    
    if not email:
        return Response({"error": "Електронна пошта не надана"}, status=status.HTTP_400_BAD_REQUEST)

    
    if User.objects.filter(email=email).exists():
        return Response({"error": "Користувач з таким email вже існує"}, status=status.HTTP_400_BAD_REQUEST)

    
    confirmation_code = generate_confirmation_code()
    send_confirmation_email(email, confirmation_code)

    
    user = User.objects.create(email=email)

    
    ConfirmationCode.objects.create(user=user, code=confirmation_code)

    return Response({"message": "Код підтвердження надіслано на вашу електронну пошту."}, status=status.HTTP_200_OK)
"""
@api_view(['POST'])
def verify_confirmation_code(request):
    """
    Перевірка коду підтвердження, отриманого на електронну пошту.
    """
    email = request.data.get('email')
    code = request.data.get('code')
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"error": "Користувач з таким email не знайдений."}, status=status.HTTP_400_BAD_REQUEST)
    
    confirmation_code = ConfirmationCode.objects.filter(user=user, code=code).first()

    if not confirmation_code:
        return Response({"error": "Невірний код підтвердження."}, status=status.HTTP_400_BAD_REQUEST)

    if confirmation_code.is_used:
        return Response({"error": "Цей код вже використано."}, status=status.HTTP_400_BAD_REQUEST)

    if confirmation_code.is_expired():
        return Response({"error": "Код підтвердження вичерпав свій час."}, status=status.HTTP_400_BAD_REQUEST)

    
    confirmation_code.is_used = True
    confirmation_code.save()

    
    return Response({"message": "Реєстрація успішна!"}, status=status.HTTP_200_OK)


@api_view(['POST'])
def register_user(request):
    
    #Реєстрація нового користувача
    
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "Користувач успішно створений!", "user": serializer.data},
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def user_list(request):
    """
    Отримати список всіх користувачів.
    """
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to view this resource.")
    
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)  

@api_view(['GET', 'PUT', 'DELETE'])
def user_detail(request, pk):
    """
    Отримати, оновити або видалити користувача.
    """
    user = get_object_or_404(User, pk=pk)

    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                if "password" in request.data:
                    user.set_password(request.data["password"])
                    user.save()
                
                serializer.save()
                updated_data = serializer.data
                updated_data.pop("password", None)                  
                return Response({"message": "Дані оновлено!", "user": updated_data})
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        user.delete()
        return Response({"message": "Користувача видалено!"}, status=status.HTTP_204_NO_CONTENT)
    

