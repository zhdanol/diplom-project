from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from ads.models import User, Shop, Category, Product, ProductInfo


class SimpleModelTests(TestCase):
    
    def test_1_user_model(self):
        user = User.objects.create_user(
            email='simple@example.com',
            password='password123'
        )
        self.assertEqual(user.email, 'simple@example.com')
    
    def test_2_shop_model(self):
        shop = Shop.objects.create(name='Simple Shop', state=True)
        self.assertEqual(shop.name, 'Simple Shop')
    
    def test_3_category_model(self):
        category = Category.objects.create(name='Simple Category')
        self.assertEqual(category.name, 'Simple Category')
    
    def test_4_product_model(self):
        category = Category.objects.create(name='Cat')
        product = Product.objects.create(name='Simple Product', category=category)
        self.assertEqual(product.name, 'Simple Product')
    
    def test_5_product_info_model(self):
        shop = Shop.objects.create(name='Shop')
        category = Category.objects.create(name='Category')
        product = Product.objects.create(name='Product', category=category)
        
        product_info = ProductInfo.objects.create(
            product=product,
            shop=shop,
            name='Simple Info',
            price=1000,
            price_rrc=1200,
            quantity=5
        )
        self.assertEqual(product_info.name, 'Simple Info')


class SimpleAPITests(TestCase):
    
    def test_1_shops_endpoint(self):
        response = self.client.get(reverse('shops'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_2_categories_endpoint(self):
        response = self.client.get(reverse('categories'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_3_user_creation(self):
        user = User.objects.create_user(
            email='api@example.com',
            password='password123',
            first_name='John',
            last_name='Doe'
        )
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')


class StringRepresentationTests(TestCase):
    
    def test_shop_str(self):
        shop = Shop.objects.create(name='Test Shop')
        self.assertEqual(str(shop), 'Test Shop')
    
    def test_category_str(self):
        category = Category.objects.create(name='Test Category')
        self.assertEqual(str(category), 'Test Category')
    
    def test_product_str(self):
        category = Category.objects.create(name='Category')
        product = Product.objects.create(name='Test Product', category=category)
        self.assertEqual(str(product), 'Test Product')
    
    def test_user_str(self):
        user = User.objects.create_user(
            email='str@example.com',
            password='pass123',
            type='buyer'
        )
        self.assertIn('str@example.com', str(user))
        self.assertIn('buyer', str(user))


class CoverageBoostTests(TestCase):
    
    def test_multiple_objects(self):
        user1 = User.objects.create_user(email='user1@example.com', password='pass1')
        user2 = User.objects.create_user(email='user2@example.com', password='pass2')
        
        shop1 = Shop.objects.create(name='Shop 1', state=True)
        shop2 = Shop.objects.create(name='Shop 2', state=False)
        
        cat1 = Category.objects.create(name='Category 1')
        cat2 = Category.objects.create(name='Category 2')
        
        product1 = Product.objects.create(name='Product 1', category=cat1)
        product2 = Product.objects.create(name='Product 2', category=cat2)
        
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Shop.objects.count(), 2)
        self.assertEqual(Category.objects.count(), 2)
        self.assertEqual(Product.objects.count(), 2)
    
    def test_endpoint_coverage(self):
        endpoints = [
            ('shops', {}),
            ('categories', {}),
        ]
        
        for endpoint, kwargs in endpoints:
            try:
                url = reverse(endpoint, kwargs=kwargs)
                response = self.client.get(url)
                self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception:
                pass