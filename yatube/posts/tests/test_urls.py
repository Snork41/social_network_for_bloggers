from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='User')
        cls.user_author = User.objects.create_user(username='authorUser')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый пост',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.user_author)
        cache.clear()

    def test_urls_access_for_anonymous(self):
        """Доступ страниц для анонимного пользователя"""
        url = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user.username}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for url_name, expected_code in url.items():
            with self.subTest(url_name=url_name):
                self.assertEqual(
                    self.client.get(url_name).status_code, expected_code
                )

    def test_urls_access_for_authorized_client(self):
        """Доступ страниц для авторизованного пользователя"""
        url = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user.username}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/edit/': HTTPStatus.FOUND,
            f'/posts/{self.post.id}/comment/': HTTPStatus.FOUND,
            '/create/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for url_name, expected_code in url.items():
            with self.subTest(url_name=url_name):
                if expected_code == HTTPStatus.FOUND:
                    self.assertRedirects(
                        self.authorized_client.get(url_name, follow=True),
                        (f'/posts/{self.post.id}/')
                    )
                else:
                    self.assertEqual(
                        self.authorized_client.get(url_name).status_code,
                        expected_code)

    def test_urls_access_for_author_client(self):
        """Доступ страниц для пользователя-автора"""
        url = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user.username}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/edit/': HTTPStatus.OK,
            '/create/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for url_name, expected_code in url.items():
            with self.subTest(url_name=url_name):
                self.assertEqual(
                    self.author_client.get(url_name).status_code, expected_code
                )

    def test_create_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_edit_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /posts/<post_id>/edit/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.client.get(
            f'/posts/{self.post.id}/edit/',
            follow=True)
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/edit/'
        )

    def test_comment_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /posts/<post_id>/comment/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.client.get(
            f'/posts/{self.post.id}/comment/', follow=True)
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/comment/')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(template=template):
                if '/edit/' in address:
                    response = self.author_client.get(address)
                else:
                    response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
