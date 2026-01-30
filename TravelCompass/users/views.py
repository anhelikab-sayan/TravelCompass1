# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages

from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from core.models import Route


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

        # Создание пользователя
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        login(request, user)
        messages.success(request, f'Добро пожаловать, {username}!')
        return redirect('profile')

    return render(request, 'users/register.html')

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
            login(request, user)
            messages.success(request, f'Добро пожаловать, {username}!')
            return redirect('profile')

        return render(request, 'users/login.html', {
            'error': 'Неверный логин или пароль',
            'username': username,
        })

    return render(request, 'users/login.html')