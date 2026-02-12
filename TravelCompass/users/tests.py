from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.core import mail
from users.models import UserProfile
import sys


class UserRegistrationTests(TestCase):
    """Тесты регистрации пользователя"""
    
    def setUp(self):
        print("\n" + "=" * 70)
        print("🔵 ТЕСТЫ РЕГИСТРАЦИИ ПОЛЬЗОВАТЕЛЯ")
        print("=" * 70)

    def test_registration_creates_inactive_user(self):
        """Тест: Регистрация создает неактивного пользователя с токеном"""
        response = self.client.post(
            reverse('register'),
            {
                'username': 'testuser',
                'email': 'test@example.com',
                'password': '12345678',
                'password2': '12345678',
            }
        )

        # Пользователь создан
        user = User.objects.get(username='testuser')
        self.assertFalse(user.is_active)
        
        # Создан профиль с токеном
        profile = UserProfile.objects.get(user=user)
        self.assertTrue(profile.email_token)
        
        # Письмо отправлено
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Подтверждение', mail.outbox[0].subject)
        
        print(f"  ✅ Регистрация: пользователь '{user.username}' создан (неактивен), токен получен, письмо отправлено")


class EmailConfirmationTests(TestCase):
    """Тесты подтверждения email"""
    
    def setUp(self):
        print("\n" + "=" * 70)
        print("📧 ТЕСТЫ ПОДТВЕРЖДЕНИЯ EMAIL")
        print("=" * 70)

    def test_email_confirmation_activates_user(self):
        """Тест: Подтверждение email активирует пользователя"""
        
        user = User.objects.create_user(
            username='confirmuser',
            email='confirm@example.com',
            password='12345678',
            is_active=False
        )

        profile = UserProfile.objects.create(
            user=user,
            email_token='testtoken123'
        )

        response = self.client.get(
            reverse('confirm_email', args=['testtoken123'])
        )

        user.refresh_from_db()
        self.assertTrue(user.is_active)

        # Профиль удалён после подтверждения
        self.assertFalse(
            UserProfile.objects.filter(user=user).exists()
        )
        
        print(f"  ✅ Подтверждение email: пользователь '{user.username}' активирован, профиль удален")


class UserPagesTests(TestCase):
    """Проверка доступности страниц и авторизации"""
    
    def setUp(self):
        print("\n" + "=" * 70)
        print("🌐 ТЕСТЫ ДОСТУПНОСТИ СТРАНИЦ")
        print("=" * 70)

    def test_register_page_opens(self):
        """Тест: Страница регистрации открывается"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        print(f"  ✅ Страница регистрации: 200 OK")

    def test_login_page_opens(self):
        """Тест: Страница входа открывается"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        print(f"  ✅ Страница входа: 200 OK")

    def test_profile_requires_login(self):
        """Тест: Профиль требует авторизации"""
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)  # редирект на логин
        print(f"  ✅ Профиль: редирект на логин (302)")

    def test_profile_after_login(self):
        """Тест: Доступ к профилю после входа"""
        user = User.objects.create_user(
            username='testuser',
            password='123456',
            is_active=True
        )

        self.client.login(username='testuser', password='123456')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        print(f"  ✅ Профиль после входа: 200 OK (пользователь '{user.username}')")
    
    def test_logout(self):
        """Тест: Выход пользователя из системы"""
        user = User.objects.create_user(
            username='logoutuser',
            password='123456',
            is_active=True
        )

        # Логинимся
        self.client.login(username='logoutuser', password='123456')
        
        # Проверяем что вошли
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)

        # Выходим
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)

        # Проверяем, что профиль снова недоступен
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)
        
        print(f"  ✅ Выход: пользователь '{user.username}' вышел, профиль недоступен")


class UserAuthNegativeTests(TestCase):
    """Негативные тесты авторизации и регистрации"""
    
    def setUp(self):
        print("\n" + "=" * 70)
        print("⚠️  НЕГАТИВНЫЕ ТЕСТЫ")
        print("=" * 70)

    def test_login_with_wrong_username(self):
        """Тест: Вход с несуществующим логином"""
        User.objects.create_user(
            username='realuser',
            password='12345678',
            is_active=True
        )

        response = self.client.post(
            reverse('login'),
            {
                'username': 'wronguser',
                'password': '12345678',
            }
        )

        self.assertContains(response, 'Неверный логин или пароль')
        print(f"  ✅ Вход: несуществующий логин - ошибка 'Неверный логин или пароль'")
    
    def test_login_with_wrong_password(self):
        """Тест: Вход с неправильным паролем"""
        User.objects.create_user(
            username='testuser',
            password='correctpass',
            is_active=True
        )

        response = self.client.post(
            reverse('login'),
            {
                'username': 'testuser',
                'password': 'wrongpass',
            }
        )

        self.assertContains(response, 'Неверный логин или пароль')
        print(f"  ✅ Вход: неправильный пароль - ошибка 'Неверный логин или пароль'")
    
    def test_registration_with_existing_email(self):
        """Тест: Регистрация с существующим email"""
        User.objects.create_user(
            username='user1',
            email='test@example.com',
            password='12345678'
        )

        response = self.client.post(
            reverse('register'),
            {
                'username': 'user2',
                'email': 'test@example.com',
                'password': '12345678',
                'password2': '12345678',
            }
        )

        self.assertContains(response, 'Пользователь с таким email уже существует')
        print(f"  ✅ Регистрация: существующий email - ошибка 'Пользователь с таким email уже существует'")

    def test_registration_shows_all_errors(self):
        """Тест: При неверной регистрации выводятся все ошибки"""
        
        response = self.client.post(
            reverse('register'),
            {
                'username': '',              # нет логина
                'email': 'bademail',          # неправильный email
                'password': '12',             # короткий пароль
                'password2': '42',            # не совпадает
            }
        )

        self.assertEqual(response.status_code, 200)

        # Проверяем, что несколько ошибок отображаются
        self.assertContains(response, 'Логин обязателен')
        self.assertContains(response, 'Введите корректный email')
        self.assertContains(response, 'Пароли не совпадают')
        self.assertContains(response, 'Пароль должен содержать минимум 6 символов')
        
        print(f"  ✅ Регистрация: все ошибки валидации отображаются")
        print(f"      - Логин обязателен")
        print(f"      - Введите корректный email")
        print(f"      - Пароли не совпадают")
        print(f"      - Пароль должен содержать минимум 6 символов")
