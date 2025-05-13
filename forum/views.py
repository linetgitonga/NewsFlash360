from rest_framework import viewsets, filters, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from .filters import PostFilter, CommentFilter

from .models import Category, Post, Comment, Tag, Report
from .serializers import (
    CategorySerializer, PostListSerializer, PostDetailSerializer, 
    PostCreateUpdateSerializer, CommentSerializer, TagSerializer, 
    ReportSerializer
)
from .permissions import IsAuthorOrReadOnly, IsNotFlagged


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for forum views"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for forum categories"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    permission_classes = [permissions.IsAdminUser]
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return super().get_permissions()


class PostViewSet(viewsets.ModelViewSet):
    """ViewSet for forum posts"""
    queryset = Post.objects.all()
    serializer_class = PostListSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly, IsNotFlagged]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PostFilter
    search_fields = ['title', 'content', 'summary', 'location', 'tags__name']
    ordering_fields = ['created_at', 'published_at', 'upvote_count', 'views']
    
    def get_queryset(self):
        queryset = Post.objects.annotate(upvote_count=Count('upvotes'))
        
        # Filter by tag if provided
        tag_slug = self.request.query_params.get('tag')
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)
        
        # Show all posts to admins, but limit regular users to published posts
        if not self.request.user.is_staff:
            if self.request.user.is_authenticated:
                # Authenticated users can see their own drafts and published posts
                queryset = queryset.filter(
                    status='published') | queryset.filter(
                    status='draft', author=self.request.user
                )
            else:
                # Anonymous users can only see published posts
                queryset = queryset.filter(status='published')
        
        return queryset
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PostCreateUpdateSerializer
        elif self.action == 'retrieve':
            return PostDetailSerializer
        return PostListSerializer
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment view count
        instance.views += 1
        instance.save(update_fields=['views'])
        return super().retrieve(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def upvote(self, request, pk=None):
        """Toggle upvote on a post"""
        post = self.get_object()
        user = request.user
        
        if user in post.upvotes.all():
            post.upvotes.remove(user)
            return Response({'status': 'upvote removed'})
        else:
            post.upvotes.add(user)
            return Response({'status': 'upvoted'})
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def publish(self, request, pk=None):
        """Publish a draft post"""
        post = self.get_object()
        
        # Check if user is author
        if post.author != request.user and not request.user.is_staff:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        if post.status != 'draft':
            return Response({'error': 'Only draft posts can be published'}, status=status.HTTP_400_BAD_REQUEST)
        
        post.status = 'published'
        post.published_at = timezone.now()
        post.save()
        
        serializer = self.get_serializer(post)
        return Response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet for post comments"""
    queryset = Comment.objects.filter(active=True)
    serializer_class = CommentSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = CommentFilter
    search_fields = ['content']
    
    def get_queryset(self):
        queryset = Comment.objects.filter(active=True).annotate(upvote_count=Count('upvotes'))
        
        # Filter by post if provided
        post_id = self.request.query_params.get('post')
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        
        # Filter by parent (for replies) if provided
        parent_id = self.request.query_params.get('parent')
        if parent_id:
            if parent_id == 'null':  # Get top-level comments
                queryset = queryset.filter(parent__isnull=True)
            else:
                queryset = queryset.filter(parent_id=parent_id)
        
        return queryset
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def upvote(self, request, pk=None):
        """Toggle upvote on a comment"""
        comment = self.get_object()
        user = request.user
        
        if user in comment.upvotes.all():
            comment.upvotes.remove(user)
            return Response({'status': 'upvote removed'})
        else:
            comment.upvotes.add(user)
            return Response({'status': 'upvoted'})


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for tags"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class ReportViewSet(viewsets.ModelViewSet):
    """ViewSet for content reports"""
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Report.objects.all()
        return Report.objects.filter(reporter=self.request.user)

    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)
        
        # Auto-flag content if it reaches threshold of reports (e.g., 3)
        report = serializer.instance
        if report.post:
            report_count = Report.objects.filter(post=report.post, resolved=False).count()
            if report_count >= 3 and report.post.status == 'published':
                report.post.status = 'flagged'
                report.post.save(update_fields=['status'])
        elif report.comment:
            report_count = Report.objects.filter(comment=report.comment, resolved=False).count()
            if report_count >= 3:
                report.comment.active = False
                report.comment.save(update_fields=['active'])