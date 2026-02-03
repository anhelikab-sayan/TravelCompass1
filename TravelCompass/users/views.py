# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages

from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from users.models import UserProfile
from core.models import Route

# Для email
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.conf import settings

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')

        errors = []

        # Проверка обязательных полей
        if not all([username, email, password, password2]):
            errors.append('Заполните все поля')

        # Проверка совпадения паролей
        elif password != password2:
            errors.append('Пароли не совпадают')

        # Проверка длины пароля
        elif len(password) < 6:
            errors.append('Пароль должен содержать минимум 6 символов')

        # Проверка формата email через Django
        else:
            try:
                validate_email(email)
            except ValidationError:
                errors.append('Введите корректный email')

        # Проверка уникальности username
        if not errors and User.objects.filter(username=username).exists():
            errors.append('Пользователь с таким логином уже существует')

        # Проверка уникальности email
        if not errors and User.objects.filter(email=email).exists():
            errors.append('Пользователь с таким email уже существует')

        if errors:
            return render(request, 'users/register.html', {
                'error': errors[0],
                'username': username,
                'email': email,
            })

        # Создание флажка для пользователя, который показывает, что он неактивен 
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_active=False
        )

        # Генерация токена
        token = get_random_string(32)
        UserProfile.objects.create(
            user=user,
            email_token=token
        )

        # Ссылка подтверждения
        confirm_link = request.build_absolute_uri(
            reverse('confirm_email', args=[token])
        )

        # Отправка письма
        send_mail(
            'Подтверждение регистрации TravelCompass',
            f'Для подтверждения регистрации перейдите по ссылке:\n{confirm_link}',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False
        )

        return render(request, 'users/register.html', {
            'success': 'Письмо отправлено. Проверьте почту для подтверждения.'
        })

    return render(request, 'users/register.html')

def confirm_email_view(request, token):
    try:
        profile = UserProfile.objects.get(email_token=token)
        user = profile.user
        user.is_active = True
        user.save()
        profile.delete()

        messages.success(request, 'Email подтверждён. Теперь можно войти.')
        return redirect('login')

    except UserProfile.DoesNotExist:
        return render(request, 'users/confirm_failed.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            return render(request, 'users/login.html', {
                'error': 'Введите логин и пароль',
                'username': username,
            })

        user = authenticate(request, username=username, password=password)
        if user:
            if not user.is_active:
                return render(request, 'users/login.html', {
                    'error': 'Подтвердите email перед входом'
            })
            login(request, user)
            messages.success(request, f'Добро пожаловать, {username}!')
            return redirect('profile')

        return render(request, 'users/login.html', {
            'error': 'Неверный логин или пароль',
            'username': username,
        })

    return render(request, 'users/login.html')

@login_required
def profile_view(request):
    routes = Route.objects.filter(user=request.user)
    return render(request, 'users/profile.html', {
        'routes': routes
    })

def logout_view(request):
    logout(request)
    messages.info(request, 'Вы успешно вышли из системы')
    return redirect('login')