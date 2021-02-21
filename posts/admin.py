from django.contrib import admin

from .models import Comment, Follow, Group, Post


class PostAdmin(admin.ModelAdmin):
    # перечисляем поля, которые должны отображаться в админке
    list_display = ("pk", "text", "pub_date", "author")
    # добавляем интерфейс для поиска по тексту постов
    search_fields = ("text",)
    # добавляем возможность фильтрации по дате
    list_filter = ("pub_date",)
    empty_value_display = "-пусто-"


class GroupAdmin(admin.ModelAdmin):
    # перечисляем поля, которые должны отображаться в админке
    list_display = ("pk", "title", "description", "slug")
    # добавляем интерфейс для поиска по тексту постов
    search_fields = ("title", "description")
    # добавляем возможность фильтрации по дате
    list_filter = ("slug",)
    empty_value_display = "-пусто-"


class CommentAdmin(admin.ModelAdmin):
    list_display = ('text', 'created', 'author', 'post')


class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')


# при регистрации модели Post источником конфигурации для неё назначаем
# класс PostAdmin
admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Follow, FollowAdmin)
