from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Comment, Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_user')
        cls.group = Group.objects.create(
            title='Ж' * 100,
            description='Много букв'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Comment'
        )

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = self.post
        group = self.group
        comment = self.comment
        post_field_verboses = {
            'text': 'Введите или отредактируйте пост',
            'group': 'Название группы',
        }
        group_field_verboses = {
            'title': 'Название группы',
            'description': 'Описание группы',
            'slug': 'URL'
        }
        comment_field_verboses = {
            'text': 'Комментарий'
        }
        for value, expected in post_field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)
        for value, expected in group_field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).verbose_name, expected)
        for value, expected in comment_field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    comment._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = self.post
        comment = self.comment
        field_help_texts = {
            'text': 'Напишите пост',
            'group': 'Выберите группу для поста'
        }
        comment_field_help_texts = {
            'text': 'Оставьте комментарий'
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)
        for value, expected in comment_field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    comment._meta.get_field(value).help_text, expected)

    def test_text_convert_to_slug(self):
        """Содержимое поля title преобразуется в slug."""
        group = self.group
        slug = group.slug
        self.assertEquals(slug, 'zh' * 50)

    def test_object_name_feild(self):
        """В поле __str__  объекта post записано значение поля post.text."""
        """В поле __str__  объекта group записано значение поля group.title."""
        group = self.group
        post = self.post
        comment = self.comment
        expected_object_name_for_comment = comment.text[:15]
        expected_object_name = group.title
        expected_object_name_for_post = post.text[:15]
        self.assertEqual(expected_object_name, str(group))
        self.assertEqual(expected_object_name_for_post, str(post))
        self.assertEqual(expected_object_name_for_comment, str(comment))

    def test_text_slug_max_length_not_exceed(self):
        """
        Длинный slug обрезается и не превышает max_length поля slug в модели.
        """
        group = PostModelTest.group
        max_length_slug = group._meta.get_field('slug').max_length
        length_slug = (len(group.slug))
        self.assertEqual(max_length_slug, length_slug)
