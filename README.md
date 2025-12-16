# MyShop E-Commerce Application

A secure Django e-commerce web application with user authentication, role-based access control, shopping cart functionality, and comprehensive security hardening.

## Project Overview

**Purpose:** Demonstrate a production-ready secure web application with modern security practices integrated throughout the development lifecycle.

**Key Security Focus:**
- User authentication and session management with CSRF protection
- Role-based access control (Customer vs. Staff/Admin)
- Input validation and output encoding to prevent XSS and SQL injection
- Secure configuration with environment-based secrets management
- Audit logging for tracking business-critical events
- Security headers and middleware for modern web security

## Features

### Core Functionality
- **User Management**: Registration, login, logout, and profile management
- **Product Catalog**: Browse and display products with images
- **Shopping Cart**: Add/update/remove items; persist cart across sessions and logins
- **Checkout**: Create orders from cart items
- **Admin Dashboard**: Staff-only access to manage products and view orders

### Security Features
1. **Authentication & Authorization**
   - User registration with email validation and strong password enforcement
   - Secure login with session rotation to prevent session fixation
   - Role-based access control (RBAC) using Django Groups: Customer, Staff, Admin
   - Custom permission decorators for fine-grained access control
   - Customer profile model to track customer data securely

2. **Session & CSRF Protection**
   - `SESSION_COOKIE_HTTPONLY=True` prevents JavaScript access to session cookies
   - `CSRF_COOKIE_HTTPONLY=False` (configurable for client-side CSRF token retrieval)
   - Session key rotation on login
   - All forms include CSRF token validation via Django middleware

3. **Input Validation & Output Encoding**
   - Django Forms with built-in validators (price > 0, email format, etc.)
   - Server-side quantity validation (must be positive integer)
   - Template auto-escaping to prevent XSS
   - SQL injection prevention via Django ORM parameterized queries

4. **Error Handling & Logging**
   - Structured logging to file and console
   - Audit logs for sensitive actions (login, order placement, product changes)
   - Safe error pages in production (DEBUG=False) to avoid information disclosure
   - Exception logging without exposing stack traces to users

5. **Security Headers & Middleware**
   - `SECURE_BROWSER_XSS_FILTER=True`
   - `SECURE_CONTENT_TYPE_NOSNIFF=True`
   - `X_FRAME_OPTIONS='DENY'` (prevents clickjacking)
   - Django SecurityMiddleware included

## Project Structure

```
myshop_app/
├── myshop/                          # Django project settings
│   ├── settings.py                  # Configuration with security hardening
│   ├── urls.py                      # Project-level URL routing
│   ├── wsgi.py                      # WSGI application
│   └── asgi.py                      # ASGI application
├── store/                           # Main Django app
│   ├── models.py                    # Product, Cart, Order, User models
│   ├── views.py                     # All application views
│   ├── urls.py                      # App-level URL routing
│   ├── forms.py                     # Forms with validation
│   ├── admin.py                     # Django admin configuration
│   ├── tests.py                     # Unit & security tests
│   ├── migrations/                  # Database migrations
│   └── templates/store/             # HTML templates
│       ├── home.html                # Product listing
│       ├── register.html            # User registration
│       ├── login.html               # User login
│       ├── profile.html             # User profile
│       ├── cart.html                # Shopping cart
│       ├── checkout.html            # Checkout page
│       ├── manage_products.html     # Staff product management
│       ├── add_product.html         # Staff add product
│       ├── edit_product.html        # Staff edit product
│       └── delete_product.html      # Staff delete product
├── logs/                            # Application logs (created on first run)
├── requirements.txt                 # Python dependencies
├── db.sqlite3                       # SQLite database (development only)
├── manage.py                        # Django management script
├── pytest.ini                       # Pytest configuration
├── SECURITY.md                      # Security documentation (DFD, threat modeling)
└── .gitignore                       # Git ignore rules
```

## Setup & Installation

### Prerequisites
- Python 3.8+
- pip package manager
- Virtual environment (recommended)

### Steps

1. **Clone and navigate to project:**
   ```bash
   cd myshop_app
   ```

2. **Create and activate virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Create logs directory:**
   ```powershell
   mkdir logs
   ```

5. **Run migrations:**
   ```powershell
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create a superuser (admin account):**
   ```powershell
   python manage.py createsuperuser
   # Enter username, email, password
   ```

7. **Start development server:**
   ```powershell
   python manage.py runserver
   ```

8. **Access the application:**
   - Homepage: http://localhost:8000/
   - Admin panel: http://localhost:8000/admin/

## Usage

### For Customers
1. **Register:** Click "Register" and create an account with email and password (password must be 8+ chars with uppercase/numbers)
2. **Browse Products:** View available products on the homepage
3. **Add to Cart:** Click "Add to cart" on any product, adjust quantity
4. **Checkout:** Review cart, proceed to checkout, place order
5. **Profile:** Update contact information in your profile

### For Staff/Admin
1. **Login:** Use a staff account (created via Django admin)
2. **Manage Products:** Navigate to `/staff/products/` to view, add, edit, or delete products
3. **View Orders:** Navigate to `/staff/orders/` to see all placed orders
4. **Admin Panel:** Access `/admin/` for full Django admin

## Security Improvements Implemented

| Requirement ID | Requirement | Status | Implementation |
|---|---|---|---|
| SR-1 | User Authentication with Strong Passwords | Completed | Django UserCreationForm, password validators, PBKDF2 hashing |
| SR-2 | Session Management & Fixation Prevention | Completed | `session_key.cycle_key()` on login, `SESSION_COOKIE_HTTPONLY=True` |
| SR-3 | CSRF Protection | Completed | Django CSRF middleware, `{% csrf_token %}` in all forms |
| SR-4 | Input Validation & Output Encoding | Completed | Django Forms validators, template auto-escaping |
| SR-5 | Authorization & Role-Based Access Control | Completed | `@user_passes_test(is_staff)` decorators, Customer/Staff roles |
| SR-6 | Secure Configuration | Completed | Environment-based settings, security headers, disabled DEBUG in production |
| SR-7 | Logging & Auditing | Completed | Structured logging to `logs/app.log`, audit trail for key events |
| SR-8 | Error Handling | Completed | Safe error pages, no stack trace disclosure to users |

## SQL Injection & XSS Attack Demonstrations

To demonstrate security vulnerabilities and their prevention, here are examples of how SQL Injection and XSS attacks could occur and how this application prevents them.

### SQL Injection Prevention

**Vulnerable Code Example (DO NOT USE):**
```python
# This would be vulnerable to SQL injection
def vulnerable_search(query):
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM products WHERE name LIKE '%{query}%'")  # UNSAFE!
    return cursor.fetchall()
