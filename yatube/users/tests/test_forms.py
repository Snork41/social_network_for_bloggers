from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class UserCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='User')

    def test_create_new_user(self):
        """Валидная форма создает запись."""
        users_count = User.objects.count()
        form_data = {
            'first_name': 'New',
            'last_name': 'User2',
            'username': 'New_User',
            'email': 'srgmjpsoirgj@gmail.com',
            'password1': 'rgwrghwr34125',
            'password2': 'rgwrghwr34125',
        }
        self.client.post(reverse('users:signup'), data=form_data)
        self.assertEqual(User.objects.count(), users_count + 1)
