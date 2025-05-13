from django.db.models import Q, Count, Avg, F
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Category, Source, News, Tag, FactCheck, 
    SavedNews, NewsRating, Comment
)
from .serializers import (
    CategorySerializer, SourceSerializer, NewsListSerializer, 
    NewsDetailSerializer, TagSerializer, FactCheckSerializer, 
    SavedNewsSerializer, NewsRatingSerializer, CommentSerializer,
    CommentDetailSerializer
)


class NewsPagination(PageNumberPagination):
    """Custom pagination for news articles."""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for news categories."""
    
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'


class SourceViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for news sources."""
    
    queryset = Source.objects.all()
    serializer_class = SourceSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for news tags."""
    
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'


class NewsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for news articles."""
    
    queryset = News.objects.filter(status='published')
    permission_classes = [AllowAny]
    pagination_class = NewsPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['categories__slug', 'tags__slug', 'source', 'county', 'town', 'is_fact_checked']
    search_fields = ['title', 'content', 'summary', 'author']
    ordering_fields = ['published_date', 'view_count', 'share_count']
    ordering = ['-published_date']
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return NewsDetailSerializer
        return NewsListSerializer
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Increment view count
        instance.view_count += 1
        instance.save(update_fields=['view_count'])
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def share(self, request, slug=None):
        """Endpoint to track when a news article is shared."""
        news = self.get_object()
        news.share_count += 1
        news.save(update_fields=['share_count'])
        return Response({'status': 'share counted'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def save(self, request, slug=None):
        """Endpoint to save a news article for a user."""
        news = self.get_object()
        user = request.user
        
        # Check if already saved
        saved, created = SavedNews.objects.get_or_create(user=user, news=news)
        
        if created:
            return Response({'status': 'news saved'}, status=status.HTTP_201_CREATED)
        return Response({'status': 'news already saved'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def unsave(self, request, slug=None):
        """Endpoint to unsave a news article for a user."""
        news = self.get_object()
        user = request.user
        
        try:
            saved_news = SavedNews.objects.get(user=user, news=news)
            saved_news.delete()
            return Response({'status': 'news unsaved'}, status=status.HTTP_204_NO_CONTENT)
        except SavedNews.DoesNotExist:
            return Response({'error': 'news not saved'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def rate(self, request, slug=None):
        """Endpoint to rate a news article."""
        news = self.get_object()
        user = request.user
        
        # Validate rating
        try:
            rating = int(request.data.get('rating', 0))
            if not 1 <= rating <= 5:
                return Response(
                    {'error': 'Rating must be between 1 and 5'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid rating value'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create or update rating
        serializer = NewsRatingSerializer(
            data={'news': news.id, 'rating': rating},
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save(user=user)
            # Calculate new average rating
            avg_rating = NewsRating.objects.filter(news=news).aggregate(Avg('rating'))
            return Response({
                'status': 'rating saved',
                'average_rating': avg_rating['rating__avg'] or 0
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def saved(self, request):
        """Endpoint to list all saved news articles for a user."""
        user = request.user
        saved_news = SavedNews.objects.filter(user=user).order_by('-saved_date')
        
        page = self.paginate_queryset(saved_news)
        if page is not None:
            serializer = SavedNewsSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = SavedNewsSerializer(saved_news, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Endpoint to get trending news based on view and share counts."""
        # Get news from the last 7 days
        last_week = timezone.now() - timezone.timedelta(days=7)
        trending_news = News.objects.filter(
            status='published',
            published_date__gte=last_week
        ).order_by('-view_count', '-share_count')[:10]
        
        serializer = NewsListSerializer(
            trending_news, 
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def fact_checked(self, request):
        """Endpoint to get fact-checked news articles."""
        fact_checked_news = News.objects.filter(
            status='published',
            is_fact_checked=True
        ).order_by('-published_date')
        
        page = self.paginate_queryset(fact_checked_news)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(fact_checked_news, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def local(self, request):
        """Endpoint to get local news based on user's preferences or query params."""
        county = request.query_params.get('county')
        town = request.query_params.get('town')
        
        # If no params provided and user is authenticated, use user preferences
        if not (county or town) and request.user.is_authenticated:
            user = request.user
            county = user.county
            town = user.town
        
        # Filter news by location
        filters = Q(status='published')
        if county:
            filters &= Q(county__iexact=county)
        if town:
            filters &= Q(town__iexact=town)
        
        local_news = News.objects.filter(filters).order_by('-published_date')
        
        page = self.paginate_queryset(local_news)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(local_news, many=True)
        return Response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet for comments on news articles."""
    
    queryset = Comment.objects.filter(is_approved=True, parent=None)
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = NewsPagination
    
    def get_queryset(self):
        """Return comments for a specific news article if specified."""
        queryset = super().get_queryset()
        news_slug = self.request.query_params.get('news')
        
        if news_slug:
            queryset = queryset.filter(news__slug=news_slug)
        
        return queryset.select_related('user', 'news').prefetch_related('replies')

    def get_serializer_class(self):
        """Return different serializer for detail actions."""
        if self.action in ['retrieve', 'list']:
            return CommentDetailSerializer
        return CommentSerializer

    def perform_create(self, serializer):
        """Set user when creating a comment."""
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """Set is_edited flag when updating a comment."""
        serializer.save(is_edited=True)