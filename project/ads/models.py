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
    
    def kalcreate_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The email given you not found')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_user(self, email, password = None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)
    
    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_stuff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.kalcreate_user(email, password, **extra_fields)
# Create your models here.
