from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from ads.models import User, Shop, Category, Product, ProductInfo, Contact


class BasicTests(TestCase):
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpassword123',
            is_active=True
        )
        self.shop = Shop.objects.create(name='Test Shop', state=True)
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category
        )
        self.product_info = ProductInfo.objects.create(
            product=self.product,
            shop=self.shop,
            name='Test Product Info',
            price=1000,
            quantity=5
        )
    
    def test_user_creation(self):
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpassword123'))
    
    def test_shop_creation(self):
        self.assertEqual(self.shop.name, 'Test Shop')
        self.assertTrue(self.shop.state)
    
    def test_product_creation(self):
        self.assertEqual(self.product.name, 'Test Product')
        self.assertEqual(self.product.category, self.category)
    
    def test_shop_list_endpoint(self):
        url = reverse('shops')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_category_list_endpoint(self):
        url = reverse('categories')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ModelTests(TestCase):
    
    def test_contact_model(self):
        user = User.objects.create_user(email='contact@example.com', password='pass123')
        contact = Contact.objects.create(
            user=user,
            type='phone',
            value='+1234567890',
            city='Москва',
            street='Ленина',
            phone='+1234567890'
        )
        
        self.assertEqual(contact.type, 'phone')
        self.assertEqual(contact.user, user)
    
    def test_product_info_model(self):
        shop = Shop.objects.create(name='Model Shop')
        category = Category.objects.create(name='Model Category')
        product = Product.objects.create(name='Model Product', category=category)
        
        product_info = ProductInfo.objects.create(
            product=product,
            shop=shop,
            name='Model Product Info',
            price=1500,
            quantity=10
        )
        
        self.assertEqual(product_info.price, 1500)
        self.assertEqual(product_info.quantity, 10)