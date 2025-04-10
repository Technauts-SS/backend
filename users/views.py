from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from django.contrib.auth import authenticate
from .models import User
from .serializers import UserSerializer
from .permissions import IsAdmin, IsSameUserOrAdmin
from rest_framework.authtoken.models import Token

class UserPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    pagination_class = UserPagination

    def get_permissions(self):
        if self.action in ['create', 'login']:
            return [AllowAny()]
        elif self.action == 'list':
            return [IsAdmin()]
        elif self.action in ['make_admin', 'make_moderator', 'make_user']:
            return [IsAdmin()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsSameUserOrAdmin()]
        return [IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def _change_role(self, user, new_role, request):
        if not request.user.is_admin:
            return Response(
                {"error": "Тільки адміни можуть змінювати ролі"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if user.id == request.user.id:
            return Response(
                {"error": "Не можна змінювати свою власну роль"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Оновлюємо роль і примусово зберігаємо
        user.role = new_role
        user.save(update_fields=['role'])  # Зберігаємо тільки поле role
        
        # Оновлюємо об'єкт з бази даних
        user.refresh_from_db()
        
        serializer = self.get_serializer(user)
        return Response({
            "status": f"Роль оновлено до {new_role}",
            "user": serializer.data
        })

    @action(detail=True, methods=['post'])
    def make_admin(self, request, pk=None):
        user = self.get_object()
        return self._change_role(user, User.Role.ADMIN, request)

    @action(detail=True, methods=['post'])
    def make_moderator(self, request, pk=None):
        print(f"Attempting to make user {pk} moderator")
        user = self.get_object()
        print(f"Current role: {user.role}")
        result = self._change_role(user, User.Role.MODERATOR, request)
        user.refresh_from_db()
        print(f"New role: {user.role}")
        return result

    @action(detail=True, methods=['post'])
    def make_user(self, request, pk=None):
        user = self.get_object()
        return self._change_role(user, User.Role.USER, request)

    @action(detail=False, methods=['post'])
    def login(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Необхідно вказати email та пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(email=email, password=password)

        if not user:
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
            'image': user.image.url if user.image else None,
            'role': user.role
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
            data['role'] = request.user.role
            return Response(data)
            
        elif request.method == 'PATCH':
            serializer = self.get_serializer(
                request.user,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            
            response_data = serializer.data
            response_data['role'] = user.role
            
            if 'password' in request.data:
                Token.objects.filter(user=request.user).delete()
                token = Token.objects.create(user=request.user)
                response_data['token'] = token.key
            
            return Response(response_data)