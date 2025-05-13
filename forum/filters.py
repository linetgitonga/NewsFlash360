import django_filters
from .models import Post, Comment


class PostFilter(django_filters.FilterSet):
    """Advanced filter set for posts"""
    title = django_filters.CharFilter(lookup_expr='icontains')
    content = django_filters.CharFilter(lookup_expr='icontains')
    location = django_filters.CharFilter(lookup_expr='icontains')
    tags = django_filters.CharFilter(field_name='tags__name', lookup_expr='icontains')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    upvotes_min = django_filters.NumberFilter(field_name='upvotes', lookup_expr='count__gte')
    
    class Meta:
        model = Post
        fields = [
            'title', 'content', 'author', 'category', 'status',
            'language', 'fact_checked', 'location', 'tags',
            'created_after', 'created_before', 'upvotes_min'
        ]


class CommentFilter(django_filters.FilterSet):
    """Filter set for comments"""
    content = django_filters.CharFilter(lookup_expr='icontains')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = Comment
        fields = ['post', 'author', 'parent', 'active', 'content', 'created_after', 'created_before']