from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from django.contrib.auth import authenticate
from .serializers import UserSerializer
from .models import User

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ['create', 'login']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
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
                'full_name': user.full_name,
                'image': user.image.url if user.image else None
            },
            'token': token.key
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def login(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Необхідно вказати email та пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.filter(email=email).first()

        if not user or not user.check_password(password):
            return Response(
                {'error': 'Невірні облікові дані'},
                status=status.HTTP_400_BAD_REQUEST
            )

        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'image': user.image.url if user.image else None
        })

    @action(detail=False, methods=['post'])
    def logout(self, request):
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Користувач не авторизований'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        request.user.auth_token.delete()
        return Response({'success': 'Ви успішно вийшли з системи'})

    @action(detail=False, methods=['get', 'patch'])
    def me(self, request):
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Необхідно авторизуватись'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            data = serializer.data
            return Response(data)
            
        elif request.method == 'PATCH':
            # Спеціальна обробка для multipart/form-data (фото)
            serializer = self.get_serializer(
                request.user,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            
            response_data = serializer.data
            
            # Оновлюємо токен, якщо змінився пароль
            if 'new_password' in request.data:
                Token.objects.filter(user=request.user).delete()
                token = Token.objects.create(user=request.user)
                response_data['token'] = token.key
            
            return Response(response_data)