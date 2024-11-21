from datetime import datetime

from django.urls import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView, View
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.http import Http404
from django.utils import timezone

from .models import Post, Category, Comment
from .forms import PostForm, UpdateUserForm, CommentForm
from .constants import QUANTITY_ON_PAGINATE


User = get_user_model()


class ProfileListView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = QUANTITY_ON_PAGINATE

    def get_queryset(self):
        queryset = Post.objects.select_related('category').filter(
            author=get_object_or_404(User, username=self.kwargs['username']),
        ).order_by('-pub_date').annotate(comment_count=Count('comments'))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(
            User,
            username=self.kwargs['username']
        )
        return context


class ProfileUpdateView(LoginRequiredMixin, View):
    def get(self, request):
        user_form = UpdateUserForm(instance=request.user)
        return render(request, 'blog/user.html', {'form': user_form})

    def post(self, request):
        user_form = UpdateUserForm(request.POST, instance=request.user)
        if user_form.is_valid():
            user_form.save()
            return redirect('blog:profile', str(self.request.user.username))


class PostListView(ListView):
    model = Post
    queryset = Post.objects.select_related('category').filter(
        is_published=True,
        category__is_published=True,
        pub_date__date__lt=datetime.now()
    ).order_by('-pub_date').annotate(comment_count=Count('comments'))
    template_name = 'blog/index.html'
    paginate_by = QUANTITY_ON_PAGINATE


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = (
            self.object.comments.select_related('author')
        )
        context['form'] = CommentForm()
        return context

    def dispatch(self, request, *args, **kwargs):
        """
        Проверяем, что пост, снятый с публикации, в неопубликованной
        категории или отложенный по времени видит только его автор.
        """
        instance = get_object_or_404(Post, pk=self.kwargs['post_id'])
        if ((instance.is_published is False
             or instance.category.is_published is False
             or instance.pub_date > timezone.now())
                and instance.author != self.request.user):
            raise Http404
        return super().dispatch(request, *args, **kwargs)


class CategotyPostListView(ListView):
    model = Post
    template_name = 'blog/category.html'
    paginate_by = QUANTITY_ON_PAGINATE

    def get_queryset(self):
        queryset = Post.objects.select_related('category').filter(
            category=get_object_or_404(Category,
                                       slug=self.kwargs['category_slug'],
                                       is_published=True
                                       ),
            is_published=True,
            category__is_published=True,
            pub_date__date__lt=datetime.now()
        ).order_by('-pub_date').annotate(comment_count=Count('comments'))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile',
                       kwargs={'username': self.request.user.username})


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=self.kwargs['post_id'])
        if instance.author != request.user:
            return redirect('blog:post_detail', post_id=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'post_id': self.kwargs[self.pk_url_kwarg]})


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=self.kwargs['post_id'])
        if instance.author != request.user:
            return redirect('blog:post_detail', post_id=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:profile',
                       kwargs={'username': self.request.user.username})


@login_required
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(data=request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
    return redirect('blog:post_detail', post_id=post_id)


@login_required
def post_comment_edit(request, post_id, comment_id):
    post = get_object_or_404(Post, id=post_id)
    instance = get_object_or_404(
        Comment.objects.filter(post=post), id=comment_id
    )
    if instance.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    form = CommentForm(request.POST or None, instance=instance)
    context = {'form': form, 'comment': instance}

    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/comment.html', context)


@login_required
def post_comment_delete(request, post_id, comment_id):
    post = get_object_or_404(Post, id=post_id)
    instance = get_object_or_404(
        Comment.objects.filter(post=post), id=comment_id
    )
    if instance.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    context = {'comment': instance}
    if request.method == 'POST':
        instance.delete()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/comment.html', context)
