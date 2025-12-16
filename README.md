# MyShop - Secure E-commerce Application

## Overview
A Django-based e-commerce application that demonstrates comprehensive web security implementations. This project was developed as part of a Secure Web Development course to showcase vulnerability identification, threat modeling, and security hardening techniques.

## Security Features Implemented

### 🔒 SQL Injection Prevention
- Replaced vulnerable raw SQL queries with Django ORM
- Implemented parameterized queries using Q objects
- All database operations now use safe ORM methods

### 🛡️ XSS Protection
- Removed unsafe template filters (`|safe`)
- Implemented proper output escaping
- All user-generated content is automatically sanitized

### 🔐 Authentication & Authorization
- Secure password hashing using PBKDF2
- Role-based access control (staff vs regular users)
- Session management with rotation to prevent fixation

### 🛡️ CSRF Protection
- Django's CSRF middleware enabled
- All forms include `{% csrf_token %}` protection
- State-changing operations require valid tokens

## Technology Stack
- **Framework:** Django 4.x
- **Database:** SQLite (development)
- **Frontend:** HTML5, CSS3, JavaScript
- **Authentication:** Django Auth System
- **Security:** Django Security Middleware

## Project Structure
```
myshop_app/
├── store/
│   ├── models.py          # Data models (Product, Cart, Order, etc.)
│   ├── views.py           # Business logic and security implementations
│   ├── forms.py           # Input validation forms
│   ├── templates/store/   # HTML templates with security
│   ├── urls.py           # URL routing
│   └── management/commands/  # Custom management commands
├── manage.py
├── requirements.txt
└── README.md
```

## Setup Instructions

### Prerequisites
- Python 3.8+
- pip package manager

### Installation
1. **Clone the repository**
   ```bash
   git clone [your-github-repo-url]
   cd myshop_app
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser account**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - Open http://127.0.0.1:8000 in your browser
   - Admin panel: http://127.0.0.1:8000/admin/

## Security Testing

### SQL Injection Testing
Test the search functionality with malicious payloads:
- Search for: `' OR '1'='1` (should return filtered results, not all products)
- Search for: `'; DROP TABLE store_product;--` (should fail safely)

### XSS Testing
Test product display and search with script payloads:
- Search for: `<script>alert('XSS')</script>` (should display as text, not execute)
- Product names/descriptions with script tags (should be escaped)

### Authentication Testing
- Attempt to access admin pages without staff privileges
- Test session timeout and rotation
- Verify password reset functionality

## Key Security Improvements

### Before vs After

**SQL Injection Vulnerability (BEFORE):**
```python
# VULNERABLE - Raw SQL with string concatenation
cursor.execute("SELECT * FROM store_product WHERE 1=1")
```

**SQL Injection Prevention (AFTER):**
```python
# SECURE - Django ORM with safe queries
products = Product.objects.filter(
    Q(name__icontains=query) |
    Q(description__icontains=query)
)
```

**XSS Vulnerability (BEFORE):**
```html
<!-- VULNERABLE - Unsafe template filter -->
<h2>{{ product.name|safe }}</h2>
```

**XSS Protection (AFTER):**
```html
<!-- SECURE - Automatic escaping -->
<h2>{{ product.name }}</h2>
```

## Features

### User Features
- User registration and login
- Product browsing and search
- Shopping cart functionality
- Order placement and history
- User profile management

### Admin Features (Staff Only)
- Product management (CRUD operations)
- Order management and viewing
- User management
- Category management

## Security Considerations

### Threat Modeling
- SQL Injection: Prevented by ORM usage
- XSS: Prevented by template escaping
- CSRF: Prevented by token validation
- Authentication Bypass: Prevented by secure auth system
- Authorization Bypass: Prevented by role decorators

### Security Headers
The application includes security headers for:
- Content Security Policy (CSP)
- HTTP Strict Transport Security (HSTS)
- X-Frame-Options
- X-Content-Type-Options

## Testing Results

### Vulnerability Assessment
- SQL Injection: Mitigated
- XSS: Mitigated
- CSRF: Protected
- Authentication: Secure
- Authorization: Implemented

### Test Cases Executed
1. SQL Injection Test: Attempted injection via search - Result: Safe failure
2. XSS Test: Script injection attempts - Result: Content escaped
3. CSRF Test: Token validation - Result: Requests blocked without tokens
4. Auth Test: Unauthorized access attempts - Result: Access denied

## Contributing

This project demonstrates secure coding practices for educational purposes. For security research or vulnerability disclosure, please follow responsible disclosure guidelines.

## License

This project is developed for educational purposes as part of the Secure Web Development course at National College of Ireland.

## Contact

For questions about this project, please refer to the technical report submitted as part of the course assessment.