```

**Secure Implementation (Used in this app):**
```python
# From store/views.py - home view
def home(request):
    query = request.GET.get('q', '')
    if query:
        # Secure search using Django ORM to prevent SQL injection
        products = Product.objects.filter(
            models.Q(name__icontains=query) | models.Q(description__icontains=query)
        )
    else:
        products = Product.objects.all()
    return render(request, 'store/home.html', {'products': products, 'query': query})
```

**Attack Demonstration:**
- Malicious input: `' OR '1'='1` in search field
- Vulnerable code would return all products
- Secure code safely filters using parameterized queries

### XSS (Cross-Site Scripting) Prevention

**Vulnerable Template Example (DO NOT USE):**
```html
<!-- This would be vulnerable to XSS -->
<div>Product: {{ product.name|safe }}</div>  <!-- UNSAFE! -->
```

**Secure Implementation (Used in this app):**
```html
<!-- From store/templates/store/home.html -->
<div class="card-title">{{ product.name }}</div>  <!-- SAFE: Auto-escaped -->
```

**Attack Demonstration:**
- Malicious input: `<script>alert('XSS')</script>` in product name
- Vulnerable template would execute JavaScript
- Secure template auto-escapes HTML characters

**Form Validation Against XSS:**
```python
# From store/forms.py - ProductForm
def clean_name(self):
    """Validate name is not empty and properly formatted."""
    name = self.cleaned_data.get('name', '').strip()
    if not name:
        raise ValidationError("Product name cannot be empty.")
    if len(name) > 100:
        raise ValidationError("Product name is too long.")
    # Check for potentially harmful characters
    if '<' in name or '>' in name or '&' in name:
        raise ValidationError("Product name contains invalid characters.")
    return name
```

### Testing Vulnerabilities

Run the included tests to verify security measures:
```bash
pytest store/tests.py -v
```

Key security tests include:
- Input validation for malicious payloads
- SQL injection attempt prevention
- XSS payload sanitization

## Testing

### Run All Tests
```powershell
pytest
```

### Run Specific Test Class
```powershell
pytest store/tests.py::AuthenticationTests -v
```

### Run with Coverage
```powershell
pip install pytest-cov
pytest --cov=store store/tests.py
```

### Security Tests Included
- **Authentication:** Registration, login, invalid credentials, email uniqueness
- **Authorization:** Staff-only access, role enforcement
- **Cart & Checkout:** Session carts, user carts, cart merging, order creation
- **Input Validation:** Price validation, quantity validation, XSS prevention
- **CSRF:** Token requirement on forms

### Static Analysis (SAST)

**Run Bandit (security linter):**
```powershell
bandit -r .
```

**Run pip-audit (dependency vulnerability scanner):**
```powershell
pip-audit
```

## Deployment Considerations

### Production Checklist
- [ ] Set `DEBUG=False` and provide `DJANGO_SECRET_KEY` environment variable
- [ ] Set `DJANGO_ALLOWED_HOSTS` to your production domain
- [ ] Use HTTPS and set `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`
- [ ] Configure production database (PostgreSQL recommended)
- [ ] Use a production WSGI server (Gunicorn, uWSGI)
- [ ] Set up log rotation and monitoring
- [ ] Run security audit: `bandit -r . && pip-audit`
- [ ] Use environment variables for sensitive data

### Environment Variables
```
DJANGO_SECRET_KEY=<strong-random-key>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DJANGO_LOG_LEVEL=WARNING
```

## Development Notes

### Session Cart → User Cart Flow
When a user logs in after adding items to their session cart:
1. Session cart is fetched using `session_key`
2. `CustomerProfile.merge_session_cart_to_user()` is called
3. Items are moved to the user's persistent cart
4. Session cart is deleted to avoid orphan records

### Password Security
- Django's PBKDF2 hasher uses 260,000 iterations (OWASP recommended minimum: 100,000)
- Passwords are never logged or displayed in plaintext
- Password validators enforce complexity (8+ chars, uppercase, numbers)

### Logging
- **Log file location:** `logs/app.log`
- **Key logged events:**
  - User registration
  - Login/logout with username (not password)
  - Product management actions
  - Order creation
  - Authentication failures

## Contributing

1. Create a feature branch: `git checkout -b feature/feature-name`
2. Commit changes: `git commit -am 'Add feature'`
3. Push to branch: `git push origin feature/feature-name`
4. Submit a pull request

## Security Reporting

If you discover a security vulnerability, please email security@myshop.local. Do not publicly disclose the issue.

## References

- Django Security Documentation: https://docs.djangoproject.com/en/stable/topics/security/
- OWASP Top 10: https://owasp.org/Top10/
- CWE/SANS Top 25: https://cwe.mitre.org/top25/
- Django Password Hashing: https://docs.djangoproject.com/en/stable/topics/auth/passwords/