import django_filters
from .models import News, Comment

class NewsFilter(django_filters.FilterSet):
    """Filter set for news articles"""
    title = django_filters.CharFilter(lookup_expr='icontains')
    content = django_filters.CharFilter(lookup_expr='icontains')
    author = django_filters.CharFilter(lookup_expr='icontains')
    country = django_filters.CharFilter(lookup_expr='iexact')
    county = django_filters.CharFilter(lookup_expr='iexact')
    town = django_filters.CharFilter(lookup_expr='iexact')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = News
        fields = [
            'title', 'content', 'author', 'source', 'categories',
            'status', 'is_fact_checked', 'country', 'county', 'town',
            'created_after', 'created_before'
        ]

class CommentFilter(django_filters.FilterSet):
    """Filter set for news comments"""
    content = django_filters.CharFilter(lookup_expr='icontains')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = Comment
        fields = ['news', 'user', 'parent', 'is_approved', 'content']