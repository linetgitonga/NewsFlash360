from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.urls import reverse

User = get_user_model()

class Category(models.Model):
    """Category model for forum posts"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('forum:category_detail', kwargs={'slug': self.slug})


class Post(models.Model):
    """Post model for user-generated news content"""
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('flagged', 'Flagged'),
        ('verified', 'Verified'),
    )
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique_for_date='created_at')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_posts')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField()
    summary = models.TextField(blank=True, help_text="Auto-generated summary of the post")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    location = models.CharField(max_length=100, blank=True, help_text="Location related to the news")
    fact_checked = models.BooleanField(default=False)
    fact_check_notes = models.TextField(blank=True)
    
    # Fields for multilingual support
    language = models.CharField(max_length=10, choices=[
        ('en', 'English'), 
        ('sw', 'Swahili'), 
        ('sh', 'Sheng')
    ], default='en')
    
    # Fields for community engagement
    upvotes = models.ManyToManyField(User, related_name='upvoted_posts', blank=True)
    views = models.PositiveIntegerField(default=0)
    
    # For media attachments
    image = models.ImageField(upload_to='forum/posts/%Y/%m/%d/', blank=True, null=True)
    
    class Meta:
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['-published_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
            
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('forum:post_detail', kwargs={
            'year': self.created_at.year,
            'month': self.created_at.month,
            'day': self.created_at.day,
            'slug': self.slug
        })
    
    @property
    def upvote_count(self):
        return self.upvotes.count()


class Comment(models.Model):
    """Comment model for discussions on posts"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)
    
    # For community engagement
    upvotes = models.ManyToManyField(User, related_name='upvoted_comments', blank=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f'Comment by {self.author.username} on {self.post}'
    
    @property
    def upvote_count(self):
        return self.upvotes.count()


class Tag(models.Model):
    """Tags for categorizing posts"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)
    posts = models.ManyToManyField(Post, related_name='tags', blank=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Report(models.Model):
    """Model for reporting inappropriate content"""
    REASON_CHOICES = (
        ('misinformation', 'Misinformation'),
        ('inappropriate', 'Inappropriate Content'),
        ('spam', 'Spam'),
        ('hate_speech', 'Hate Speech'),
        ('other', 'Other'),
    )
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True)
    
    def __str__(self):
        if self.post:
            return f'Report on post: {self.post.title}'
        return f'Report on comment by {self.comment.author.username}'