from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Category, Source, News, Tag, FactCheck, 
    SavedNews, NewsRating, Comment
)

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for news categories."""
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class SourceSerializer(serializers.ModelSerializer):
    """Serializer for news sources."""
    
    class Meta:
        model = Source
        fields = [
            'id', 'name', 'url', 'logo', 'description', 
            'is_verified', 'reliability_score', 'source_type', 
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'is_verified', 'reliability_score']


class TagSerializer(serializers.ModelSerializer):
    """Serializer for news tags."""
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']
        read_only_fields = ['id']


class FactCheckSerializer(serializers.ModelSerializer):
    """Serializer for fact checks."""
    
    checker_name = serializers.SerializerMethodField()
    
    class Meta:
        model = FactCheck
        fields = [
            'id', 'claim', 'verdict', 'explanation', 
            'sources', 'checker', 'checker_name', 'checked_date'
        ]
        read_only_fields = ['id', 'checker', 'checked_date']
    
    def get_checker_name(self, obj):
        if obj.checker:
            return f"{obj.checker.first_name} {obj.checker.last_name}".strip() or obj.checker.email
        return "Automated System"


class CommentUserSerializer(serializers.ModelSerializer):
    """Minimalist serializer for user in comments."""
    
    name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'name', 'profile_picture']
    
    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.email.split('@')[0]


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for comments."""
    
    user = CommentUserSerializer(read_only=True)
    replies_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'user', 'news', 'parent', 'content', 
            'created_at', 'updated_at', 'is_edited', 
            'is_approved', 'replies_count'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'is_edited']
    
    def get_replies_count(self, obj):
        return obj.replies.count()


class CommentDetailSerializer(CommentSerializer):
    """Detailed serializer for comments with replies."""
    
    replies = serializers.SerializerMethodField()
    
    class Meta(CommentSerializer.Meta):
        fields = CommentSerializer.Meta.fields + ['replies']
    
    def get_replies(self, obj):
        replies = obj.replies.filter(is_approved=True).order_by('created_at')
        return CommentSerializer(replies, many=True).data


class NewsListSerializer(serializers.ModelSerializer):
    """Serializer for listing news articles."""
    
    source_name = serializers.CharField(source='source.name', read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comments_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    
    class Meta:
        model = News
        fields = [
            'id', 'title', 'slug', 'summary', 'summary_swahili', 'summary_sheng',
            'source', 'source_name', 'featured_image', 'image_caption',
            'author', 'published_date', 'categories', 'tags',
            'is_fact_checked', 'view_count', 'share_count',
            'country', 'county', 'town', 'comments_count',
            'average_rating', 'is_saved'
        ]
        read_only_fields = ['id', 'comments_count', 'average_rating', 'is_saved']
    
    def get_comments_count(self, obj):
        return obj.comments.filter(parent=None, is_approved=True).count()
    
    def get_average_rating(self, obj):
        ratings = obj.ratings.all()
        if not ratings:
            return 0
        return sum(r.rating for r in ratings) / len(ratings)
    
    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return SavedNews.objects.filter(user=request.user, news=obj).exists()
        return False


class NewsDetailSerializer(NewsListSerializer):
    """Detailed serializer for news articles."""
    
    content = serializers.SerializerMethodField()
    fact_checks = FactCheckSerializer(many=True, read_only=True)
    
    class Meta(NewsListSerializer.Meta):
        fields = NewsListSerializer.Meta.fields + [
            'content', 'content_swahili', 'content_sheng',
            'original_url', 'fact_checks', 'status'
        ]
    
    def get_content(self, obj):
        # Logic to return content based on user's language preference
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            lang = request.user.preferred_language
            if lang == 'sw' and obj.content_swahili:
                return obj.content_swahili
            elif lang == 'sheng' and obj.content_sheng:
                return obj.content_sheng
        return obj.content


class NewsRatingSerializer(serializers.ModelSerializer):
    """Serializer for news ratings."""
    
    class Meta:
        model = NewsRating
        fields = ['id', 'news', 'rating', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value
    
    def create(self, validated_data):
        user = self.context['request'].user
        news = validated_data['news']
        
        # Update existing rating if it exists
        try:
            rating = NewsRating.objects.get(user=user, news=news)
            rating.rating = validated_data['rating']
            rating.save()
            return rating
        except NewsRating.DoesNotExist:
            return super().create(validated_data)


class SavedNewsSerializer(serializers.ModelSerializer):
    """Serializer for saved news."""
    
    news = NewsListSerializer(read_only=True)
    
    class Meta:
        model = SavedNews
        fields = ['id', 'news', 'saved_date']
        read_only_fields = ['id', 'saved_date']