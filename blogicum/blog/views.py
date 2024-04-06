from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm

from blog.models import Post, Category, Comment
from .forms import PostForm, CommentForm


def get_published_posts(posts):
    return posts.filter(is_published=True,
                        pub_date__lte=timezone.now(),
                        category__is_published=True)


def index(request):
    posts = Post.objects.all()
    post_list = get_published_posts(posts)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, 'blog/index.html', context)


def post_detail(request, post_id):
    template_name = 'blog/detail.html'
    post = get_object_or_404(Post,
                             pk=post_id)
    comments = post.comments.all()
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid:
            comment_form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        comment_form = CommentForm()
    context = {'post': post, 'comments': comments,
               'comment_form': comment_form}
    return render(request, template_name, context)


def category_posts(request, category_slug):
    template_name = 'blog/category.html'
    category = get_object_or_404(Category, slug=category_slug,
                                 is_published=True)
    all_posts = Post.objects.filter(category=category)
    post_list = get_published_posts(all_posts)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'category': category, 'page_obj': page_obj}
    return render(request, template_name, context)


def profile(request, username):
    profile = get_object_or_404(User, username=username)
    if request.user == profile:
        posts = Post.objects.filter(author=profile)
    else:
        posts = Post.objects.filter(author=profile,
                                    pub_date__lte=timezone.now())
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'profile': profile, 'page_obj': page_obj}
    return render(request, 'blog/profile.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = CommentForm()
    context = {'form': form, 'post_id': post_id}
    return render(request, 'blog/detail.html', context)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id, author=request.user)
    form = CommentForm(request.POST or None, instance=comment)
    context = {'form': form, 'comment': comment}
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/comment.html', context)


@login_required
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
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
    profile = get_object_or_404(User, username=username)
    if request.user == profile:
        if request.method == 'POST':
            form = UserChangeForm(request.POST, instance=profile)
            if form.is_valid():
                form.save()
                return redirect('blog:profile', username=username)
        else:
            form = UserChangeForm(instance=profile)
        return render(request, 'blog/user.html', {'form': form})


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            if post.pub_date > timezone.now():
                post.is_published = False
            else:
                post.is_published = True
            post.author = request.user
            post.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = PostForm()
    return render(request, 'blog/create.html', {'form': form})


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        if request.user.is_authenticated:
            return redirect('blog:post_detail', post_id=post_id)
        else:
            return redirect('login')
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/create.html', {'form': form})
