from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Product, Category, Shop, Order, ProductInfo, Contact, OrderItem, Parameter, ProductParameter

# Register your models here.
@admin.register(User)
class CustomAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'company', 'position', 'type', 'is_staff')
    list_filter = ('type', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'company',)
    ordering = ('email',)

admin.site.register(Product)
admin.site.register(Category) 
admin.site.register(Shop)
admin.site.register(Order)


@admin.register(ProductInfo)
class ProductInfoAdmin(admin.ModelAdmin):
    list_display = ['name', 'product', 'shop', 'price', 'quantity']
    list_filter = ['shop']
    search_fields = ['name', 'product__name']
    
admin.site.register(Contact)
admin.site.register(OrderItem)
admin.site.register(Parameter)
admin.site.register(ProductParameter)