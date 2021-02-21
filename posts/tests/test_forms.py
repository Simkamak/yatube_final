import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Group, Post

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем запись в базе данных
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
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

        )

    def setUp(self):
        # Создаем авторизованного клиента
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        # Подсчитаем количество записей в Post
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст1',
            'author': self.user,
            'group': self.group.id,
            'image': self.uploaded
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:new_post'),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse('posts:index'))
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что создалась запись с нашим слагом
        self.assertTrue(
            Post.objects.filter(group=self.group.id).exists())
        self.assertTrue(response.context.get('page')[0].image, self.uploaded)

    def test_create_comment(self):
        """Валидная форма создает запись в Comment."""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
            'author': self.user,
            'post': self.post,
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=[self.user, self.post.id]),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post',
                                               args=[self.user, self.post.id]))
        self.assertEqual(Comment.objects.count(), comment_count + 1)

    def test_post_edit_save_to_database(self):
        """Проверка редактирования поста в форме /<username>/<post_id>/edit/ -
        изменяется соответствующая запись"""
        posts_count = Post.objects.count()
        post = Post.objects.get(id=self.post.id)
        form_data = {
            'text': 'Измененный тестовый текст',
            'author': self.user,
            'group': PostCreateFormTests.group.id,
        }
        self.authorized_client.post(
            reverse('posts:post_edit', args=[post.author, post.id]),
            data=form_data,
            follow=True
        )
        # Проверяем, что тестовая запись изменилась
        self.assertNotEqual(post, post.refresh_from_db(),
                            'Запись /<username>/<post_id>/edit/ не изменилась')
        # Проверяем, что колиество записей не изменилось
        self.assertEqual(Post.objects.count(), posts_count,
                         'Кол-во записей увеличивается при редактировании!')
