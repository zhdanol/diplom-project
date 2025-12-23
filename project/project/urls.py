"""
URL configuration for project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.contrib import admin
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from ads.views import(
    RegisterUser, EmailConfirmUser, LoginUser, CategoryView, ShopView, ProductInfoView, CartView, PartnerState, PartnerUpdate,
    ContactView, OrderView, ProductImageView, ProductMainImageView, SocialLoginCallbackView, PartnerOrders, SocialLoginProviderView
)
from django.urls import path, include


urlpatterns = [
    path('admin/', include('baton.urls')),
    path('admin/', admin.site.urls),
    path('api/', include('ads.urls')),
    path('api/auth/', include('rest_framework.urls')),
    
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    path('api/user/register/', RegisterUser.as_view(), name='user-register'),
    path('api/user/confirm/', EmailConfirmUser.as_view(), name='user-confirm'),
    path('api/user/login/', LoginUser.as_view(), name='user-login'),
    path('api/categories/', CategoryView.as_view(), name='categories'),
    path('api/shops/', ShopView.as_view(), name='shops'),
    path('api/products/', ProductInfoView.as_view(), name='products'),
    path('api/cart/', CartView.as_view(), name='cart'),
    path('api/partner/state/', PartnerState.as_view(), name='partner-state'),
    path('api/partner/orders/', PartnerOrders.as_view(), name='partner-orders'),
    path('api/partner/update/', PartnerUpdate.as_view(), name='partner-update'),
    path('api/contacts/', ContactView.as_view(), name='contacts'),
    path('api/orders/', OrderView.as_view(), name='orders'),
    path('api/orders/<int:pk>/', OrderView.as_view(), name='order-detail'),
    path('api/products/<int:product_id>/images/', ProductImageView.as_view(), name='product-images'),
    path('api/product-images/<int:pk>/', ProductImageView.as_view(), name='product-image-detail'),
    path('api/products/<int:product_id>/set-main-image/', ProductMainImageView.as_view(), name='set-main-image'),
    
    path('api/auth/social/callback/', SocialLoginCallbackView.as_view(), name='social-login-callback'),
    path('api/auth/social/<backend>/', SocialLoginCallbackView.as_view(), name='social-auth'),
    

    path('api/password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    path('social-auth/', include('social_django.urls', namespace='social')),
    path('api/auth/social/providers/', SocialLoginProviderView.as_view(), name='social-providers'),
    path('api/auth/social/<backend>/', SocialLoginCallbackView.as_view(), name='social-auth-callback'),
]


