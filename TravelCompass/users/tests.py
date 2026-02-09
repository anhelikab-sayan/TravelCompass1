from django.test import TestCase

# Create your tests here.
from django.urls import reverse
from django.contrib.auth.models import User
from django.core import mail

from users.models import UserProfile


class UserRegistrationTests(TestCase):
    # Тесты регистрации пользователя

    def test_registration_creates_inactive_user(self):
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

        # Письмо отправлено (но не реально)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Подтверждение', mail.outbox[0].subject)


class EmailConfirmationTests(TestCase):
    # Тесты подтверждения email

    def test_email_confirmation_activates_user(self):

        # Проверяем, что:
        # переход по ссылке подтверждает email
        # пользователь становится активным

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

class UserPagesTests(TestCase):

    # Проверка доступности страниц и авторизации


    def test_register_page_opens(self):

        # Проверка, что страница регистрации открывается

        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_login_page_opens(self):

        # Проверка, что страница входа открывается

        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_profile_requires_login(self):

        # Проверка, что без авторизации профиль недоступен

        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)  # редирект на логин

    def test_profile_after_login(self):

        # Проверка доступа к профилю после входа

        user = User.objects.create_user(
            username='testuser',
            password='123456',
            is_active=True
        )

        self.client.login(username='testuser', password='123456')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
    
    def test_logout(self):

        # Проверка выхода пользователя из системы

        user = User.objects.create_user(
            username='logoutuser',
            password='123456',
            is_active=True
        )

        # Логинимся
        self.client.login(username='logoutuser', password='123456')

        # Выходим
        response = self.client.get(reverse('logout'))

        # После выхода должен редирект 
        self.assertEqual(response.status_code, 302)

        # Проверяем, что профиль снова недоступен
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)

class UserAuthNegativeTests(TestCase):
    # Негативные тесты авторизации и регистрации
    def test_login_with_wrong_username(self):

    # Проверка входа с несуществующим логином
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
    
    def test_login_with_wrong_password(self):
        # Проверка входа с неправильным паролем

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
    
    def test_registration_with_existing_email(self):
        # Проверка регистрации с email, который уже существует в системе

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

    def test_registration_shows_all_errors(self):

        # Проверка, что при неверной регистрации выводятся все ошибки, а не только первая


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

