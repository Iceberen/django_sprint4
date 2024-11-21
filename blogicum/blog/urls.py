from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.PostListView.as_view(), name='index'),
    path('posts/<int:post_id>/', views.PostDetailView.as_view(),
         name='post_detail'),
    path('posts/create/', views.PostCreateView.as_view(),
         name='create_post'),
    path('posts/<int:post_id>/edit/', views.PostUpdateView.as_view(),
         name='edit_post'),
    path('posts/<int:post_id>/delete/', views.PostDeleteView.as_view(),
         name='delete_post'),

    path('category/<slug:category_slug>/',
         views.CategotyPostListView.as_view(),
         name='category_posts'),

    path('profile/<slug:username>/', views.ProfileListView.as_view(),
         name='profile'),
    path('edit_profile/',
         views.ProfileUpdateView.as_view(),
         name='edit_profile'),

    path('posts/<int:post_id>/comment/', views.post_comment,
         name='add_comment'),
    path('posts/<int:post_id>/edit_comment/<int:comment_id>/',
         views.post_comment_edit,
         name='edit_comment'),
    path('posts/<int:post_id>/delete_comment/<int:comment_id>/',
         views.post_comment_delete,
         name='delete_comment'),
]
