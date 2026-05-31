from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CommentForm, CustomUserChangeForm, PostForm
from .models import Category, Comment, Post

POSTS_PER_PAGE = 10


# Вспомогательные функции(по рекомендации)

def get_published_posts_queryset():
    """Возвращает QuerySet опубликованных постов с аннотацией и связями."""
    return Post.objects.filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True
    ).select_related(
        'author', 'location', 'category'
    ).annotate(
        comment_count=Count('comments')
    )


def paginate_queryset(request, queryset):
    """Разбивает QuerySet на страницы."""
    paginator = Paginator(queryset, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


# View функции

def index(request):
    """Главная страница."""
    template_name = 'blog/index.html'
    post_list = get_published_posts_queryset().order_by('-pub_date')
    page_obj = paginate_queryset(request, post_list)
    return render(request, template_name, {'page_obj': page_obj})


def category_posts(request, category_slug):
    """Страница постов определенной категории."""
    template_name = 'blog/category.html'
    category = get_object_or_404(
        Category, slug=category_slug, is_published=True
    )
    post_list = get_published_posts_queryset().filter(
        category=category
    ).order_by('-pub_date')
    page_obj = paginate_queryset(request, post_list)
    return render(
        request, template_name, {'category': category, 'page_obj': page_obj}
    )


def post_detail(request, post_id):
    """Страница отдельного поста."""
    template_name = 'blog/detail.html'
    post = get_object_or_404(Post, id=post_id)
    post_published = post.is_published and post.pub_date <= timezone.now()
    category_published = (post.category is None) or post.category.is_published
    is_accessible = (post_published and category_published) or (
        request.user.is_authenticated and post.author == request.user
    )
    if not is_accessible:
        raise Http404("Страница не найдена") 
    comments = post.comments.select_related('author').order_by('created_at')
    form = CommentForm()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, template_name, context)


def profile(request, username):
    """Профиль пользователя."""
    template_name = 'blog/profile.html'
    profile_user = get_object_or_404(User, username=username)
    posts_query = Post.objects.filter(author=profile_user).select_related(
        'author', 'location', 'category'
    ).annotate(
        comment_count=Count('comments')
    )
    if request.user != profile_user:
        posts_query = posts_query.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True
        )   
    post_list = posts_query.order_by('-pub_date')
    page_obj = paginate_queryset(request, post_list)
    
    context = {
        'profile': profile_user,
        'page_obj': page_obj,
    }
    return render(request, template_name, context)


@login_required
def edit_profile(request):
    """Редактирование профиля пользователя."""
    template_name = 'blog/user.html'
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, template_name, {'form': form})


@login_required
def create_post(request):
    """Создание новой публикации."""
    template_name = 'blog/create.html'
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = PostForm()
    return render(request, template_name, {'form': form})


@login_required
def edit_post(request, post_id):
    """Редактирование публикации."""
    template_name = 'blog/create.html'
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
        
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = PostForm(instance=post)
    return render(request, template_name, {'form': form, 'is_edit': True})


@login_required
def delete_post(request, post_id):
    """Удаление публикации."""
    template_name = 'blog/create.html' 
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
        
    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', username=request.user.username)
        
    form = PostForm(instance=post)
    return render(request, template_name, {'form': form, 'is_delete': True})


@login_required
def add_comment(request, post_id):
    """Добавление комментария."""
    base_post = get_object_or_404(Post, id=post_id)

    if base_post.author != request.user:
        post = get_object_or_404(get_published_posts_queryset(), id=post_id)
    else:
        post = base_post
        
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()     
    return redirect('blog:post_detail', post_id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    """Редактирование комментария."""
    template_name = 'blog/comment.html'
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
        
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = CommentForm(instance=comment)
    return render(request, template_name, {'form': form, 'comment': comment})


@login_required
def delete_comment(request, post_id, comment_id):
    """Удаление комментария."""
    template_name = 'blog/comment.html'
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
        
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, template_name, {'comment': comment, 'is_delete': True})