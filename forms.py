from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import Product, Order, CustomerProfile


class RegistrationForm(UserCreationForm):
    """User registration form with email and profile fields."""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def clean_email(self):
        """Validate email is unique."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already registered.")
        return email

    def save(self, commit=True):
        """Save user and create default cart and profile."""
        user = super().save(commit)
        if commit:
            # Create customer profile
            CustomerProfile.objects.get_or_create(user=user)
            # Create user cart (session cart will merge on login)
        return user


class LoginForm(forms.Form):
    """Simple login form."""
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)


class ProductForm(forms.ModelForm):
    """Form for creating/editing products (staff only)."""
    class Meta:
        model = Product
        fields = ('name', 'description', 'price', 'image')

    def clean_price(self):
        """Validate price is positive and within reasonable bounds."""
        price = self.cleaned_data.get('price')
        if price is None:
            raise ValidationError("Price is required.")
        if price <= 0:
            raise ValidationError("Price must be greater than zero.")
        if price > 999999.99:
            raise ValidationError("Price is too high.")
        return price

    def clean_name(self):
        """Validate name is not empty and properly formatted."""
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise ValidationError("Product name cannot be empty.")
        if len(name) > 100:
            raise ValidationError("Product name is too long.")
        return name

    def clean_description(self):
        """Validate description."""
        description = self.cleaned_data.get('description', '').strip()
        if len(description) > 1000:
            raise ValidationError("Description is too long.")
        # Check for potentially harmful characters
        if '<script' in description.lower():
            raise ValidationError("Description contains potentially harmful content.")
        return description

    def clean_image(self):
        """Validate image file."""
        image = self.cleaned_data.get('image')
        if image:
            # Check file size (max 5MB)
            if image.size > 5 * 1024 * 1024:
                raise ValidationError("Image file is too large (max 5MB).")
            # Check file type
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if hasattr(image, 'content_type') and image.content_type not in allowed_types:
                raise ValidationError("Invalid image format. Allowed: JPEG, PNG, GIF, WebP.")
        return image


class OrderFilterForm(forms.Form):
    """Form for filtering orders by status."""
    STATUS_CHOICES = (
        ('', 'All'),
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('cancelled', 'Cancelled'),
    )
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False)
