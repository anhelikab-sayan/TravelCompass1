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



