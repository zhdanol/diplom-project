from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (RegisterUser, EmailConfirmUser, LoginUser,
                    ProductInfoView, CategoryView, ShopView,
                    CartView, PartnerState, PartnerOrders,
                    PartnerUpdate, ContactView, OrderView)
urlpatterns = [
    path('user/register/', RegisterUser.as_view(), name='user-register'),
    path('user/confirm/', EmailConfirmUser.as_view(), name='user-confirm'),
    path('user/login/', LoginUser.as_view(), name='user-login'),
    path('products/', ProductInfoView.as_view(), name='product-list'),
    path('categories/', CategoryView.as_view(), name='category-list'),
    path('shops/', ShopView.as_view(), name='shop-list'),
    path('cart/', CartView.as_view(), name='cart'),
    path('contacts/', ContactView.as_view(), name='contacts'),
    path('orders/', OrderView.as_view(), name='orders'),
    path('partner/state', PartnerState.as_view(), name='partner-state'),
    path('partner/orders', PartnerOrders.as_view(), name='partner-orders'),
    path('partner/update', PartnerUpdate.as_view(), name='partner-update')
]
