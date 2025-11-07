from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils.translation import gettext_lazy as gettex
from django_rest_passwordreset.tokens import get_token_generator

STATE_CHOICES = (
    ('cart_status', 'Статус корзины')
    ('new', 'Новый')
    ('confirmed', 'Подтверждён')
    ('collected', 'Собран')
    ('sent', 'Собран')
    ('delivered', 'Доставлен')
    ('canceled', 'Отменён')
)

USER_TYPE_CHOICES = (
    ('shop', 'Магазин')
    ('buyer', 'Покупатель')
    
)

class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password = None, **extra_fields):
        if not email:
            raise ValueError('Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
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
# Create your models here.

class User(AdstractUser):
    
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
    
class Shop(models.Model):
    name = models.CharField(max_length=40, verbose_name='Название')
    url = models.URLField(verbose_name='Ссылка', null=False, blank=True)
    user = models.OneToOneField(User, verbose_name='Пользователь', blank=True, null=True, on_delete=models.CASCADE)
    state = models.BooleanField(verbose_name='Статус получение заказа', default=True)
    
    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Список магазинов'
        ordering = ('-name',)
    
    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=40, verbose_name='Название')
    shops = models.ManyToManyField(Shop, verbose_name='Магазины', related_name='categories', blank=True)
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Список категорий'
        ordering = ('-name')
    
    def __str__(self):
        return self.name
    
class Product(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название продукта')
    category = models.ForeignKey(Category, verbose_name='Категория', related_name='product', blank=True, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Список продуктов'
        ordering = ('-name')
        
    def __str__(self):
        return self.name
    
class ProductInfo(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название', blank=True)
    model = models.CharField(max_length=100, verbose_name='Модель', blank=True)
    external_id = models.PositiveIntegerField(verbose_name='Внешний id')
    product = models.ForeignKey(Product, verbose_name='Продукт', related_name='product_info', blank=True, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, verbose_name='Магазин', related_name='product_info', blank=True, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    price = models.PositiveIntegerField(verbose_name='Цена')
    price_rrc = models.PositiveBigIntegerField(verbose_name='Розичная цена')
    
    class Meta:
        verbose_name = 'Имя продукта'
        verbose_name_plural = 'Список имён параметров'
        ordering = ('-name')
        
    def __str__(self):
        return self.name
    
class Parameter(models.Model):
    name = models.CharField(max_length=40, verbose_name='Название')
    
    class Meta:
        verbose_name = 'Имя параметра'
        verbose_name_plural = 'Список имён параметров'
        ordering = ('-name')
        
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
    
class Order(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь', related_name='order', blank=True, on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True)
    status = models.CharField(verbose_name='Статус', choices=STATE_CHOICES, max_length=20)
    
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Список заказов'
        ordering = ('-name')
        
    def __str__(self):
        return f'{self.user}: {self.dt}'
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name='Заказ', related_name='order_items', blank=True, on_delete=models.CASCADE)
    product = models.ForeignKey(ProductInfo, verbose_name='Информация о продукте', related_name='order_items', blank=True, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, verbose_name='Магазин', related_name='order_item', blank=True, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Кол-во')
    
    class Meta:
        verbose_name = 'Заказанная позиция'
        verbose_name_related = 'Список заказанных позиций'
        constraints = [models.UniqueConstraint(fields=['order_id', 'product_info',], name='unique_order_item')]
    
    
class Contact(models.Model):
    type = 
    user
    value