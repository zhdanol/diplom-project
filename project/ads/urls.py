from django.urls import path
from .views import (RegisterUser, EmailConfirmUser, LoginUser,
                    ProductInfoView, CategoryView, ShopView,
                    CartView, PartnerState, PartnerOrders,
                    PartnerUpdate, ContactView, OrderView, SocialLoginCallbackView, social_auth, SentryView, PerformanceView)
from django.views.generic import TemplateView
from rest_framework.authtoken.views import obtain_auth_token
from .views import ProductImageView, ProductMainImageView

urlpatterns = [
    # Регистрация пользователя
    path('user/register/', RegisterUser.as_view(), name='user-register'),
    # Подтверждение email
    path('user/confirm/', EmailConfirmUser.as_view(), name='user-confirm'),
    # Авторизация
    path('user/login/', LoginUser.as_view(), name='user-login'),
    path('user/token/', obtain_auth_token, name='api-token-auth'),
    
    path('social/login/google/', TemplateView.as_view(template_name='social_login.html'), name='social-login-google'),
    path('social/login/github/', TemplateView.as_view(template_name='social_login.html'), name='social-login-github'),
    path('social/callback/', SocialLoginCallbackView.as_view(), name='social-login-google'),
    path('social/auth/<str:backend>/', social_auth, name='social-auth'),
    
    # Список товаров, категорий, магазинов
    path('products/', ProductInfoView.as_view(), name='product-list'),
    path('categories/', CategoryView.as_view(), name='category-list'),
    path('shops/', ShopView.as_view(), name='shop-list'),
    
    # Управление корзиной и заказами
    path('cart/', CartView.as_view(), name='cart'),
    path('contacts/', ContactView.as_view(), name='contacts'),
    path('orders/', OrderView.as_view(), name='orders'),
    
    # Детали заказа
    path('api/orders/<int:pk>/', OrderView.as_view(), name='order-detail'),
    
    path('test-sentry/', SentryView.as_view(), name='test-sentry'),
    path('performance-test/', PerformanceView.as_view(), name='performance-test'),
    
    # Партнёрский интервейс
    path('partner/state/', PartnerState.as_view(), name='partner-state'),
    path('partner/orders/', PartnerOrders.as_view(), name='partner-orders'),
    path('partner/update/', PartnerUpdate.as_view(), name='partner-update'),
    path('products/<int:product_id>/images/', ProductImageView.as_view(), name='product-images'),
    path('products/<int:product_id>/images/<int:pk>/', ProductImageView.as_view(), name='product-image-detail'),
    path('products/<int:product_id>/set-main-image/', ProductMainImageView.as_view(), name='set-main-image'),
]

