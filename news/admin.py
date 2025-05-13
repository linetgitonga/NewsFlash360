from django.contrib import admin
from .models import Category, Source, News, Tag, FactCheck, SavedNews, NewsRating, Comment

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')

@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'source_type', 'is_verified', 'reliability_score', 'created_at')
    list_filter = ('source_type', 'is_verified')
    search_fields = ('name', 'description')

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'status', 'published_date', 'is_fact_checked', 'view_count')
    list_filter = ('status', 'is_fact_checked', 'categories', 'country', 'county')
    search_fields = ('title', 'content', 'author')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_date'
    filter_horizontal = ('categories',)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(FactCheck)
class FactCheckAdmin(admin.ModelAdmin):
    list_display = ('news', 'verdict', 'checker', 'checked_date')
    list_filter = ('verdict', 'checked_date')
    search_fields = ('claim', 'explanation')

@admin.register(SavedNews)
class SavedNewsAdmin(admin.ModelAdmin):
    list_display = ('user', 'news', 'saved_date')
    list_filter = ('saved_date',)
    search_fields = ('user__email', 'news__title')

@admin.register(NewsRating)
class NewsRatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'news', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__email', 'news__title')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'news', 'created_at', 'is_approved')
    list_filter = ('is_approved', 'created_at', 'is_edited')
    search_fields = ('user__email', 'content', 'news__title')