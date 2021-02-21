# posts/tests/tests_url.py
from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_user')
        cls.another_user = User.objects.create(username='another_test_user')
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
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

        self.templates_urls = {
            'index.html': '/',
            'group.html': '/group/' + self.group.slug,
            'new.html': '/new/',
            'profile.html': '/' + self.user.username + '/',
            'post.html':
                '/' + self.user.username + '/' + str(self.post.id) + '/',
            'post_edit.html':
                '/' + self.user.username + '/' + str(self.post.id) + '/edit/',
            'about/author.html': '/about/author/',
            'about/tech.html': '/about/tech/',

        }

    def test_urls_200(self):
        """Тестируем доступность страниц для пользователя"""
        for value in self.templates_urls.values():
            with self.subTest():
                response = self.authorized_client.get(value)
                self.assertEqual(response.status_code, 200)

    def test_edit_page_for_not_author(self):
        """Тестируем доступность страницы /<str:username>/<int:post_id>/edit/
        для авторизованного пользователя, не автора поста"""
        authorized_client = Client()
        authorized_client.force_login(self.another_user)
        response = authorized_client.get(
            self.templates_urls['post.html'] + '/edit/')
        self.assertEqual(response.status_code, 404)

    def test_redirect_guest_client(self):
        """Тестируем редирект для страницы /new/"""
        response = self.guest_client.get('/new/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/new/')

    def test_redirect_guest_client_for_edit_page(self):
        """Тестируем редирект для страницы
        /<str:username>/<int:post_id>/edit/ """
        response = self.guest_client.get(
            '/' + self.user.username + '/' + str(self.post.id) + '/edit/',
            follow=True
        )
        self.assertRedirects(
            response, '/auth/login/?next=/' + self.user.username + '/' + str(
                self.post.id) + '/edit/'
        )
        response = self.guest_client.get(
            '/' + self.user.username + '/' + str(self.post.id) + '/edit/',
            follow=True
        )
        self.assertRedirects(
            response, '/auth/login/?next=/' + self.user.username + '/' + str(
                self.post.id) + '/edit/'
        )

    def test_url_correct_template(self):
        """Тестируем шаблоны страниц"""
        for template, reverse_name in self.templates_urls.items():
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
