from django.db import models
from django.conf import settings


class Category(models.Model):
    """Model for news categories."""
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "categories"


class Source(models.Model):
    """Model for news sources."""
    
    name = models.CharField(max_length=100)
    url = models.URLField()
    logo = models.ImageField(upload_to='source_logos/', blank=True, null=True)
    description = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    reliability_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)  # 0-1 score
    created_at = models.DateTimeField(auto_now_add=True)
    
    SOURCE_TYPES = [
        ('blog', 'Blog'),
        ('newspaper', 'Newspaper'),
        ('tv', 'TV Station'),
        ('radio', 'Radio Station'),
        ('social_media', 'Social Media'),
        ('agency', 'News Agency'),
        ('other', 'Other'),
    ]
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    
    scraping_config = models.JSONField(
        default=dict,
        help_text="Configuration for scraping (CSS selectors, API keys, etc.)"
    )
    last_scraped = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.source_type})"

class News(models.Model):
    """Model for news articles."""
    
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    
    # Content in different languages
    content_swahili = models.TextField(blank=True, null=True)
    content_sheng = models.TextField(blank=True, null=True)
    
    summary = models.TextField(blank=True)
    
    # Summaries in different languages
    summary_swahili = models.TextField(blank=True, null=True)
    summary_sheng = models.TextField(blank=True, null=True)
    
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name="news")
    original_url = models.URLField(blank=True)
    
    categories = models.ManyToManyField(Category, related_name="news")
    
    # Featured image
    featured_image = models.ImageField(upload_to='news_images/', blank=True, null=True)
    image_caption = models.CharField(max_length=255, blank=True)
    
    # Metadata
    author = models.CharField(max_length=100, blank=True)
    published_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Status and verification
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    is_fact_checked = models.BooleanField(default=False)
    
    # Analytics and engagement
    view_count = models.PositiveIntegerField(default=0)
    share_count = models.PositiveIntegerField(default=0)
    
    # Geographical tagging
    country = models.CharField(max_length=100, default='Kenya')
    county = models.CharField(max_length=100, blank=True)
    town = models.CharField(max_length=100, blank=True)
    
    # For AI processing
    is_ai_processed = models.BooleanField(default=False)
    ai_processing_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "news"
        ordering = ['-published_date']
    
    def __str__(self):
        return self.title


class Tag(models.Model):
    """Model for news tags."""
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    news = models.ManyToManyField(News, related_name="tags")
    
    def __str__(self):
        return self.name


class FactCheck(models.Model):
    """Model for fact-checking results."""
    
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name="fact_checks")
    claim = models.TextField()
    
    VERDICT_CHOICES = [
        ('true', 'True'),
        ('mostly_true', 'Mostly True'),
        ('half_true', 'Half True'),
        ('mostly_false', 'Mostly False'),
        ('false', 'False'),
        ('unverifiable', 'Unverifiable'),
    ]
    verdict = models.CharField(max_length=20, choices=VERDICT_CHOICES)
    
    explanation = models.TextField()
    sources = models.TextField(blank=True)  # References for fact-checking
    checker = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="fact_checks"
    )
    checked_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.news.title} - {self.verdict}"


class SavedNews(models.Model):
    """Model for user's saved news articles."""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_news")
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name="saved_by")
    saved_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'news')
        verbose_name_plural = "saved news"
    
    def __str__(self):
        return f"{self.user.email} - {self.news.title}"


class NewsRating(models.Model):
    """Model for user ratings on news articles."""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name="ratings")
    rating = models.PositiveSmallIntegerField()  # 1-5 rating
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'news')
    
    def __str__(self):
        return f"{self.user.email} - {self.news.title} - {self.rating}"


class Comment(models.Model):
    """Model for comments on news articles."""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name="replies")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.news.title[:30]}"