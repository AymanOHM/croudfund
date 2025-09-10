from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
import secrets
from .models import User
from .forms import UserRegistrationForm, UserLoginForm, UserUpdateForm, PasswordResetForm, PasswordResetConfirmForm

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.activation_token = secrets.token_urlsafe(32)
            user.activation_token_expires = timezone.now() + timezone.timedelta(hours=24)
            user.save()
            
            subject = 'Activate Your Account'
            message = render_to_string('accounts/activation_email.html', {
                'user': user,
                'domain': request.get_host(),
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': user.activation_token,
            })
            
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
            
            messages.success(request, 'Registration successful. Please check your email to activate your account.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and user.activation_token == token and user.activation_token_expires > timezone.now():
        user.is_active = True
        user.activation_token = None
        user.activation_token_expires = None
        user.save()
        messages.success(request, 'Account activated successfully. You can now login.')
        return redirect('login')
    else:
        messages.error(request, 'Activation link is invalid or has expired.')
        return redirect('login')

def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return redirect('home')
                else:
                    messages.error(request, 'Your account is not activated. Please check your email.')
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = UserLoginForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required
def profile(request):
    return render(request, 'accounts/profile.html')

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = UserUpdateForm(instance=request.user)
    return render(request, 'accounts/edit_profile.html', {'form': form})

@login_required
def delete_account(request):
    if request.method == 'POST':
        request.user.delete()
        messages.success(request, 'Your account has been deleted successfully.')
        return redirect('home')
    return render(request, 'accounts/delete_account.html')

def password_reset(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                token = secrets.token_urlsafe(32)
                user.activation_token = token
                user.activation_token_expires = timezone.now() + timezone.timedelta(hours=1)
                user.save()
                
                subject = 'Password Reset Request'
                message = render_to_string('accounts/password_reset_email.html', {
                    'user': user,
                    'domain': request.get_host(),
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': token,
                })
                
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
                messages.success(request, 'Password reset link has been sent to your email.')
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, 'No account found with this email address.')
    else:
        form = PasswordResetForm()
    return render(request, 'accounts/password_reset.html', {'form': form})

def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is None or user.activation_token != token or user.activation_token_expires < timezone.now():
        messages.error(request, 'Password reset link is invalid or has expired.')
        return redirect('login')
    
    if request.method == 'POST':
        form = PasswordResetConfirmForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password1']
            user.set_password(password)
            user.activation_token = None
            user.activation_token_expires = None
            user.save()
            messages.success(request, 'Password reset successfully. You can now login with your new password.')
            return redirect('login')
    else:
        form = PasswordResetConfirmForm()
    
    return render(request, 'accounts/password_reset_confirm.html', {'form': form})