from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'forum'

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'posts', views.PostViewSet)
router.register(r'comments', views.CommentViewSet)
router.register(r'tags', views.TagViewSet)
router.register(r'reports', views.ReportViewSet)

urlpatterns = [
    path('', include(router.urls)),
]