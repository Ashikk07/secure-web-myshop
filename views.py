from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db import models
from .models import Product, Cart, CartItem, Order, OrderItem, CustomerProfile, Category
from .forms import RegistrationForm, LoginForm, ProductForm
from decimal import Decimal
import logging
from functools import wraps
from django.core.exceptions import PermissionDenied

logger = logging.getLogger(__name__)

def has_role(role_name):
    """Decorator to check if user has a specific role (group name)."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            if not request.user.groups.filter(name=role_name).exists():
                raise PermissionDenied("You don't have permission to access this page.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def is_staff(user):
    """Check if user is staff/admin."""
    return user.is_staff


def register(request):
    """User registration view."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            logger.info(f"New user registered: {user.username}")
            messages.success(request, "Registration successful! Please log in.")
            return redirect('login')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = RegistrationForm()

    return render(request, 'store/register.html', {'form': form})


def login_view(request):
    """User login view with session rotation and cart merge."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                # Save old session key for cart merge
                old_session_key = request.session.session_key
                login(request, user)
                # Rotate session key after login to prevent session fixation
                request.session.cycle_key()

                # Merge session cart into user cart
                if old_session_key:
                    CustomerProfile.merge_session_cart_to_user(user, old_session_key)

                logger.info(f"User logged in: {user.username}")
                messages.success(request, f"Welcome, {user.username}!")
                return redirect('home')
            else:
                logger.warning(f"Failed login attempt for username: {username}")
                messages.error(request, "Invalid credentials.")
    else:
        form = LoginForm()

    return render(request, 'store/login.html', {'form': form})


def logout_view(request):
    """User logout view."""
    username = request.user.username if request.user.is_authenticated else "anonymous"
    logout(request)
    logger.info(f"User logged out: {username}")
    messages.success(request, "You have been logged out.")
    return redirect('home')


@login_required(login_url='login')
def profile(request):
    """User profile view."""
    profile_obj, created = CustomerProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        profile_obj.phone = request.POST.get('phone', '')
        profile_obj.address = request.POST.get('address', '')
        profile_obj.save()
        messages.success(request, "Profile updated.")
        return redirect('profile')

    return render(request, 'store/profile.html', {'profile': profile_obj})


@require_POST
def update_cart(request):
    """Update cart item quantity with validation."""
    product_id = request.POST.get('product_id')
    try:
        quantity = int(request.POST.get('quantity', 0) or 0)
    except (ValueError, TypeError):
        messages.error(request, "Invalid quantity.")
        return redirect('cart')

    cart = get_user_cart(request)
    item = CartItem.objects.filter(cart=cart, product_id=product_id).first()
    if item:
        if quantity <= 0:
            item.delete()
            messages.success(request, "Item removed from cart.")
        else:
            item.quantity = quantity
            item.save()
            messages.success(request, "Cart updated.")
    return redirect('cart')


@require_POST
def remove_from_cart(request):
    """Remove item from cart."""
    product_id = request.POST.get('product_id')
    cart = get_user_cart(request)
    if cart:
        CartItem.objects.filter(cart=cart, product_id=product_id).delete()
        messages.success(request, "Item removed.")
    return redirect('cart')


def checkout(request):
    """Checkout view: create Order from cart and clear it."""
    cart = get_user_cart(request)
    if not cart or not cart.items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('cart')

    if request.method == 'POST':
        # Validate input
        try:
            order = Order.objects.create(total=cart.total)
            for item in cart.items.select_related('product').all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.product.price,
                    quantity=item.quantity,
                )
            # Clear cart
            cart.clear()
            logger.info(f"Order created: {order.id} by {request.user or 'anonymous'}")
            messages.success(request, f"Order #{order.id} placed successfully!")
            return redirect('checkout_success')
        except Exception as e:
            logger.error(f"Checkout error: {e}")
            messages.error(request, "An error occurred during checkout.")
            return redirect('cart')

    items = []
    total = Decimal('0.00')
    for item in cart.items.select_related('product').all():
        subtotal = item.product.price * item.quantity
        items.append({'item': item, 'subtotal': subtotal})
        total += subtotal

    return render(request, 'store/checkout.html', {'items': items, 'total': total})


def checkout_success(request):
    """Order confirmation page."""
    return render(request, 'store/checkout_success.html')


@login_required(login_url='login')
def manage_products(request):
    """Staff-only view for managing products."""
    products = Product.objects.all()
    return render(request, 'store/manage_products.html', {'products': products})


@login_required(login_url='login')
def add_product(request):
    """Staff-only view for adding products."""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            logger.info(f"Product created: {product.name} by {request.user.username}")
            messages.success(request, "Product added successfully.")
            return redirect('manage_products')
        # If form is invalid, fall through and render it with errors
    else:
        form = ProductForm()

    return render(request, 'store/add_product.html', {'form': form})


# Require staff for product management views
manage_products = user_passes_test(is_staff, login_url='home')(manage_products)
add_product = user_passes_test(is_staff, login_url='home')(add_product)


@login_required(login_url='login')
def edit_product(request, pk):
    """Staff-only view for editing products."""
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            logger.info(f"Product updated: {product.name} by {request.user.username}")
            messages.success(request, "Product updated successfully.")
            return redirect('manage_products')
    else:
        form = ProductForm(instance=product)
    return render(request, 'store/edit_product.html', {'form': form, 'product': product})


@login_required(login_url='login')
def delete_product(request, pk):
    """Staff-only view for deleting products."""
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        logger.info(f"Product deleted: {product_name} by {request.user.username}")
        messages.success(request, "Product deleted successfully.")
        return redirect('manage_products')
    return render(request, 'store/delete_product.html', {'product': product})


delete_product = user_passes_test(is_staff, login_url='home')(delete_product)


@login_required(login_url='login')
def manage_orders(request):
    """Staff-only view for viewing all orders."""
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'store/manage_orders.html', {'orders': orders})


manage_orders = user_passes_test(is_staff, login_url='home')(manage_orders)


def home(request):
    query = request.GET.get('q', '')
    category_slug = request.GET.get('category', '')
    products = Product.objects.all()
    if query:
        # Safe search using ORM to avoid SQL injection
        from django.db.models import Q
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category_slug:
        products = products.filter(category__slug=category_slug)
    categories = Category.objects.all()
    return render(request, 'store/home.html', {'products': products, 'query': query, 'categories': categories, 'selected_category': category_slug})


def product_detail(request, pk):
    """View for displaying detailed information about a specific product."""
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'store/product_detail.html', {'product': product})


@require_POST
def add_to_cart(request):
    """Add a product to the cart with input validation."""
    product_id = request.POST.get('product_id')
    try:
        quantity = int(request.POST.get('quantity', 1) or 1)
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
    except (ValueError, TypeError):
        messages.error(request, "Invalid quantity.")
        return redirect(request.POST.get('next') or 'cart')

    product = get_object_or_404(Product, pk=product_id)
    cart = get_user_cart(request)

    item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': quantity})
    if not created:
        item.quantity += quantity
        item.save()

    logger.info(f"Product added to cart: {product.name} (qty: {quantity})")
    messages.success(request, f"{product.name} added to cart.")
    return redirect(request.POST.get('next') or 'home')


def get_user_cart(request):
    """Get cart for authenticated user or session."""
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
    return cart


def cart_view(request):
    """Show current cart and items."""
    cart = get_user_cart(request)
    qs_items = cart.items.select_related('product') if cart else []

    # Build a list of items with subtotal (pre-calculated for template rendering)
    items = []
    total = Decimal('0.00')
    for it in qs_items:
        subtotal = (it.product.price or Decimal('0.00')) * it.quantity
        items.append({
            'item': it,
            'subtotal': subtotal,
        })
        total += subtotal

    return render(request, 'store/cart.html', {'cart': cart, 'items': items, 'total': total})
