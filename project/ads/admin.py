from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Product, Category, Shop, Order, ProductInfo, Contact, OrderItem, Parameter, ProductParameter

# Register your models here.


# Админка для пользователей
@admin.register(User)
class CustomAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'company', 'position', 'type', 'is_staff')
    list_filter = ('type', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'company',)
    ordering = ('email',)


# Базовые товары
admin.site.register(Product)
# Категории товаров
admin.site.register(Category) 
# Магазины-поставщики
admin.site.register(Shop)
# Заказы пользователей
admin.site.register(Order)


# Расширенная админка для информации о товарах
@admin.register(ProductInfo)
class ProductInfoAdmin(admin.ModelAdmin):
    list_display = ['name', 'product', 'shop', 'price', 'quantity']
    list_filter = ['shop']
    search_fields = ['name', 'product__name']
    
    
# Контакты пользователей
admin.site.register(Contact)
# Позиции заказов
admin.site.register(OrderItem)
# Параметры товаров
admin.site.register(Parameter)
# Значения параметров товаров
admin.site.register(ProductParameter)