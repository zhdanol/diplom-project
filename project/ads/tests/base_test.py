from rest_framework.test import APITestCase
from unittest.mock import patch
from django.contrib.auth import get_user_model
from ads.models import Shop, Category, Product, ProductInfo

User = get_user_model()

class BaseAPITestCase(APITestCase):
    
    def setUp(self):
        super().setUp()
        
        self.throttle_patchers = []
        
        views_to_patch = [
            'ads.views.RegisterUser',
            'ads.views.LoginUser',
            'ads.views.ProductImageView',
            'ads.views.ProductMainImageView',
            'ads.views.CartView',
            'ads.views.PartnerState',
            'ads.views.PartnerOrders',
            'ads.views.PartnerUpdate',
            'ads.views.ContactView',
            'ads.views.OrderView',
        ]
        
        for view in views_to_patch:
            patcher = patch(f'{view}.throttle_classes', [])
            self.throttle_patchers.append(patcher)
            patcher.start()
    
    def tearDown(self):
        for patcher in self.throttle_patchers:
            patcher.stop()
        super().tearDown()