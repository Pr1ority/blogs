from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm
from django.urls import reverse_lazy

from blog.models import Post, Category, Comment
from .forms import PostForm, CommentForm

POSTS_PER_PAGE = 10


def get_paginated_page(request, queryset, per_page):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


def get_published_posts(posts):
    return posts.filter(is_published=True,
                        pub_date__lte=timezone.now(),
                        category__is_published=True).select_related('author',
                                                                    'category')


def index(request):
    posts = Post.objects.all()
    published_posts = get_published_posts(posts)
    page_obj = get_paginated_page(request, published_posts, POSTS_PER_PAGE)
    context = {'page_obj': page_obj}
    return render(request, 'blog/index.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        post = get_object_or_404(
            (get_published_posts(Post.objects)), pk=post_id)
    comments = post.comments.order_by('created_at')
    form = CommentForm()
    return render(request, 'blog/detail.html', {'post': post,
                                                'comments': comments,
                                                'form': form})


def category_posts(request, category_slug):
    template_name = 'blog/category.html'
    category = get_object_or_404(Category, slug=category_slug,
                                 is_published=True)
    post_list = get_published_posts(category.posts.all())
    page_obj = get_paginated_page(request, post_list, POSTS_PER_PAGE)
    context = {'category': category, 'page_obj': page_obj}
    return render(request, template_name, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    if request.user == author:
        posts = author.posts.all()
    else:
        posts = author.posts.filter(pub_date__lte=timezone.now())
    page_obj = get_paginated_page(request, posts, POSTS_PER_PAGE)
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
    else:
        return redirect('blog:post_detail', post_id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    form = CommentForm(request.POST or None, instance=comment)
    context = {'form': form, 'comment': comment}
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/comment.html', context)


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
    comment = get_object_or_404(Comment, pk=comment_id, author=request.user)
    context = {'comment': comment}
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/comment.html', context)


@login_required
def edit_profile(request, username):
    author = get_object_or_404(User, username=username)
    if request.user == author:
        if request.method == 'POST':
            form = UserChangeForm(request.POST, instance=author)
            if form.is_valid():
                form.save()
                return redirect('blog:profile', username=username)
        else:
            form = UserChangeForm(instance=author)
        return render(request, 'blog/user.html', {'form': form})
    return redirect('blog:profile', username=username)


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = PostForm()
    return render(request, 'blog/create.html', {'form': form})


@login_required
def edit_post(request, post_id):
    if not request.user.is_authenticated:
        return redirect(reverse_lazy('login'))
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('blog:post_detail', post_id=post_id)
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/create.html', {'form': form})
