from rest_framework import serializers
from .models import Category, Post, Comment, Tag, Report
from django.contrib.auth import get_user_model

User = get_user_model()


class UserBriefSerializer(serializers.ModelSerializer):
    """Brief user information for nested serialization"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class TagSerializer(serializers.ModelSerializer):
    """Serializer for post tags"""
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']
        read_only_fields = ['slug']


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for post categories"""
    post_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'created_at', 'post_count']
        read_only_fields = ['slug', 'created_at', 'post_count']
    
    def get_post_count(self, obj):
        return obj.posts.filter(status='published').count()


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for post comments"""
    author = UserBriefSerializer(read_only=True)
    upvote_count = serializers.IntegerField(read_only=True)
    is_upvoted = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'post', 'author', 'parent', 'content', 
            'created_at', 'updated_at', 'active', 
            'upvote_count', 'is_upvoted', 'replies'
        ]
        read_only_fields = ['created_at', 'updated_at', 'active', 'upvote_count']
    
    def get_is_upvoted(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return user in obj.upvotes.all()
        return False
    
    def get_replies(self, obj):
        if obj.replies.exists():
            return CommentBriefSerializer(obj.replies.filter(active=True), many=True).data
        return []
    
    def create(self, validated_data):
        user = self.context.get('request').user
        comment = Comment.objects.create(
            author=user,
            **validated_data
        )
        return comment


class CommentBriefSerializer(serializers.ModelSerializer):
    """Brief comment serializer for nested replies"""
    author = UserBriefSerializer(read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'author', 'content', 'created_at', 'upvote_count']


class PostListSerializer(serializers.ModelSerializer):
    """Serializer for listing posts"""
    author = UserBriefSerializer(read_only=True)
    category_name = serializers.ReadOnlyField(source='category.name')
    comment_count = serializers.SerializerMethodField()
    upvote_count = serializers.IntegerField(read_only=True)
    is_upvoted = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'author', 'category', 'category_name',
            'summary', 'created_at', 'published_at', 'status',
            'location', 'fact_checked', 'language',
            'upvote_count', 'views', 'image', 'comment_count',
            'is_upvoted', 'tags'
        ]
        read_only_fields = [
            'slug', 'created_at', 'published_at', 'views', 
            'upvote_count', 'comment_count', 'fact_checked'
        ]
    
    def get_comment_count(self, obj):
        return obj.comments.filter(active=True).count()
    
    def get_is_upvoted(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return user in obj.upvotes.all()
        return False


class PostDetailSerializer(PostListSerializer):
    """Detailed serializer for single post view"""
    comments = serializers.SerializerMethodField()
    
    class Meta(PostListSerializer.Meta):
        fields = PostListSerializer.Meta.fields + ['content', 'fact_check_notes', 'comments']
    
    def get_comments(self, obj):
        # Only get top-level comments (no parent)
        comments = obj.comments.filter(active=True, parent=None)
        return CommentSerializer(comments, many=True, context=self.context).data


class PostCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating posts"""
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False, 
        write_only=True
    )
    
    class Meta:
        model = Post
        fields = [
            'title', 'category', 'content', 'location', 
            'language', 'image', 'tags', 'status'
        ]
    
    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
        user = self.context.get('request').user
        
        post = Post.objects.create(
            author=user,
            **validated_data
        )
        
        # Handle tags
        self._process_tags(post, tags_data)
        
        return post
    
    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Only update published_at if status changes to published
        if instance.status == 'published' and not instance.published_at:
            instance.published_at = timezone.now()
            
        instance.save()
        
        # Handle tags if provided
        if tags_data is not None:
            # Remove existing tags
            instance.tags.clear()
            self._process_tags(instance, tags_data)
        
        return instance
    
    def _process_tags(self, post, tags_data):
        for tag_name in tags_data:
            tag_name = tag_name.strip()
            if tag_name:
                tag, _ = Tag.objects.get_or_create(
                    name=tag_name,
                    defaults={'slug': slugify(tag_name)}
                )
                post.tags.add(tag)


class ReportSerializer(serializers.ModelSerializer):
    """Serializer for content reports"""
    reporter = UserBriefSerializer(read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id', 'post', 'comment', 'reporter', 'reason', 
            'details', 'created_at', 'resolved'
        ]
        read_only_fields = ['reporter', 'created_at', 'resolved']
    
    def validate(self, data):
        # Ensure either post or comment is provided, but not both
        if not data.get('post') and not data.get('comment'):
            raise serializers.ValidationError("Either post or comment must be provided")
        if data.get('post') and data.get('comment'):
            raise serializers.ValidationError("Only one of post or comment should be provided")
        return data
    
    def create(self, validated_data):
        user = self.context.get('request').user
        report = Report.objects.create(
            reporter=user,
            **validated_data
        )
        return report