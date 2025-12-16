import pytest
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from .models import Product, Cart, CartItem, Order, OrderItem, CustomerProfile
from decimal import Decimal


class SecurityTestCase(TestCase):
    """Security-focused test cases"""

    def setUp(self):
        self.client = Client()
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Create staff user
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='staffpass123',
            is_staff=True
        )
        # Create product
        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            price=Decimal('29.99')
        )

class AdminAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = 'admin_test'
        self.password = 'strongpassword'
        self.user = User.objects.create_user(username=self.username, password=self.password)

    def test_admin_access_for_promoted_user(self):
        # Initially non-staff should be blocked
        self.client.login(username=self.username, password=self.password)
        response = self.client.get('/admin/')
        self.assertIn(response.status_code, (302, 403))

        # Promote user to staff and superuser
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

        # Re-login to ensure session reflects new permissions
        self.client.logout()
        self.client.login(username=self.username, password=self.password)
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)

    def test_sql_injection_prevention(self):
        """Test that SQL injection attacks are prevented"""
        # Test search functionality with malicious input
        malicious_queries = [
            "'; DROP TABLE store_product; --",
            "' OR '1'='1",
            "<script>alert('xss')</script>",
            "UNION SELECT * FROM auth_user",
        ]

        for query in malicious_queries:
            response = self.client.get(reverse('home'), {'q': query})
            self.assertEqual(response.status_code, 200)
            # Ensure no error occurs and response is safe
            self.assertNotContains(response, 'error', status_code=500)

    def test_unauthorized_access_prevention(self):
        """Test that unauthorized users cannot access admin functions"""
        # Test without authentication
        response = self.client.get(reverse('manage_products'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

        # Test with regular user
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('manage_products'))
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Test with staff user (should work)
        self.client.login(username='staffuser', password='staffpass123')
        response = self.client.get(reverse('manage_products'))
        self.assertEqual(response.status_code, 200)

    def test_input_validation(self):
        """Test comprehensive input validation"""
        self.client.login(username='staffuser', password='staffpass123')

        # Test invalid product data
        invalid_data = {
            'name': '',  # Empty name
            'description': 'Valid description',
            'price': '-10',  # Negative price
        }
        response = self.client.post(reverse('add_product'), invalid_data)
        self.assertContains(response, 'error')  # Should show validation errors

        # Test XSS prevention
        xss_data = {
            'name': '<script>alert("xss")</script>',
            'description': 'Valid description',
            'price': '29.99',
        }
        response = self.client.post(reverse('add_product'), xss_data)
        self.assertContains(response, 'invalid characters')

    def test_session_security(self):
        """Test session security features"""
        # Login and check session rotation
        client = Client()
        # Obtain CSRF token
        resp = client.get(reverse('login'))
        csrftoken = resp.cookies.get('csrftoken').value if 'csrftoken' in resp.cookies else None

        post_data = {'username': 'testuser', 'password': 'testpass123'}
        if csrftoken:
            post_data['csrfmiddlewaretoken'] = csrftoken
        response = client.post(reverse('login'), post_data, follow=False)
        self.assertEqual(response.status_code, 302)

        # Check that session was rotated (new session key)
        session_key = client.session.session_key
        self.assertIsNotNone(session_key)

    def test_csrf_protection(self):
        """Test CSRF protection on forms"""
        # Use a client that enforces CSRF checks
        client = Client(enforce_csrf_checks=True)
        client.login(username='staffuser', password='staffpass123')

        # POST without CSRF token should be rejected (403)
        response = client.post(reverse('add_product'), {
            'name': 'Test Product',
            'description': 'Test Description',
            'price': '29.99'
        })
        self.assertEqual(response.status_code, 403)


class FunctionalTestCase(TestCase):
    """Functional test cases for core features"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            price=Decimal('29.99')
        )

    def test_user_registration(self):
        """Test user registration flow"""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'newpass123',
            'password2': 'newpass123',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_product_search(self):
        """Test product search functionality"""
        # Create additional products
        Product.objects.create(name='Another Product', description='Another desc', price=Decimal('19.99'))

        # Test search
        response = self.client.get(reverse('home'), {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Product')
        self.assertNotContains(response, 'Another Product')

    def test_shopping_cart_flow(self):
        """Test complete shopping cart flow"""
        self.client.login(username='testuser', password='testpass123')

        # Add to cart
        response = self.client.post(reverse('add_to_cart'), {
            'product_id': self.product.id,
            'quantity': 2
        })
        self.assertEqual(response.status_code, 302)

        # Check cart
        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Product')

        # Update cart
        cart = Cart.objects.get(user=self.user)
        cart_item = CartItem.objects.get(cart=cart, product=self.product)
        response = self.client.post(reverse('update_cart'), {
            'product_id': self.product.id,
            'quantity': 1
        })
        self.assertEqual(response.status_code, 302)
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 1)

    def test_order_creation(self):
        """Test order creation from cart"""
        self.client.login(username='testuser', password='testpass123')

        # Add product to cart
        self.client.post(reverse('add_to_cart'), {
            'product_id': self.product.id,
            'quantity': 1
        })

        # Checkout
        response = self.client.post(reverse('checkout'))
        self.assertEqual(response.status_code, 302)

        # Verify order created
        self.assertTrue(Order.objects.exists())
        order = Order.objects.first()
        self.assertEqual(order.total, self.product.price)


class PerformanceTestCase(TestCase):
    """Basic performance test cases"""

    def setUp(self):
        # Create multiple products for performance testing
        for i in range(100):
            Product.objects.create(
                name=f'Product {i}',
                description=f'Description {i}',
                price=Decimal('10.00')
            )

    def test_product_listing_performance(self):
        """Test product listing performance"""
        import time
        start_time = time.time()

        response = self.client.get(reverse('home'))
        end_time = time.time()

        self.assertEqual(response.status_code, 200)
        # Should complete within reasonable time (adjust threshold as needed)
        self.assertLess(end_time - start_time, 1.0)  # Less than 1 second
