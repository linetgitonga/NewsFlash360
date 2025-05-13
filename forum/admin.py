from django.contrib import admin
from .models import Category, Post, Comment, Tag, Report


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')
    date_hierarchy = 'created_at'


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('author', 'content', 'created_at', 'active')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'status', 'published_at', 
                   'language', 'fact_checked', 'view_count', 'comment_count')
    list_filter = ('status', 'created_at', 'published_at', 'category', 'language', 'fact_checked')
    search_fields = ('title', 'content', 'summary', 'location')
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('author',)
    date_hierarchy = 'published_at'
    ordering = ('-published_at', '-created_at')
    readonly_fields = ('created_at', 'updated_at', 'published_at', 'views')
    filter_horizontal = ('upvotes',)
    inlines = [CommentInline]
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'author', 'category', 'content', 'summary',
                      'status', 'image')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'published_at', 'language',
                      'location', 'views')
        }),
        ('Fact-checking', {
            'fields': ('fact_checked', 'fact_check_notes')
        }),
        ('Community Engagement', {
            'fields': ('upvotes',)
        })
    )
    
    def view_count(self, obj):
        return obj.views
    view_count.short_description = 'Views'
    
    def comment_count(self, obj):
        return obj.comments.filter(active=True).count()
    comment_count.short_description = 'Comments'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'short_content', 'created_at', 'active', 'is_reply')
    list_filter = ('active', 'created_at', 'updated_at')
    search_fields = ('author__username', 'content', 'post__title')
    raw_id_fields = ('author', 'post', 'parent')
    actions = ['activate_comments', 'deactivate_comments']
    filter_horizontal = ('upvotes',)
    
    def short_content(self, obj):
        return obj.content[:75] + '...' if len(obj.content) > 75 else obj.content
    short_content.short_description = 'Content'
    
    def is_reply(self, obj):
        return obj.parent is not None
    is_reply.boolean = True
    is_reply.short_description = 'Reply'
    
    def activate_comments(self, request, queryset):
        updated = queryset.update(active=True)
        self.message_user(request, f'{updated} comments have been activated.')
    activate_comments.short_description = 'Activate selected comments'
    
    def deactivate_comments(self, request, queryset):
        updated = queryset.update(active=False)
        self.message_user(request, f'{updated} comments have been deactivated.')
    deactivate_comments.short_description = 'Deactivate selected comments'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'post_count')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    
    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = 'Number of posts'


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'reporter', 'report_target', 'reason', 'created_at', 'resolved')
    list_filter = ('reason', 'resolved', 'created_at')
    search_fields = ('reporter__username', 'details')
    readonly_fields = ('reporter', 'post', 'comment', 'created_at')
    date_hierarchy = 'created_at'
    actions = ['mark_resolved', 'mark_unresolved']
    
    def report_target(self, obj):
        if obj.post:
            return f"Post: {obj.post.title[:30]}..."
        elif obj.comment:
            return f"Comment: {obj.comment.content[:30]}..."
        return "Unknown"
    report_target.short_description = 'Reported Content'
    
    def mark_resolved(self, request, queryset):
        updated = queryset.update(resolved=True)
        self.message_user(request, f'{updated} reports have been marked as resolved.')
    mark_resolved.short_description = 'Mark selected reports as resolved'
    
    def mark_unresolved(self, request, queryset):
        updated = queryset.update(resolved=False)
        self.message_user(request, f'{updated} reports have been marked as unresolved.')
    mark_unresolved.short_description = 'Mark selected reports as unresolved'