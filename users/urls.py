from django.urls import path
from . import views


urlpatterns = [
    path('login/', views.login_user, name='login_user'),
    path('users/', views.user_list, name='user_list'),
    path('users/<int:pk>/', views.user_detail, name='user_detail'),
    path('users/register/', views.register_user, name='register_user'),  
    path("update-password/", views.update_password, name="update_password"),
]