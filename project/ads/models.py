from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django_rest_passwordreset.tokens import get_token_generator
from imagekit.models import ImageSpecField, ProcessedImageField
from imagekit.processors import ResizeToFill, ResizeToFit, SmartResize, Transpose
from .imagekit_ import ProductThumbnail, ProductMedium, ProductLarge, ProductWebP, AdminThumbnail
from django.core.validators import FileExtensionValidator
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

def optimize_image(image_field, max_size=(1200, 1200), quality=85):
    img = Image.open(image_field)
    
    if img.width > max_size[0] or img.height > max_size[1]:
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
    output = BytesIO()
    img.save(output, format='JPEG', quality=quality, optimize=True)
    output.seek(0)
    
    return ContentFile(output.read(), image_field.name)

STATE_CHOICES = (
    ('cart', 'Корзина'),
    ('new', 'Новый'),
    ('confirmed', 'Подтверждён'),
    ('assembled', 'Собран'),
    ('sent', 'Отправлен'),
    ('delivered', 'Доставлен'),
    ('canceled', 'Отменён')
)

USER_TYPE_CHOICES = (
    ('admin', 'Администратор'),
    ('shop', 'Магазин'), 
    ('employee', 'Работник магазина'),
    ('buyer', 'Покупатель'),
)

CONTACT_TYPE = [
    ('phone', 'телефон'),
    ('email', 'email'),
    ('address', 'Адрес'),
]
# Модели


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password = None, **extra_fields):
        if not email:
            raise ValueError('Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using = self._db)
        return user
    
    def create_superuser(self, email, password, **extra_fields):
        
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_stuff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)

# Записи пользователей
class User(AbstractUser):
    
    REQUIRED_FIELDS = []
    objects = UserManager()
    USERNAME_FIELD = 'email'
    email = models.EmailField(('email address'), unique=True)
    company = models.CharField('Компания', max_length=40, blank=True)
    position = models.CharField('Должность', max_length=40, blank=True)
    type = models.CharField('Тип пользователя', choices=USER_TYPE_CHOICES, max_length=10, default='buyer')
    username = models.CharField('Имя пользователя', max_length=100, blank=True, null=True)
    
    
    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'список пользователей'
    def __str__(self):
        return f'{self.email}({self.get_type_display()})'
    
    
# Магазины-поставщики товаров
class Shop(models.Model):
    name = models.CharField(max_length=40, verbose_name='Название')
    url = models.URLField(verbose_name='Ссылка', null=True, blank=True)
    user = models.OneToOneField(User, verbose_name='Пользователь', blank=True, null=True, on_delete=models.CASCADE, related_name='shop')
    state = models.BooleanField(verbose_name='Статус получения заказов', default=True)
    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Список магазинов'
        ordering = ('-name',)
    
    def __str__(self):
        return self.name

