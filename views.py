from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from .forms import RegistrationForm, LoginForm
from .models import UserProfile
import logging

logger = logging.getLogger(__name__)


def register(request):
    """User registration view."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.get_or_create(user=user)
            logger.info(f"New user registered: {user.username}")
            messages.success(request, "Registration successful! Please log in.")
            return redirect('login')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """User login view with session rotation."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                request.session.cycle_key()  # Prevent session fixation
                logger.info(f"User logged in: {user.username}")
                messages.success(request, f"Welcome, {user.username}!")
                return redirect('home')
            else:
                logger.warning(f"Failed login attempt for username: {username}")
                messages.error(request, "Invalid credentials.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


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
    profile_obj, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        profile_obj.phone = request.POST.get('phone', '')
        profile_obj.address = request.POST.get('address', '')
        profile_obj.save()
        messages.success(request, "Profile updated.")
        return redirect('profile')

    return render(request, 'accounts/profile.html', {'profile': profile_obj})
