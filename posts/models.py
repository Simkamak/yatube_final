from django.contrib.auth import get_user_model
from django.db import models
from pytils.translit import slugify

User = get_user_model()


class Group(models.Model):
    title = models.CharField('Название группы', max_length=200)
    slug = models.SlugField('URL', unique=True, max_length=100)
    description = models.TextField('Описание группы')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:100]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name='Введите или отредактируйте пост',
                            help_text='Напишите пост')
    pub_date = models.DateTimeField("date published", auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="posts")
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, blank=True,
                              null=True, related_name="posts",
                              verbose_name='Название группы',
                              help_text='Выберите группу для поста')
    image = models.ImageField(upload_to='posts/', blank=True, null=True,
                              verbose_name='Рисунок')

    def __str__(self):
        return self.text

    class Meta:
        ordering = ['-pub_date']


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.SET_NULL, null=True,
                             related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='comments')
    text = models.TextField(verbose_name='Комментарий',
                            help_text='Оставьте комментарий')
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='follower')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='following')
