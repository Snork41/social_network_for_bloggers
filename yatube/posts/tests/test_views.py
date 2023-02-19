import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from yatube.settings import (COUNT_POSTS, FIRST_OBJ, POSTS_ON_FIRST_PAGE,
                             POSTS_ON_SECOND_PAGE)
from ..models import Comment, Follow, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='User')
        cls.user_2 = User.objects.create_user(username='User_2')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.group_two = Group.objects.create(
            title='Тестовый заголовок_2',
            slug='test-slug_2',
            description='Тестовое описание_2'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост',
            image=cls.uploaded,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_2)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse(
                'posts:index'):
                    'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}):
                    'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.user.username}):
                    'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}):
                    'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}):
                    'posts/create_post.html',
            reverse(
                'posts:post_create'):
                    'posts/create_post.html',
            '/unexisting_page/': 'core/404.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][FIRST_OBJ]
        self.assertEqual(first_object.author, self.user)
        self.assertEqual(first_object.id, self.post.id)
        self.assertEqual(first_object.image, self.post.image)

    def test_group_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        if self.post.group:
            response = self.authorized_client.get(
                reverse('posts:group_list', kwargs={'slug': self.group.slug}))
            first_object = response.context.get('group')
            excepted = Post.objects.filter(group=self.group)[FIRST_OBJ]
            self.assertEqual(first_object.title, self.group.title)
            self.assertEqual(first_object.description, self.group.description)
            self.assertEqual(first_object.slug, self.group.slug)
            self.assertEqual(excepted.image, self.post.image)
            self.assertEqual(response.context['page_obj'][FIRST_OBJ], excepted)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username})
        )
        excepted = Post.objects.filter(author=self.user)[FIRST_OBJ]
        self.assertEqual(response.context['page_obj'][FIRST_OBJ], excepted)
        self.assertEqual(excepted.image, self.post.image)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        excepted = Post.objects.filter(id=self.post.id)[FIRST_OBJ]
        self.assertEqual(response.context.get('post'), excepted)
        self.assertEqual(excepted.image, self.post.image)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_with_group_show_on_pages(self):
        '''При создании поста c группой, он появляется на страницах.'''
        if self.post.group:
            address_pages = [
                reverse(
                    'posts:index'),
                reverse(
                    'posts:group_list', kwargs={'slug': self.group.slug}),
                reverse(
                    'posts:profile', kwargs={'username': self.user.username}),
            ]
            for address in address_pages:
                with self.subTest(address=address):
                    response = self.authorized_client.get(address)
                    self.assertIn(self.post, response.context['page_obj'])

    def test_post_not_in_other_groups(self):
        """Пост не попал в группу, для которой не был предназначен."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group_two.slug}))
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_comment_show_on_page(self):
        """При создании комментария, он появляется на странице поста."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id})
        )
        self.assertIn(self.comment, response.context.get('comments'))

    def test_cache_index_page(self):
        """Кеш главной страницы работает."""
        response_1 = self.client.get(reverse('posts:index'))
        Post.objects.create(author=self.user, text='Новый пост')
        response_2 = self.client.get(reverse('posts:index'))
        cache.clear()
        response_3 = self.client.get(reverse('posts:index'))
        self.assertEqual(response_1.content, response_2.content)
        self.assertNotEqual(response_1.content, response_3.content)

    def test_user_can_following(self):
        """Авторизованный юзер может подписываться."""
        self.authorized_client_2.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user.username})
        )
        response = self.authorized_client_2.get(
            reverse(
                'posts:follow_index')
        )
        self.assertIn(self.post, response.context['page_obj'])

    def test_user_can_unfollowing(self):
        """Авторизованный юзер может отписываться."""
        Follow.objects.create(user=self.user_2, author=self.user)
        self.authorized_client_2.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user.username})
        )
        response = self.authorized_client_2.get(
            reverse('posts:follow_index'))
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_new_post_show_at_page_follower(self):
        """Новый пост юзера есть в ленте его подписчиков
        и нет в ленте тех, кто на него не подписан.
        """
        self.authorized_client_2.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user.username})
        )
        new_post = Post.objects.create(author=self.user, text='Новый пост')
        response = self.authorized_client_2.get(reverse('posts:follow_index'))
        self.assertIn(new_post, response.context['page_obj'])
        self.authorized_client_2.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user.username})
        )
        response = self.authorized_client_2.get(reverse('posts:follow_index'))
        self.assertNotIn(new_post, response.context['page_obj'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='User')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )
        for number in range(COUNT_POSTS):
            Post.objects.create(
                author=cls.user,
                group=cls.group,
                text=f'Тестовый пост #{number}',
            )

    def test_first_and_second_pages_contains_records(self):
        posts_on_page = {
            reverse(
                'posts:index'):
                    POSTS_ON_FIRST_PAGE,
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}):
                    POSTS_ON_FIRST_PAGE,
            reverse(
                'posts:profile', kwargs={'username': self.user.username}):
                    POSTS_ON_FIRST_PAGE,
            reverse(
                'posts:index') + '?page=2':
                    POSTS_ON_SECOND_PAGE,
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}) + '?page=2':
                    POSTS_ON_SECOND_PAGE,
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}) + '?page=2':
                    POSTS_ON_SECOND_PAGE,
        }
        for reverse_name, posts in posts_on_page.items():
            with self.subTest(reverse_name=reverse_name):
                cache.clear()
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), posts)
