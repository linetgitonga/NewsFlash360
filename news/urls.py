from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'news'

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'sources', views.SourceViewSet)
router.register(r'tags', views.TagViewSet)
router.register(r'news', views.NewsViewSet)
router.register(r'comments', views.CommentViewSet)

# The API URLs are now determined automatically by the router
urlpatterns = [
    # Include the router URLs
    path('', include(router.urls)),
]