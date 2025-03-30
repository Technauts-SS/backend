from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from django.contrib.auth import authenticate
from .serializers import UserSerializer
from .models import User

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для реєстрації, авторизації та управління користувачами
    Підтримує вхід за email
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        """
        Налаштування прав доступу:
        - Реєстрація та логін доступні для всіх
        - Інші операції вимагають авторизації
        """
        if self.action in ['create', 'login']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        """
        Реєстрація нового користувача
        --- 
        Параметри:
        - email (обов'язковий)
        - password (обов'язковий)
        - full_name (опціонально)
        - phone_number (опціонально)
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Додаткова валідація email
        if User.objects.filter(email=serializer.validated_data.get('email')).exists():
            return Response(
                {'error': 'Користувач з таким email вже існує'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = serializer.save()
        token = Token.objects.create(user=user)
        
        return Response({
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name
            },
            'token': token.key
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def login(self, request):
        """
        Авторизація користувача (по email)
        --- 
        Параметри:
        - email (обов'язковий)
        - password (обов'язковий)
        """
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Необхідно вказати email та пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Спроба знайти користувача по email
        user = User.objects.filter(email=email).first()

        if not user or not user.check_password(password):
            return Response(
                {'error': 'Невірні облікові дані'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Аутентифікація
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.id,
            'email': user.email,
            'full_name': user.full_name
        })

    @action(detail=False, methods=['post'])
    def logout(self, request):
        """
        Вийти з системи (видалити токен)
        --- 
        Заголовки:
        - Authorization: Token <ваш_токен>
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Користувач не авторизований'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        request.user.auth_token.delete()
        return Response({'success': 'Ви успішно вийшли з системи'})

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Отримати інформацію про поточного користувача
        --- 
        Заголовки:
        - Authorization: Token <ваш_токен>
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Необхідно авторизуватись'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
