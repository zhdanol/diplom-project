from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin
from .models import User, Product, Category, Shop, Order, ProductInfo, Contact, OrderItem, Parameter, ProductParameter, ProductImage
from imagekit.admin import AdminThumbnail
        
admin.site.register(User)
# Базовые товары
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'product_count', 'image_preview']
    list_filter = ['category']
    search_fields = ['name', 'sku', 'description']
    readonly_fields = ['image_preview']
    
    admin_thumbnail = AdminThumbnail(image_field='admin_thumbnail')
    admin_thumbnail.short_description = 'Миниатюра'
    
    def image_preview(self, obj):
        main_image = obj.get_main_image()
        if main_image and main_image.thumbnail:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover;" />',
                main_image.thumbnail.url
            )
        return "Нет изображения"
    image_preview.short_description = 'Изображение'
    
    def product_count(self, obj):
        return obj.product_infos.count()
    product_count.short_description = 'Количество предложений'
# Категории товаров
admin.site.register(Category) 
# Магазины-поставщики
admin.site.register(Shop)
# Заказы пользователей
admin.site.register(Order)

admin.site.register(ProductInfo)

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['admin_thumbnail', 'product', 'is_main', 'order', 'created_at']
    list_filter = ['is_main', 'created_at']
    list_editable = ['order', 'is_main']
    search_fields = ['product__name', 'alt_text']
    raw_id_fields = ['product']
    
    admin_thumbnail = AdminThumbnail(image_field='thumbnail')
    admin_thumbnail.short_description = 'Миниатюра'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')

# Контакты пользователей
admin.site.register(Contact)
# Позиции заказов
admin.site.register(OrderItem)
# Параметры товаров
admin.site.register(Parameter)
# Значения параметров товаров
admin.site.register(ProductParameter)