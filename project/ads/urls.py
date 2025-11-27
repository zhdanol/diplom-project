from django.urls import path
from .views import (RegisterUser, EmailConfirmUser, LoginUser,
                    ProductInfoView, CategoryView, ShopView,
                    CartView, PartnerState, PartnerOrders,
                    PartnerUpdate, ContactView, OrderView)
urlpatterns = [
    # Регистрация пользователя
    path('user/register/', RegisterUser.as_view(), name='user-register'),
    # Подтверждение email
    path('user/confirm/', EmailConfirmUser.as_view(), name='user-confirm'),
    # Авторизация
    path('user/login/', LoginUser.as_view(), name='user-login'),
    # Список товаров
    path('products/', ProductInfoView.as_view(), name='product-list'),
    # Список категорий
    path('categories/', CategoryView.as_view(), name='category-list'),
    # Список магазинов
    path('shops/', ShopView.as_view(), name='shop-list'),
    # Управление корзиной
    path('cart/', CartView.as_view(), name='cart'),
    # Управление контактами
    path('contacts/', ContactView.as_view(), name='contacts'),
    # Список заказов
    path('orders/', OrderView.as_view(), name='orders'),
    # Детали заказа
    path('api/orders/<int:pk>/', OrderView.as_view(), name='order-detail'),
    # Статус магазина
    path('partner/state', PartnerState.as_view(), name='partner-state'),
    # Заказы магазина
    path('partner/orders', PartnerOrders.as_view(), name='partner-orders'),
    # Обновление каталога
    path('partner/update', PartnerUpdate.as_view(), name='partner-update')
]
