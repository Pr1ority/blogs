from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm
from django.db.models import Count

from blog.models import Post, Category, Comment
from blog.forms import PostForm, CommentForm

POSTS_PER_PAGE = 10


def get_paginated_page(request, queryset, per_page):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


def get_published_posts(posts, include_comments=False):
    published_posts = posts.filter(is_published=True,
                                   pub_date__lte=timezone.now(),
                                   category__is_published=True)
    if include_comments:
        published_posts = published_posts.annotate(
            comment_count=Count('comments'))
        published_posts = published_posts.order_by('-pub_date')
    return published_posts.select_related('author', 'category')


def index(request):
    posts = Post.objects.all()
    published_posts = get_published_posts(posts, include_comments=True)
    page_obj = get_paginated_page(request, published_posts, POSTS_PER_PAGE)
    context = {'page_obj': page_obj}
    return render(request, 'blog/index.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        post = get_object_or_404(
            (get_published_posts(Post.objects)), pk=post_id)
    comments = post.comments.all()
    form = CommentForm()
    return render(request, 'blog/detail.html', {'post': post,
                                                'comments': comments,
                                                'form': form})


def category_posts(request, category_slug):
    template_name = 'blog/category.html'
    category = get_object_or_404(Category, slug=category_slug,
                                 is_published=True)
    posts = get_published_posts(category.posts.all())
    page_obj = get_paginated_page(request, posts, POSTS_PER_PAGE)
    context = {'category': category, 'page_obj': page_obj}
    return render(request, template_name, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    if request.user == author:
        page_obj = get_paginated_page(request, posts, POSTS_PER_PAGE)
    else:
        published_posts = get_published_posts(posts, include_comments=True)
        page_obj = get_paginated_page(request, published_posts, POSTS_PER_PAGE)
    context = {'author': author, 'page_obj': page_obj}
    return render(request, 'blog/profile.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', post_id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    form = CommentForm(request.POST or None, instance=comment)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/comment.html', {'form': form,
                                                 'comment': comment})


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.method == 'POST':
        if request.user == post.author:
            post.delete()
            return redirect('blog:index')
    context = {'post': post}
    return render(request, 'blog/index.html', context)


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id=post_id)
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/comment.html', {'comment': comment})


@login_required
def edit_profile(request, username):
    if request.user != get_object_or_404(User, username=username):
        return redirect('blog:profile', username=username)
    form = UserChangeForm(request.POST or None, instance=request.user)
    if form.is_valid():
        form.save()
        return redirect('blog:profile', username=username)
    return render(request, 'blog/user.html', {'form': form})


@login_required
def create_post(request):
    form = PostForm(request.POST or None, request.FILES)
    if not form.is_valid():
        return render(request, 'blog/create.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('blog:profile', username=request.user.username)


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('blog:post_detail', post_id=post_id)
    form = PostForm(request.POST or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/create.html', {'form': form})