class ConfirmEmailToken(models.Model):
    user = models.ForeignKey(User, related_name='confirm_email_tokens', on_delete=models.CASCADE, verbose_name=('Пользователь'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=('Дата создания'))
    key = models.CharField(('key'), max_length=65, db_index=True, unique=True)
    
    class Meta:
        verbose_name = 'Токен подтверждения Email'
        verbose_name_plural = 'Токены подтверждения Email'
        
    def save(self, *args, **kwargs):
        if not self.key:
            self.key = get_token_generator().generate_token()
        return super().save(*args, **kwargs)
    
    def __str__(self):
         return f'Токен для {self.user}'
        
        
# Категории товаров
class Category(models.Model):
    name = models.CharField(max_length=40, verbose_name='Название')
    shops = models.ManyToManyField(Shop, verbose_name='Магазины', related_name='categories', blank=True)
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Список категорий'
        ordering = ('-name',)
    
    def __str__(self):
        return self.name
    
class ProductImage(models.Model):
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE, 
        related_name='images',
        verbose_name='Товар'
    )
    image = ProcessedImageField(
        upload_to='product_images/%Y/%m/%d/',
        processors=[Transpose()],
        format='JPEG',
        options={'quality': 85},
        verbose_name='Оригинальное изображение',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])]
    )
    is_main = models.BooleanField(default=False, verbose_name='Гдавное изображение')
    alt_text = models.CharField(max_length=255, blank=True, verbose_name='Описание изображения')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    
    thumbnail = ImageSpecField(
        source='image',
        id='ads:product_thumbnail',  # ID зарегистрированной спецификации
    )
    
    medium = ImageSpecField(
        source='image',
        id='ads:product_medium',
    )
    
    large = ImageSpecField(
        source='image',
        id='ads:product_large',
    )
    
    web_optimized = ImageSpecField(
        source='image',
        id='ads:product_webp',
    )
    
    admin_thumbnail = ImageSpecField(
        source='image',
        id='ads:admin_thumbnail',
    )
    catalog_preview = ImageSpecField(
        source='image',
        processors=[Transpose(), ResizeToFill(300, 200)],
        format='JPEG',
        options={'quality': 80}
    )
    
    mobile_optimized = ImageSpecField(
        source='image',
        processors=[Transpose(), SmartResize(600, 600)],
        format='JPEG',
        options={'quality': 75}
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    update_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Изображение товара'
        ordering = ['order', 'created_at']
        unique_together = ['product', 'is_main']
        
    def __str__(self):
        return f"Изображение для {self.product.name}"
    
    def save(self, *args, **kwargs):
        if self.is_main:
            ProductImage.objects.filter(
                product=self.product,
                is_main=True
            ).exclude(pk=self.pk).update(is_main=False)
        
        if self.image and not self.pk:
            optimized_image = optimize_image(self.image)
            self.image.save(self.image.name, optimized_image, save=False)
        
        super().save(*args, **kwargs)
        
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('product-image-detail', kwargs={'pk': self.pk})
    
    def get_all_variants(self):
        return {
            'original': self.image.url,
            'thumbnail': self.thumbnail.url if hasattr(self.thumbnail, 'url') else None,
            'medium': self.medium.url if hasattr(self.medium, 'url') else None,
            'large': self.large.url if hasattr(self.large, 'url') else None,
            'web_optimized': self.web_optimized.url if hasattr(self.web_optimized, 'url') else None,
            'admin_thumbnail': self.admin_thumbnail.url if hasattr(self.admin_thumbnail, 'url') else None,
            'catalog_preview': self.catalog_preview.url if hasattr(self.catalog_preview, 'url') else None,
            'mobile_optimized': self.mobile_optimized.url if hasattr(self.mobile_optimized, 'url') else None,
        }        
    
# Основная информация о товаре
class Product(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название продукта')
    category = models.ForeignKey(Category, verbose_name='Категория', related_name='products', blank=True, on_delete=models.CASCADE)
    description = models.TextField(blank=True, verbose_name='Описание')
    sku = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name='Артикул')
    
    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Список продуктов'
        ordering = ('-name',)
        
    def __str__(self):
        return self.name
    
    def get_main_image(self):
        return self.images.filter(is_main=True).first()

    def get_image_url(self, size='medium'):
        main_image = self.get_main_image()
        if main_image:
            if size == 'thumbnail':
                return main_image.thumbnail.url
            elif size == 'large':
                return main_image.large.url
            elif size == 'web':
                return main_image.web_optimized.url
            else:
                return main_image.medium.url
        return None

# Конкретные данные товара в магазине (цена, количество) 
class ProductInfo(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название', blank=True)
    product = models.ForeignKey(Product, verbose_name='Продукт', related_name='product_infos', blank=True, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, verbose_name='Магазин', related_name='product_infos', blank=True, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    price = models.PositiveIntegerField(verbose_name='Цена')
    price_rrc = models.PositiveIntegerField(verbose_name='Розничная цена')
    
    class Meta:
        verbose_name = 'Имя продукта'
        verbose_name_plural = 'Список параметров продукта'
        ordering = ('-name',)
        
    def __str__(self):
        return self.name
    
    
class Parameter(models.Model):
    name = models.CharField(max_length=40, verbose_name='Название')
    
    class Meta:
        verbose_name = 'Имя параметра'
        verbose_name_plural = 'Список имён параметров'
        ordering = ('-name',)
        
    def __str__(self):
        return self.name
    
    
class ProductParameter(models.Model):
    product_info = models.ForeignKey(ProductInfo, verbose_name='Информация о продукте', related_name='product_parameters', blank=True, on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, verbose_name='Параметр', related_name='product_parameters', blank=True, on_delete=models.CASCADE)
    value = models.CharField(verbose_name='Значение', max_length=50)
    
    class Meta:
        verbose_name = 'Параметр'
        verbose_name_plural = 'Список параметров'
        constraints = [
            models.UniqueConstraint(fields=['product_info', 'parameter'], name='unique_product_parameter')
        ]
    def __str__(self):
        return f'{self.product_info}:{self.parameter.name}'
    
# Заказы пользователей    
class Order(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь', related_name='orders', blank=True, on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True)
    status = models.CharField(verbose_name='Статус', choices=STATE_CHOICES, max_length=20)
    
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Список заказов'
        ordering = ('-dt',)
        
    def __str__(self):
        return f'{self.user}: {self.dt}'
    

# Конкретные товары в заказе
class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name='Заказ', related_name='order_items', blank=True, on_delete=models.CASCADE)
    product = models.ForeignKey(ProductInfo, verbose_name='Информация о продукте', related_name='order_items', blank=True, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, verbose_name='Магазин', related_name='order_item', blank=True, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Кол-во')
    
    class Meta:
        verbose_name = 'Заказанная позиция'
        verbose_name_plural = 'Список заказанных позиций'
        constraints = [
            models.UniqueConstraint(fields=['order', 'product'], name='unique_order_item')
            ]   

# Адреса доставки и контакты пользователей
class Contact(models.Model):
    type = models.CharField(verbose_name='Тип контакта', max_length=20, choices=CONTACT_TYPE, default='phone')
    user = models.ForeignKey(User, verbose_name='Пользователь', related_name='contacts', on_delete=models.CASCADE)
    country = models.CharField(verbose_name='Страна', max_length=50, blank=True, null=True)
    region = models.CharField(verbose_name='Регион', max_length=50, blank=True, null=True)
    city = models.CharField(verbose_name='Город', max_length=50, blank=True, null=True)
    street = models.CharField(verbose_name='Улица', max_length=100, blank=True, null=True)
    house = models.CharField(verbose_name='Дом', max_length=10, blank=True, null=True)
    building = models.CharField(verbose_name='Корпус/Строение', max_length=10, blank=True, null=True)
    structure = models.CharField(verbose_name='Строение', max_length=10, blank=True, null=True)
    apartment = models.CharField(verbose_name='Квартира', max_length=10, blank=True, null=True)
    phone = models.CharField(verbose_name='Телефон', max_length=20, blank=True, null=True)
    value = models.CharField(verbose_name='Значение', max_length=150)
    
    is_main = models.BooleanField(verbose_name='Основной контакт', default=False)
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Контакт'
        verbose_name_plural = 'Контакты'
        constraints = [models.UniqueConstraint(fields=['user', 'type', 'value'], name='unique_user_contact')]
        ordering = ['-is_main', 'type']
        
        
    def __str__(self):
        return f'{self.user.email}: {self.get_type_display()} - {self.get_display_value()}'
    
    def get_display_value(self):
        if self.type == 'address':
            return self.get_full_address()
        elif self.type == 'phone':
            return self.phone or self.value
        else:
            return self.value
    
    def get_full_address(self):
        address_parts = []
        
        if self.country:
            address_parts.append(self.country)
        if self.region:
            address_parts.append(self.region)
        if self.city:
            address_parts.append(f'Г. {self.city}')
        if self.street:
            address_parts.append(f'Ул. {self.street}')
            
        building_parts = []

        if self.house:
            address_parts.append(f'Д. {self.house}')
        if self.building:
            address_parts.append(f'Корп. {self.building}')
        if self.structure:
            address_parts.append(f'Стр. {self.structure}')
        if self.apartment:
            address_parts.append(f'Кв. {self.apartment}')
            
        if building_parts:
            address_parts.append(', '.join(building_parts))
            
        return ', '.join(address_parts)
    
    def clean(self):
        if self.type == 'phone' and not (self.phone or self.value):
            raise ValidationError('Необъходимо указать телефон')
        if self.type == 'email' and not (self.phone or self.value):
            raise ValidationError('Необъходимо указать email')
        if self.type == 'address' and not any([self.city, self.street, self.house]):
            raise ValidationError('Необъходимо указать город, улицу и дом')
    
    def save(self, *args, **kwargs):
        if self.is_main:
            Contact.objects.filter(
                user=self.user,
                type=self.type,
                is_main=True
            ).exclude(pk=self.pk).update(is_main=False)
            
        if self.type == 'address' and not self.value:
            self.value = self.get_full_address()
        
        super().save(*args, **kwargs)
        
