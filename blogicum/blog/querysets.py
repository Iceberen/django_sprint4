from django.db.models import Count
from django.utils import timezone


def filter_profile_post_list(query):
    return (query
            .select_related('author', 'category', 'location')
            .annotate(comment_count=Count('comments'))
            .order_by('-pub_date')
            )


def add_filter_post_list(query):
    return (query.filter(
        is_published=True,
        category__is_published=True,
        pub_date__date__lt=timezone.now(),)
    )
