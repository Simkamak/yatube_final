import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import caches
from django.core.cache.utils import make_template_fragment_key
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post
from yatube.settings import BASE_DIR, MEDIA_ROOT

User = get_user_model()

MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class CustomErrorHandlerTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_404_page_not_found(self):
        response = self.guest_client.get('fake_url/')
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, status_code=404, text='Ошибка 404')


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.templates_pages_names = {
            'about/author.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech')
        }

    def test_author_page_accessible_by_name(self):
        """URL, генерируемый при помощи имени about:..., доступен."""
        for item in self.templates_pages_names.values():
            with self.subTest():
                response = self.guest_client.get(item)
                self.assertEqual(response.status_code, 200)

    def test_about_page_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for template, reverse_name in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create(username='test_user')
        cls.group = Group.objects.create(
            title='Test',
            description='Много букв'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=cls.uploaded
        )

    def setUp(self):
        # Создаем авторизованного клиента
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)
        self.templates_pages_names = {
            'index.html': reverse('posts:index'),
            'new.html': reverse('posts:new_post'),
            'group.html': reverse('posts:group_slug',
                                  kwargs={'slug': self.group.slug}),
            'profile.html': reverse('posts:profile',
                                    kwargs={'username': self.user.username}),
            'post.html': reverse('posts:post',
                                 kwargs={'username': self.user.username,
                                         'post_id': self.post.id}),
            'post_edit.html': reverse('posts:post_edit',
                                      kwargs={'username': self.user.username,
                                              'post_id': self.post.id}),
        }
        self.templates_pages_names_for_context = {
            'index.html': reverse('posts:index'),
            'group.html': reverse('posts:group_slug',
                                  kwargs={'slug': self.group.slug}),
            'profile.html': reverse('posts:profile',
                                    kwargs={'username': self.user.username}),

        }

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_index_page_cache(self):
        """Тестируем кэштрование данных на странице index.html"""
        cache = caches['default']
        key = make_template_fragment_key('index_page')
        self.assertTrue(cache.get(key))

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for template, reverse_name in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_page_show_correct_context(self):
        """Шаблоны index.html, group.html, profile.html сформированы с
        правильным контекстом."""
        for template in self.templates_pages_names_for_context:
            response = self.authorized_client.get(
                self.templates_pages_names_for_context[template])
            post = response.context.get('page')[0]
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.group, self.group)
            self.assertEqual(post.author, self.user)
            self.assertEqual(post.pub_date, self.post.pub_date)
            self.assertEqual(post.image, self.post.image)

    def test_new_page_show_correct_context(self):
        """Шаблон new.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:new_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }

        # Проверяем, что типы полей формы в словаре context
        # соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_index_page_list_is_1(self):
        # Удостоверимся, что на страницу со списком постов передаётся
        # ожидаемое количество объектов
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page']), 1)

    def test_post_group_page_list_is_1(self):
        # Удостоверимся, что на страницу группы постов передаётся
        # ожидаемое количество объектов
        response = self.authorized_client.get(
            self.templates_pages_names['group.html'])
        self.assertEqual(len(response.context['page']), 1)

    def test_post_page_show_correct_context(self):
        """Шаблон post.html сформирован с правильным контекстом для
        /<username>/<post_id>/. """
        response = self.authorized_client.get(reverse(
            'posts:post',
            kwargs={'username': self.user.username, 'post_id': self.post.id})
        )
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        post = response.context.get('posts')[0]
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.pub_date, self.post.pub_date)
        self.assertEqual(post.author.username, self.user.username)
        self.assertEqual(post.image, self.post.image)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit.html сформирован с правильным контекстом для
        /<username>/<post_id>/edit/. """
        response = self.authorized_client.get(reverse(
            'posts:post_edit',
            kwargs={'username': self.user.username, 'post_id': self.post.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        # Проверяем, что типы полей формы в словаре context
        # соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        # Проверим, что поле с текстом не пусто
        field_not_empty = response.context.get('post')
        self.assertEqual(field_not_empty, self.post)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_user')
        cls.group = Group.objects.create(
            title='Test',
            description='Много букв'
        )
        posts = [Post(author=cls.user, group=cls.group, text=str(i)) for i in
                 range(13)]
        Post.objects.bulk_create(posts)

    def setUp(self):
        # Создаем авторизованного клиента
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        """Проверка, что 1 страница содержит 10 записей"""
        response = self.authorized_client.get(reverse('posts:index'))
        response_1 = self.authorized_client.get(reverse(
            'posts:group_slug', kwargs={'slug': self.group.slug})
        )
        # Проверка: количество постов на первой странице равно 10.

        self.assertEqual(len(response.context.get('page').object_list), 10)
        self.assertEqual(len(response_1.context.get('page').object_list), 10)

    def test_second_page_contains_three_records(self):
        """Проверка, что 2 страница содержит 3 записей"""
        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2')
        response_1 = self.authorized_client.get(
            reverse('posts:group_slug',
                    kwargs={'slug': self.group.slug}) + '?page=2'
        )

        # Проверка: на второй странице должно быть три поста.

        self.assertEqual(len(response.context.get('page').object_list), 3)
        self.assertEqual(len(response_1.context.get('page').object_list), 3)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_user')
        cls.author = User.objects.create(username='test_author')
        cls.another_user = User.objects.create(username='another_user')
        cls.group = Group.objects.create(
            title='Test',
            description='Много букв'
        )

    def setUp(self):
        # Создаем авторизованного клиента
        self.authorized_client = Client()
        self.authorized_client_1 = Client()
        self.authorized_client_2 = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)
        self.authorized_client_1.force_login(self.author)
        self.authorized_client_2.force_login(self.another_user)

    def test_follow_myself(self):
        """Проверка невозможности подписки на самого себя"""
        before_follow = self.author.follower.count()
        self.authorized_client_1.get(reverse('posts:profile_follow',
                                             args=[self.author.username]))
        after_follow = self.author.follower.count()
        self.assertEqual(before_follow, after_follow,
                         'Проверьте, что нельзя подписаться на самого себя')

    def test_follow_author(self):
        """Проверка возможности подписки"""
        self.authorized_client.get(
            reverse('posts:profile_follow', args=[self.author.username]))
        after_follow = self.user.follower.count()
        self.assertEqual(after_follow, 1,
                         'Проверьте, что вы можете подписаться на пользователя'
                         )
        self.authorized_client.get(
            reverse('posts:profile_follow', args=[self.author.username]))
        second_follow = self.user.follower.count()
        self.assertTrue(after_follow == second_follow,
                        'Проверьте, что вы можете подписаться на пользователя '
                        'только один раз')

    def test_unfollow_author(self):
        """Проверка возможности отписки"""
        Follow.objects.create(
            user=self.user,
            author=self.author
        )
        self.authorized_client.get(
            reverse('posts:profile_unfollow', args=[self.author.username]))
        count = self.user.follower.count()
        self.assertTrue(count == 0,
                        'Проверьте, что вы можете отписаться от пользователя')

    def test_follow_context(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
             подписан и не появляется в ленте тех, кто не подписан на него."""
        Post.objects.create(
            author=self.author,
            text='Тестовый текст',
            group=self.group
        )
        Post.objects.create(
            author=self.author,
            text='Тестовый текст1',
            group=self.group
        )
        Post.objects.create(
            author=self.user,
            text='Тестовый текст2',
            group=self.group
        )
        Follow.objects.create(
            user=self.user,
            author=self.author
        )
        Follow.objects.create(
            user=self.author,
            author=self.user
        )
        Follow.objects.create(
            user=self.another_user,
            author=self.user
        )
        Follow.objects.create(
            user=self.another_user,
            author=self.author
        )

        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertTrue(len(response.context.get('page')) == 2,
                        'Проверьте, что на странице `/follow/` отображается'
                        'список статей авторов на которых подписаны')
        response_1 = self.authorized_client_1.get(reverse('posts:follow_index')
                                                  )
        self.assertTrue(len(response_1.context.get('page')) == 1,
                        'Проверьте, что на странице `/follow/` отображается'
                        'список статей авторов на которых подписаны')
        response_2 = self.authorized_client_2.get(reverse('posts:follow_index')
                                                  )
        self.assertTrue(len(response_2.context.get('page')) == 3,
                        'Проверьте, что на странице `/follow/` отображается'
                        'список статей авторов на которых подписаны')


class CommentViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_user')
        cls.group = Group.objects.create(
            title='Test',
            description='Много букв'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group
        )

    def setUp(self):
        # Создаем авторизованного клиента
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_comment_add_view(self):
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=[self.user.username,
                                               self.post.id]),
            data={'text': 'Новый коммент!'})
        self.assertRedirects(response, reverse('posts:post',
                                               args=[self.user.username,
                                                     self.post.id]), 302)
