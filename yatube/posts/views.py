from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .models import Group, Post, User, Follow
from .forms import PostForm, CommentForm


@cache_page(20)
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {'page': page, })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    group_post_list = group.posts.all()
    paginator = Paginator(group_post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html',
                  {'group': group, 'page': page}, )


def profile(request, username):
    author = get_object_or_404(User, username=username)
    author_posts = author.posts.all()
    paginator = Paginator(author_posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'profile.html', {
        'author': author,
        'page': page,
    })


def post_view(request, username, post_id):
    form = CommentForm(request.POST or None)
    post = get_object_or_404(
        Post, author__username=username,
        id=post_id)
    comments = post.comments.filter(post=post)
    return render(
        request, 'post.html',
        {'post': post, 'form': form, 'comments': comments})


@login_required
def new_post(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')
    return render(request, 'new.html', {'form': form, 'is_new': True, })


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(
        Post, author__username=username, id=post_id)
    if post.author != request.user:
        return redirect('post', username, post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        post = form.save(commit=False)
        form.save()
        return redirect('post', username, post_id)
    return render(request, 'new.html',
                  {'post': post, 'form': form})


def page_not_found(request, exception):
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(
        Post, author__username=username, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('post', username, post_id)
    return redirect('post', username, post_id)


@login_required
def follow_index(request):
    posts_list = Post.objects.filter(
        author__following__user=request.user)
    paginator = Paginator(posts_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html', {'page': page})


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if user == author:
        return redirect('profile', username)
    followed = Follow.objects.filter(user=user, author=author)
    following = True if followed else False

    if following:
        return redirect('profile', username)
    else:
        model = Follow.objects.create(
            user=request.user, author=author)
        model.save()
        return redirect('profile', username)


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    followed = Follow.objects.filter(user=user, author=author)
    following = True if followed else False

    if following:
        model = Follow.objects.filter(
            user=request.user, author=author)
        model.delete()
        return redirect('profile', username)
    else:
        return redirect('profile', username)
