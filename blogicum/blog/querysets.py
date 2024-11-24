from django.db.models import Count
from django.utils import timezone


def selected_post_profile(query):
    return (query
            .select_related('author', 'category', 'location')
            .annotate(comment_count=Count('comments'))
            .order_by('-pub_date')
            )


def selected_post_index(query):
    return (selected_post_profile(query).filter(
        is_published=True,
        category__is_published=True,
        pub_date__date__lt=timezone.now(),)
    )
