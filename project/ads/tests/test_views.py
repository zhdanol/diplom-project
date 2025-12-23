from .base_test import BaseAPITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from ads.models import Shop, Category, Product, ProductInfo, ProductImage
import json

User = get_user_model()

class ProductInfoViewTests(BaseAPITestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='productuser@example.com',
            password='password123'
        )
        self.user.is_active = True
        self.user.save()
        
        self.category = Category.objects.create(name='Electronics')
        self.shop = Shop.objects.create(name='Test Shop', state=True)
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category
        )
        self.product_info = ProductInfo.objects.create(
            product=self.product,
            shop=self.shop,
            name='Test Product Info',
            price=1000,
            price_rrc=1200,
            quantity=5
        )
        
        self.products_url = reverse('product-list')
        self.token = self.get_auth_token()
    
    def get_auth_token(self):
        login_response = self.client.post(
            reverse('user-login'),
            {'email': 'productuser@example.com', 'password': 'password123'}
        )
        return login_response.json()['Token']
    
    def test_get_products(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token}')
        response = self.client.get(self.products_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_products_filter_by_shop(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token}')
        response = self.client.get(f"{self.products_url}?shop_id={self.shop.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_products_filter_by_category(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token}')
        response = self.client.get(f"{self.products_url}?category_id={self.category.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ProductImageViewTests(BaseAPITestCase):
    
    def setUp(self):
        self.shop_user = User.objects.create_user(
            email='shopimage@example.com',
            password='password123',
            type='shop'
        )
        self.shop_user.is_active = True
        self.shop_user.save()
        
        self.category = Category.objects.create(name='Electronics')
        self.shop = Shop.objects.create(
            name='Image Shop',
            user=self.shop_user,
            state=True
        )
        self.product = Product.objects.create(
            name='Image Product',
            category=self.category
        )
        self.product_info = ProductInfo.objects.create(
            product=self.product,
            shop=self.shop,
            name='Image Product Info',
            price=2000,
            price_rrc=2200, 
            quantity=10
        )
        from django.core.files.uploadedfile import SimpleUploadedFile
        image_file = SimpleUploadedFile(
            name='test.jpg',
            content=b'',
            content_type='image/jpeg'
        )
        
        self.product_image = ProductImage.objects.create(
            product=self.product,
            image=image_file
        )
        
        self.images_url = reverse('product-images', kwargs={'product_id': self.product.id})
        self.image_detail_url = reverse('product-image-detail', kwargs={
            'product_id': self.product.id,
            'pk': self.product_image.id
        })
        self.token = self.get_auth_token()
    
    def get_auth_token(self):
        from unittest.mock import patch
        
        with patch('ads.views.LoginUser.throttle_classes', []):
            login_response = self.client.post(
                reverse('user-login'),
                {'email': 'shopimage@example.com', 'password': 'password123'}
            )
            return login_response.json()['Token']
    
    def test_get_product_images(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token}')
        response = self.client.get(self.images_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_product_image_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token}')
        response = self.client.get(self.image_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PartnerUpdateTests(BaseAPITestCase):
    
    def setUp(self):
        self.shop_user = User.objects.create_user(
            email='partnerupdate@example.com',
            password='password123',
            type='shop'
        )
        self.shop_user.is_active = True
        self.shop_user.save()
        
        self.partner_update_url = reverse('partner-update')
        self.token = self.get_auth_token()
    
    def get_auth_token(self):
        login_response = self.client.post(
            reverse('user-login'),
            {'email': 'partnerupdate@example.com', 'password': 'password123'},
            format='json'
        )
        return login_response.Json()['Token']
    
    def test_partner_update_missing_url(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token}')
        response = self.client.post(self.partner_update_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_partner_update_invalid_url(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token}')
        payload = {'url': 'not-a-valid-url'}
        response = self.client.post(self.partner_update_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
class UserRegistrationTests(BaseAPITestCase):
    
    def setUp(self):
        self.register_url = reverse('user-register')
    
    def test_successful_registration(self):
        payload = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'testuser@example.com',
            'password': 'TestPassword123',
            'password_confirm': 'TestPassword123',
            'company': 'Test Company',
            'position': 'Test Position'
        }
        response = self.client.post(self.register_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        self.assertTrue(response_data['Status'])
        self.assertIn('Token for email confirmation', response_data)
    
    def test_registration_missing_fields(self):
        payload = {
            'email': 'test@example.com',
            'password': 'password123'
        }
        response = self.client.post(self.register_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_registration_password_mismatch(self):
        payload = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test2@example.com',
            'password': 'Password123',
            'password_confirm': 'DifferentPassword',
            'company': 'Company',
            'position': 'Position'
        }
        response = self.client.post(self.register_url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class UserLoginTests(BaseAPITestCase):
    
    def setUp(self):
        self.login_url = reverse('user-login')
        self.user = User.objects.create_user(
            email='logintest@example.com',
            password='TestPassword123'
        )
        self.user.is_active = True
        self.user.save()
    
    def test_successful_login(self):
        payload = {
            'email': 'logintest@example.com',
            'password': 'TestPassword123'
        }
        response = self.client.post(self.login_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertTrue(response_data['Status'])
        self.assertIn('Token', response_data)
    
    def test_login_invalid_credentials(self):
        payload = {
            'email': 'logintest@example.com',
            'password': 'WrongPassword'
        }
        response = self.client.post(self.login_url, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_login_missing_credentials(self):
        response = self.client.post(self.login_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ShopViewTests(BaseAPITestCase):
    
    def setUp(self):
        self.shops_url = reverse('shops')
        self.shop = Shop.objects.create(
            name='Test Shop',
            state=True
        )
    
    def test_get_shops(self):
        response = self.client.get(self.shops_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_shop_filtering_active_only(self):
        Shop.objects.create(name='Inactive Shop', state=False)
        response = self.client.get(self.shops_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CategoryViewTests(BaseAPITestCase):
    
    def setUp(self):
        self.categories_url = reverse('categories')
        self.category = Category.objects.create(name='Test Category')
    
    def test_get_categories(self):
        response = self.client.get(self.categories_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ContactViewTests(BaseAPITestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='contacttest@example.com',
            password='password123'
        )
        self.user.is_active = True
        self.user.save()
        
        self.contacts_url = reverse('contacts')
        self.token = self.get_auth_token()
    
    def get_auth_token(self):
        login_response = self.client.post(
            reverse('user-login'),
            {'email': 'contacttest@example.com', 'password': 'password123'}
        )
        return login_response.json()['Token']
    
    def test_get_contacts_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token}')
        response = self.client.get(self.contacts_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_contact(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token}')
        payload = {
            'type': 'phone',
            'value': '+1234567890',
            'city': 'Test City',
            'street': 'Test Street',
            'phone': '+1234567890'
        }
        response = self.client.post(self.contacts_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class CartViewTests(BaseAPITestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='carttest@example.com',
            password='password123'
        )
        self.user.is_active = True
        self.user.save()
        
        self.cart_url = reverse('cart')
        self.token = self.get_auth_token()
        
        self.category = Category.objects.create(name='Electronics')
        self.shop = Shop.objects.create(name='Cart Shop')
        self.product = Product.objects.create(
            name='Cart Product',
            category=self.category
        )
        self.product_info = ProductInfo.objects.create(
            product=self.product,
            shop=self.shop,
            name='Cart Product Info',
            price=1500,
            quantity=20
        )
    
    def get_auth_token(self):
        login_response = self.client.post(
            reverse('user-login'),
            {'email': 'carttest@example.com', 'password': 'password123'}
        )
        return login_response.json()['Token']
    
    def test_get_cart(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token}')
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_add_to_cart(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token}')
        payload = {
            'items': json.dumps([
                {
                    'product_id': self.product_info.id,
                    'quantity': 2
                }
            ])
        }
        response = self.client.post(self.cart_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class ThrottlingTests(BaseAPITestCase):
    
    def test_registration_throttling(self):
        url = reverse('user-register')
        for _ in range(10):
            payload = {
                'first_name': 'Test',
                'last_name': 'User',
                'email': f'test{_}@example.com',
                'password': 'TestPassword123',
                'password_confirm': 'TestPassword123',
                'company': 'Company',
                'position': 'Position'
            }
            response = self.client.post(url, payload)
        
        payload = {
            'first_name': 'Extra',
            'last_name': 'User',
            'email': 'extra@example.com',
            'password': 'TestPassword123',
            'password_confirm': 'TestPassword123',
            'company': 'Company',
            'position': 'Position'
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)