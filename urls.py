from django.urls import path
from . import views

urlpatterns = [
    # Public views
    path('', views.home, name='home'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # User views
    path('profile/', views.profile, name='profile'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/update/', views.update_cart, name='update_cart'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/success/', views.checkout_success, name='checkout_success'),

    # Staff views
    path('staff/products/', views.manage_products, name='manage_products'),
    path('staff/products/add/', views.add_product, name='add_product'),
    path('staff/products/<int:pk>/edit/', views.edit_product, name='edit_product'),
    path('staff/products/<int:pk>/delete/', views.delete_product, name='delete_product'),
    path('staff/orders/', views.manage_orders, name='manage_orders'),
]
