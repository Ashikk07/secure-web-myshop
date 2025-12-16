from django.test import TestCase, Client
from django.contrib.auth.models import User
from store.models import Product
from .models import CartItem


class CartTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.product = Product.objects.create(name='Test Product', description='Test', price=10.00)

    def test_add_to_cart(self):
        self.client.login(username='testuser', password='pass')
        response = self.client.post('/cart/add/', {'product_id': self.product.id, 'quantity': 1})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CartItem.objects.count(), 1)
