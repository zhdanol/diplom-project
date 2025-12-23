from django.test import TestCase, override_settings
from django.core import mail
from ads.models import User, Order, Shop, Category, Product, ProductInfo
from ..tasks import send_email, send_order_confirmation, send_invoice_admin


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
)
class CeleryTaskTests(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='tasktest@example.com',
            password='password123',
            is_active=True
        )
        
        self.category = Category.objects.create(name='Test Category')
        self.shop = Shop.objects.create(name='Test Shop')
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
            quantity=10
        )
        
        mail.outbox.clear()
    
    def test_send_email_task(self):
        result = send_email.delay(
            'Test Subject',
            'Test Message',
            'test@example.com'
        )
        
        self.assertEqual(result.state, 'SUCCESS')
    
    def test_send_order_confirmation_task(self):
        order = Order.objects.create(
            user=self.user,
            status='new'
        )
        
        result = send_order_confirmation.delay(order.id)

        self.assertEqual(result.state, 'SUCCESS')

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn(str(order.id), email.subject)
    
    def test_send_invoice_admin_task(self):
        order = Order.objects.create(
            user=self.user,
            status='new'
        )
        
        result = send_invoice_admin.delay(order.id)

        self.assertEqual(result.state, 'SUCCESS')

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn('Новая накладная', email.subject)