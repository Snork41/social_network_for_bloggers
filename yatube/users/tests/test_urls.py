from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class UsersURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='User_one')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_access_for_anonymous(self):
        """Доступ страниц для анонимного пользователя"""
        url = {
            '/auth/signup/': HTTPStatus.OK,
            '/auth/login/': HTTPStatus.OK,
        }
        for url_name, expected_code in url.items():
            with self.subTest(url_name=url_name):
                self.assertEqual(
                    self.client.get(url_name).status_code, expected_code
                )

    def test_urls_access_for_authorized_client(self):
        """Доступ страниц для авторизованного пользователя"""
        url = {
            '/auth/signup/': HTTPStatus.OK,
            '/auth/logout/': HTTPStatus.OK,
            '/auth/login/': HTTPStatus.OK,
            '/auth/password_reset/': HTTPStatus.OK,
            '/auth/password_reset/done/': HTTPStatus.OK,
            '/auth/reset/<uidb64>/<token>/': HTTPStatus.OK,
            '/auth/reset/done/': HTTPStatus.OK,
            '/auth/password_change/': HTTPStatus.FOUND,
            '/auth/password_change/done/': HTTPStatus.FOUND,
        }
        for url_name, expected_code in url.items():
            with self.subTest(url_name=url_name):
                self.assertEqual(
                    self.authorized_client.get(url_name).status_code,
                    expected_code)

    def test_url_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'users/password_change_form.html':
                '/auth/password_change/',
            'users/password_change_done.html':
                '/auth/password_change/done/',
            'users/signup.html':
                '/auth/signup/',
            'users/logged_out.html':
                '/auth/logout/',
            'users/login.html':
                '/auth/login/',
            'users/password_reset_form.html':
                '/auth/password_reset/',
            'users/password_reset_done.html':
                '/auth/password_reset/done/',
            'users/password_reset_confirm.html':
                '/auth/reset/<uidb64>/<token>/',
            'users/password_reset_complete.html':
                '/auth/reset/done/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
