from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import (HttpResponse, get_object_or_404, redirect,
                              render, reverse)

from posts.forms import CommentForm, PostForm

from .models import Comment, Follow, Group, Post

User = get_user_model()


def index(request):
    latest = Post.objects.all()
    paginator = Paginator(latest, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "index.html",
                  {"page": page, "paginator": paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "group.html",
                  {"group": group, "page": page, "paginator": paginator})


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == "POST" and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect(reverse("posts:index"))

    return render(request, 'new.html', {'form': form})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    if (request.user.id is not None
            and Follow.objects.filter(author_id=author.id).exists()):
        return render(request, 'profile.html',
                      {'author': author, "page": page, "paginator": paginator,
                       "posts": posts, 'following': 'True'})
    else:
        return render(request, 'profile.html',
                      {'author': author, "page": page, "paginator": paginator,
                       "posts": posts})


def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm()
    comments = Comment.objects.filter(post=post)

    return render(request, 'post.html',
                  {"author": author, "post": post, "posts": posts,
                   "form": form, "comments": comments})


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if request.user != post.author:
        return redirect(reverse(
            'posts:post',
            kwargs={'username': post.author, 'post_id': post.id})
        )
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('posts:post', post.author, post.id)
    return render(request, 'post_edit.html', {'form': form, 'post': post})


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = CommentForm(request.POST or None)
    if request.method != "POST" or not form.is_valid():
        return redirect('posts:post', post.author, post.id)
    comment = form.save(commit=False)
    comment.post = post
    comment.author = request.user
    comment.save()
    return redirect(reverse("posts:post", args=[post.author, post.id]))


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользовательской страницы 404 мы не станем
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    return render(request, "follow.html",
                  {"page": page, "paginator": paginator})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
        return redirect('posts:follow_index')
    else:
        return HttpResponse('Вы не можете подписаться на самого себя!')


@login_required
def profile_unfollow(request, username):
    follow_user = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=follow_user).delete()
    return redirect('posts:follow_index')
